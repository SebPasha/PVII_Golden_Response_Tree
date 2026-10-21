"""The model client: disk cache, spend and call caps, bounded fan-out, retries, a breaker.

Cache key = (model, prompt bytes, expected shape, temperature). A change to any of them is a
miss, which is why prompt edits are the only thing in this package that costs money.
"""
import hashlib
import json
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from pvii import config


class BudgetExceeded(RuntimeError):
    """A cost or call cap would be breached; the run aborts."""


class StageAborted(RuntimeError):
    """The failure rate of a stage says its prompt is broken."""


class TruncatedResponse(RuntimeError):
    """The model hit the output cap, so the JSON is cut off."""


class CacheMiss(RuntimeError):
    """PVII_OFFLINE is set and the response is not in the cache."""


_FENCE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$", re.IGNORECASE)


def extract_json(text):
    """Parse a response as JSON, tolerating fences and stray prose around one value."""
    if text is None:
        raise ValueError("empty response")
    s = text.strip()
    for candidate in (s, _FENCE.sub("", s).strip()):
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass
    stripped = _FENCE.sub("", s).strip()
    for opener, closer in (("[", "]"), ("{", "}")):
        start = stripped.find(opener)
        if start == -1:
            continue
        depth, in_str, esc = 0, False, False
        for i in range(start, len(stripped)):
            ch = stripped[i]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch == opener:
                depth += 1
            elif ch == closer:
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(stripped[start:i + 1])
                    except json.JSONDecodeError:
                        break
    raise ValueError(f"could not parse JSON from response: {s[:300]}")


def retry_after(exc):
    """Seconds the service asked us to wait, from the header or the error body, or None."""
    resp = getattr(exc, "response", None)
    headers = getattr(resp, "headers", None) or {}
    for key in ("retry-after", "Retry-After", "retry-after-ms"):
        v = headers.get(key)
        if v:
            try:
                return float(v) / (1000.0 if key.endswith("ms") else 1.0)
            except (TypeError, ValueError):
                pass
    m = re.search(r"retry after (\d+) second", str(exc), re.I)
    return float(m.group(1)) if m else None


def record(path):
    """Copy a cache entry into PVII_RECORD_DIR, when set, to build a replay corpus."""
    if config.RECORD_DIR:
        import shutil
        os.makedirs(config.RECORD_DIR, exist_ok=True)
        shutil.copy2(path, os.path.join(config.RECORD_DIR, os.path.basename(path)))


_ENCODER = None


def count_tokens(text):
    """Approximate token count for estimates and batch sizing."""
    global _ENCODER
    if _ENCODER is None:
        try:
            import tiktoken
            _ENCODER = tiktoken.get_encoding("o200k_base")
        except Exception:                       # no tiktoken: characters / 4
            _ENCODER = False
    return len(_ENCODER.encode(text)) if _ENCODER else max(1, len(text) // 4)


class Ledger:
    """Thread-safe record of what a run has spent, and the caps it must respect."""

    def __init__(self, max_cost_usd, max_calls, dry_run=False):
        self.max_cost, self.max_calls, self.dry_run = max_cost_usd, max_calls, dry_run
        self._lock = threading.Lock()
        self.stages, self.calls, self.cost, self.cache_hits = {}, 0, 0.0, 0
        self.reserved = 0.0        # projections held by calls in flight, so 16 workers
        self.inflight = 0          # cannot each pass the same check against one balance

    def _stage(self, stage):
        return self.stages.setdefault(stage, {"calls": 0, "cache_hits": 0, "in": 0, "out": 0,
                                              "cost": 0.0, "errors": 0, "est_in": 0,
                                              "est_out": 0, "est_cost": 0.0})

    def reserve(self, stage, est_in_tokens, model):
        """Hold this call's projection until it settles; raises before the cap, not after."""
        p_in, p_out = config.price_for(model)
        projection = (est_in_tokens / 1e6) * (p_in + p_out)
        with self._lock:
            if self.calls + self.inflight + 1 > self.max_calls:
                raise BudgetExceeded(f"call cap reached ({self.max_calls}). Raise --max-calls.")
            if self.cost + self.reserved + projection > self.max_cost:
                raise BudgetExceeded(f"spend cap reached: ${self.cost:.4f} spent and "
                                     f"${self.reserved:.4f} in flight; the next call is "
                                     f"projected past ${self.max_cost:.2f}. Raise --max-cost.")
            self.reserved += projection
            self.inflight += 1
        return projection

    def release(self, projection):
        with self._lock:
            self.reserved = max(0.0, self.reserved - projection)
            self.inflight = max(0, self.inflight - 1)

    def record_time(self, stage, seconds, latencies):
        with self._lock:
            st = self._stage(stage)
            st["seconds"] = round(st.get("seconds", 0.0) + seconds, 1)
            lat = sorted(latencies)
            if lat:
                st["p95_seconds"] = round(lat[max(0, int(len(lat) * 0.95) - 1)], 1)

    def record(self, stage, model, in_tok, out_tok):
        p_in, p_out = config.price_for(model)
        cost = (in_tok / 1e6) * p_in + (out_tok / 1e6) * p_out
        with self._lock:
            st = self._stage(stage)
            st["calls"] += 1
            st["in"] += in_tok
            st["out"] += out_tok
            st["cost"] += cost
            self.calls += 1
            self.cost += cost
        return cost

    def record_estimate(self, stage, model, in_tok, out_tok):
        p_in, p_out = config.price_for(model)
        with self._lock:
            st = self._stage(stage)
            st["est_in"] += in_tok
            st["est_out"] += out_tok
            st["est_cost"] += (in_tok / 1e6) * p_in + (out_tok / 1e6) * p_out
            st["calls"] += 1
            self.calls += 1

    def record_cache_hit(self, stage):
        with self._lock:
            self._stage(stage)["cache_hits"] += 1
            self.cache_hits += 1

    def record_error(self, stage):
        with self._lock:
            self._stage(stage)["errors"] += 1

    def as_dict(self):
        with self._lock:
            return {"stages": {k: dict(v) for k, v in self.stages.items()},
                    "calls": self.calls, "cost": round(self.cost, 6),
                    "cache_hits": self.cache_hits, "dry_run": self.dry_run}

    def report(self):
        """Markdown summary; never contains a credential."""
        dry = self.dry_run
        lines = ["# Cost report", "",
                 "Temperature: extraction (C, E) at **%s**, judgement (F, M) at **%s**."
                 % (config.STAGE_TEMPERATURES["E"], config.STAGE_TEMPERATURES["M"]), "",
                 "**Dry run, no API calls were made.**" if dry else
                 f"**Total: ${self.cost:.4f} across {self.calls} calls "
                 f"({self.cache_hits} served from cache)**", "",
                 "| Stage | Calls | Cache hits | Tokens in | Tokens out | Cost (USD) | Errors |",
                 "|---|---|---|---|---|---|---|"]
        for stage in sorted(self.stages):
            s = self.stages[stage]
            lines.append(f"| {stage} | {s['calls']} | - | {s['est_in']:,} | ~{s['est_out']:,} | "
                         f"~{s['est_cost']:.4f} | - |" if dry else
                         f"| {stage} | {s['calls']} | {s['cache_hits']} | {s['in']:,} | "
                         f"{s['out']:,} | {s['cost']:.4f} | {s['errors']} |")
        total = sum(s["est_cost"] if dry else s["cost"] for s in self.stages.values())
        lines += ["", f"**{'Estimated total' if dry else 'Total'}: ${total:.4f}**", ""]
        return "\n".join(lines)


class LLMClient:
    def __init__(self, ledger, cache_dir=None, dry_run=False, verbose=True,
                 use_cache=True, temperature=None):
        self.ledger = ledger
        self.temperature = config.TEMPERATURE if temperature is None else float(temperature)
        self.dry_run, self.verbose, self.use_cache = dry_run, verbose, use_cache
        self.cache_dir = cache_dir or config.CACHE_DIR
        os.makedirs(self.cache_dir, exist_ok=True)
        self._client, self._lock, self._unsupported = None, threading.Lock(), set()

    def _get_client(self):
        with self._lock:
            if self._client is None:
                try:
                    from openai import OpenAI
                except ImportError:
                    sys.exit("ERROR: pip install openai")
                cfg = config.openai_config()
                self._client = OpenAI(base_url=cfg["base_url"], api_key=cfg["api_key"],
                                      timeout=300.0, max_retries=2)
            return self._client

    def _cache_path(self, model, prompt, expect, temperature=None):
        h = hashlib.sha256()
        h.update(model.encode())
        h.update(b"\x00")
        h.update(prompt.encode())
        h.update(b"\x00" + str(expect).encode())
        h.update(b"\x00" + ("t=%.3f" % (self.temperature if temperature is None
                                          else temperature)).encode())
        return os.path.join(self.cache_dir, f"{h.hexdigest()}.json")

    def _request(self, model, prompt, use_json_object, max_tokens, temperature=None):
        """One HTTP request, dropping parameters the deployment rejects and remembering them."""
        client = self._get_client()
        messages = [{"role": "user", "content": prompt}]
        while True:
            kwargs = {"model": model, "messages": messages}
            if use_json_object and "response_format" not in self._unsupported:
                kwargs["response_format"] = {"type": "json_object"}
            if "temperature" not in self._unsupported:
                kwargs["temperature"] = self.temperature if temperature is None else temperature
            if max_tokens:
                key = ("max_tokens" if "max_completion_tokens" in self._unsupported
                       else "max_completion_tokens")
                if key not in self._unsupported:
                    kwargs[key] = max_tokens
            try:
                return client.chat.completions.create(**kwargs)
            except Exception as e:
                dropped = self._drop_unsupported(e, kwargs)
                if not dropped:
                    raise
                if self.verbose:
                    print(f"    note: endpoint rejected '{dropped}', retrying without it")

    def _drop_unsupported(self, exc, kwargs):
        msg = str(exc)
        if "400" not in msg and "unsupported" not in msg.lower() and "invalid" not in msg.lower():
            return None
        for param in ("response_format", "temperature", "max_completion_tokens", "max_tokens"):
            if param in kwargs and param in msg:
                with self._lock:
                    self._unsupported.add(param)
                return param
        return None

    def call(self, stage, prompt, model=None, json_mode=True, max_tokens=None, expect="object"):
        """One prompt in, parsed JSON out. Cached, capped, retried.

        json_object mode forces a top-level object, so it is used only where an object is
        expected; array stages are parsed leniently instead.
        """
        model = model or config.STAGE_MODELS.get(stage, config.MODEL_SMALL)
        use_json_object = json_mode and expect == "object"
        budget = max_tokens or config.STAGE_MAX_TOKENS.get(stage, 8000)
        temp = config.temperature_for(stage)
        path = self._cache_path(model, prompt, expect if json_mode else "text", temperature=temp)

        if self.use_cache and os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                cached = json.load(f)
            self.ledger.record_cache_hit(stage)
            record(path)
            return extract_json(cached["content"]) if json_mode else cached["content"]
        if config.OFFLINE:
            raise CacheMiss(f"stage {stage}: not in cache and PVII_OFFLINE is set")

        in_tok = count_tokens(prompt)
        if self.dry_run:
            self.ledger.record_estimate(stage, model, in_tok, max(200, in_tok // 4))
            return None
        held = self.ledger.reserve(stage, in_tok, model)

        last_err, attempt, escalations = None, -1, 0
        # Growing the budget after truncation has its own allowance, apart from error retries.
        while attempt < config.MAX_RETRIES - 1 + escalations:
            attempt += 1
            try:
                resp = self._request(model, prompt, use_json_object, budget, temperature=temp)
                choice = resp.choices[0]
                content = choice.message.content
                usage = getattr(resp, "usage", None)
                self.ledger.record(stage, model, getattr(usage, "prompt_tokens", in_tok) or in_tok,
                                   getattr(usage, "completion_tokens", 0) or 0)
                if getattr(choice, "finish_reason", None) == "length":
                    if budget < config.MAX_OUTPUT_CEILING:
                        budget = min(budget * 2, config.MAX_OUTPUT_CEILING)
                        escalations += 1
                        if self.verbose:
                            print(f"    note: stage {stage} hit the token cap, retrying with "
                                  f"max_tokens={budget}")
                        continue
                    raise TruncatedResponse(f"stage {stage}: truncated even at "
                                            f"max_tokens={config.MAX_OUTPUT_CEILING}; split the input")
                parsed = extract_json(content) if json_mode else content
                with open(path, "w", encoding="utf-8") as f:     # only what parsed is cached
                    json.dump({"model": model, "content": content}, f)
                record(path)
                self.ledger.release(held)
                return parsed
            except BudgetExceeded:
                self.ledger.release(held)
                raise
            except TruncatedResponse as e:
                last_err = e
                break
            except Exception as e:
                last_err = e
                if attempt < config.MAX_RETRIES - 1:
                    # The service says how long to wait when it is rate limiting; a blind
                    # backoff either hammers it or sits idle.
                    wait = retry_after(e)
                    if wait is None:
                        transient = not isinstance(e, ValueError)
                        wait = (4 ** attempt if transient else 2 ** attempt) + 0.5
                    time.sleep(min(wait, 120.0))
        self.ledger.release(held)
        self.ledger.record_error(stage)
        raise RuntimeError(f"stage {stage}: {last_err}")

    def map(self, stage, items, build_prompt, model=None, json_mode=True, max_tokens=None,
            concurrency=None, label="item", expect="object"):
        """One call per item, bounded concurrency. Returns (results aligned to items, errors)."""
        n = len(items)
        if n == 0:
            return [], []
        workers = concurrency or config.concurrency_for(stage)
        results, errors, done, aborted = [None] * n, [], [0], []
        latencies, started = [], time.monotonic()
        lock = threading.Lock()

        def work(i):
            if aborted:
                return
            t0 = time.monotonic()
            try:
                results[i] = self.call(stage, build_prompt(items[i]), model=model,
                                       json_mode=json_mode, max_tokens=max_tokens, expect=expect)
                with lock:
                    latencies.append(time.monotonic() - t0)
            except (BudgetExceeded, CacheMiss) as e:
                with lock:
                    aborted.append(str(e))
            except Exception as e:                  # one item's failure is counted, not fatal
                with lock:
                    errors.append((i, str(e)))
            finally:
                with lock:
                    done[0] += 1
                    if self.verbose and (done[0] % 10 == 0 or done[0] == n):
                        print(f"    stage {stage}: {done[0]}/{n} {label}s "
                              f"(${self.ledger.cost:.4f})", flush=True)

        with ThreadPoolExecutor(max_workers=workers) as ex:
            list(ex.map(work, range(n)))
        elapsed = time.monotonic() - started
        self.ledger.record_time(stage, elapsed, latencies)
        # The budget config.STAGE_TIME_BUDGET_S has promised since it was written. Nothing read
        # it, so it took a value from the environment and changed nothing. A stage running long
        # on genuine 64,000-token generations therefore said nothing at all, a healthy stage
        # read as a stuck one, and Nigeria's stage 5 was stopped by hand for no reason (W129).
        # The client's read timeout cannot help there: a generation that keeps sending bytes is
        # not a silent socket. This does not stop a slow stage and should not, since the slow
        # stage was doing correct work. It puts the elapsed time in front of whoever is
        # watching, which is the judgement that was made wrongly without it.
        if elapsed > config.STAGE_TIME_BUDGET_S:
            slowest = ("slowest call %.0fs" % max(latencies)) if latencies else "none completed"
            print("    note: stage %s took %.0fs, over the %ds budget: %d %ss, %s"
                  % (stage, elapsed, config.STAGE_TIME_BUDGET_S, n, label, slowest), flush=True)
        if aborted:
            raise BudgetExceeded(aborted[0])
        # The n >= 5 floor exists so a one-call stage that fails once is not read as a 100%
        # failure rate. A stage whose threshold is zero has no floor: one lost call is the
        # defect, whatever the denominator.
        limit = config.failure_rate_abort_for(stage)
        if errors and (limit == 0 or (n >= 5 and len(errors) / n > limit)):
            raise StageAborted(f"stage {stage}: {len(errors)}/{n} calls failed "
                               f"(>{limit:.0%}). First error: {errors[0][1]}")
        return results, errors
