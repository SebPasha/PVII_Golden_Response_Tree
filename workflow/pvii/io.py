"""CSV and JSON in and out. Lists are stored in a cell as JSON so they read back as lists."""
import csv
import json
import os


def _cell(v):
    if isinstance(v, (list, dict)):
        return json.dumps(v, ensure_ascii=False)
    return "" if v is None else v


def write_csv(path, rows, columns):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({c: _cell(r.get(c)) for c in columns})
    os.replace(tmp, path)


def read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def as_list(v):
    """A cell back to a list: JSON where it is JSON, else a single value, else []."""
    if isinstance(v, list):
        return v
    s = str(v or "").strip()
    if not s:
        return []
    if s.startswith("["):
        try:
            out = json.loads(s)
            return out if isinstance(out, list) else [out]
        except json.JSONDecodeError:
            pass
    return [s]


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def read_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)
