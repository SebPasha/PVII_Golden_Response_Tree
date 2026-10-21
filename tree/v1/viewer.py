"""Write mother_tree.html: the six-level viewer for mother tree v1 (tree, compare-at, mechanisms, objectives, validation)."""
import csv, json, os, re, html
HERE = os.path.dirname(os.path.abspath(__file__))

def rd(n):
    return list(csv.DictReader(open(os.path.join(HERE, n))))

fam = rd("families.csv"); mech = rd("mechanisms.csv"); obj = rd("objectives_v1.csv"); st = rd("strategy_nodes.csv")
SUBS = [("TSE","People-first Approach","Tackling Structural Exclusion",0),("CAP","People-first Approach","Enhancing Capabilities",0),
        ("FUT","People-first Approach","Future Generations",0),("SPE","People-first Approach","Standard People",1),
        ("EXP","Smarter Growth","Export-led",0),("DOM","Smarter Growth","Domestic Integration",0),("GTI","Smarter Growth","Growth through Inclusion",0),
        ("SEC","Smarter Growth","Standard Economy",1),("ANT","Making Change Happen","Anticipation and Strategic Foresight",0),
        ("ADA","Making Change Happen","Adaptability and Course Correction",0),("AGI","Making Change Happen","Agility and Delivery Capability",0),
        ("REF","Making Change Happen","Reform Leadership, Coalitions and Civic Engagement",0),("SGO","Making Change Happen","Standard Governance",1)]
subname = {s[2]: s[0] for s in SUBS}
HOLD = {"Standard People holding branch": "SPE", "Standard Economy holding branch": "SEC", "Standard Governance holding branch": "SGO",
        "Goals held outside the tree": "GOAL"}
HOLDKEY = {"H-SPE": "SPE", "H-SEC": "SEC", "H-SGO": "SGO", "H-GOAL": "GOAL"}

F = [dict(id=f["family_id"], n=f["family"], s=subname[f["subpillar"]], d=f["definition"], cv=f["core_variables"],
          inc=f["inclusion_rule"], exc=f["exclusion_rule"], lit=f["literature"], why=f["primary_reason"],
          sec=f["secondary_rhdr"], rk=f["risks"]) for f in fam]
fi = {f["id"]: i for i, f in enumerate(F)}
M = [dict(id=m["mechanism_id"], n=m["mechanism"], f=fi[m["family_id"]], i=m["causal_input"], t=m["transmission"], o=m["outcome"],
          c=m["conditions"], ds=m["distinction"], e=m["evidence"], rk=m["risks"], rj=m["risk_justification"],
          su=m["classification_suitability"], ev=m["evidence_status"], rs=m["risk_status"], cr=m["conditional_risks"],
          rr=m["rejected_risks"]) for m in mech]
mi = {m["id"]: i for i, m in enumerate(M)}
O = []
for o in obj:
    lv = {"L3 mechanism": 3, "L2 family": 2, "Standard holding": 0, "Goal held outside": -1}[o["level"]]
    h = HOLD.get(o["holding"], "")
    O.append(dict(id=o["objective_id"], n=o["objective"], d=o["definition"], lv=lv, f=fi.get(o["family_id"], -1),
                  m=mi.get(o["mechanism_id"], -1), h=h, r=o["depth_reason"], c=o["candidate_mechanisms"],
                  b=o["classification_basis"], cf=o["confidence"], sr=o["secondary_rhdr"], src=o["source_objective_ids"],
                  mh=o["merge_history"], bau=o["bau_flag"]))
oi = {o["id"]: i for i, o in enumerate(O)}
countries = sorted({s["country"] for s in st})
ci = {c: i for i, c in enumerate(countries)}
S = []
for s in st:
    lv = {"L3": 3, "L2": 2, "STD": 0, "GOAL": -1}[s["level"]]
    S.append([ci[s["country"]], oi[s["l4_id"]], lv, mi.get(s["mechanism_id"], -1), fi.get(s["family_id"], -1),
              HOLDKEY.get(s["holding"], ""), s["strategy"], s["depth_basis"], s["evidence"], 1 if s["bau"] == "yes" else 0])
validation = open(os.path.join(HERE, "VALIDATION.md")).read()
DATA = dict(subs=[dict(c=a, p=b, n=c, std=d) for a, b, c, d in SUBS], F=F, M=M, O=O, S=S, C=countries,
            risks=["Climate Change","Pandemics","Biodiversity Loss","Environmental Degradation and Pollution","Resource and Energy Pressures",
                   "Shifts in Globalisation","Technological Change","Demographic Shifts","Democratic Backsliding","Growing Populism","Increased Polarisation"],
            validation=validation)

PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PV II Mother Tree</title>
<style>
:root { --bg:#06180F; --panel:#0A2318; --row:#0F2E21; --line:#1C4433; --gold:#D4A72C; --gold2:#F1D58A;
        --sage:#8DB8A0; --text:#FFFFFF; --muted:#A9C4B5; --dim:#5E8270; }
:root[data-theme="light"] { --bg:#F6F3E8; --panel:#FFFFFF; --row:#EFEBDD; --line:#D9D2BC; --gold:#9A7414; --gold2:#7A5A0C;
        --sage:#3F6E55; --text:#14271D; --muted:#4D6658; --dim:#8A9C90; }
* { box-sizing:border-box; }
body { margin:0; background:var(--bg); color:var(--text); font-family:Calibri, Carlito, "Segoe UI", Arial, sans-serif; font-size:14px; }
h1, h2, h3 { font-family:Cambria, Georgia, serif; font-weight:bold; margin:0; }
a { color:var(--gold2); }
.hero { padding:22px 24px 14px; border-bottom:1px solid var(--line); display:flex; gap:24px; align-items:flex-end; flex-wrap:wrap; }
.hero h1 { font-size:28px; color:var(--gold2); letter-spacing:.3px; }
.hero p { margin:6px 0 0; color:var(--muted); max-width:760px; }
.stats { display:flex; gap:18px; margin-left:auto; flex-wrap:wrap; }
.stat b { display:block; font-size:22px; color:var(--gold); font-family:Cambria, Georgia, serif; }
.stat span { font-size:12px; color:var(--muted); }
nav { display:flex; gap:4px; padding:0 24px; border-bottom:1px solid var(--line); background:var(--panel); overflow-x:auto; }
nav button { background:none; border:0; color:var(--muted); padding:11px 14px; font:inherit; cursor:pointer; border-bottom:2px solid transparent; white-space:nowrap; }
nav button.on { color:var(--gold2); border-bottom-color:var(--gold); }
.tab { display:none; padding:16px 24px 40px; }
.tab.on { display:block; }
.bar { display:flex; gap:10px; flex-wrap:wrap; align-items:center; margin-bottom:12px; }
select, input[type=search] { background:var(--row); color:var(--text); border:1px solid var(--line); border-radius:6px; padding:6px 8px; font:inherit; }
.btn { background:var(--row); color:var(--text); border:1px solid var(--line); border-radius:6px; padding:6px 10px; font:inherit; cursor:pointer; }
.btn:hover { border-color:var(--gold); }
label.ck { color:var(--muted); display:flex; gap:5px; align-items:center; }
.layout { display:grid; grid-template-columns:minmax(0,1fr) 380px; gap:16px; }
@media (max-width: 1000px) { .layout { grid-template-columns:1fr; } }
#treewrap { position:relative; height:76vh; min-height:420px; overflow:hidden; border:1px solid var(--line); border-radius:8px; background:var(--panel);
  touch-action:none; cursor:grab; user-select:none; -webkit-user-select:none; }
#treewrap.drag { cursor:grabbing; }
#tsvg { display:block; width:100%; height:100%; }
#tsvg .nd { cursor:pointer; }
#tsvg .nd:hover text.lb { fill:var(--gold2); }
#colhead { position:absolute; top:0; left:0; right:0; height:34px; pointer-events:none; z-index:2;
  background:linear-gradient(var(--panel) 60%, transparent); }
#colhead span { position:absolute; top:10px; font-size:11px; letter-spacing:.7px; text-transform:uppercase; color:var(--sage); white-space:nowrap; }
.zoom { position:absolute; right:10px; bottom:10px; display:flex; gap:4px; z-index:3; }
.zoom button { background:var(--row); color:var(--text); border:1px solid var(--line); border-radius:6px; min-width:34px; height:32px; font:inherit; cursor:pointer; }
.zoom button:hover { border-color:var(--gold); }
.hint { position:absolute; left:12px; bottom:12px; font-size:12px; color:var(--muted); z-index:3; pointer-events:none; }
@media (max-width: 600px) { .hint { display:none; } }
.side { border:1px solid var(--line); border-radius:8px; background:var(--panel); padding:14px; max-height:78vh; overflow:auto; }
.side h3 { color:var(--gold2); font-size:17px; margin-bottom:4px; }
.kv { margin:8px 0; }
.kv b { display:block; color:var(--sage); font-size:12px; text-transform:uppercase; letter-spacing:.5px; margin-bottom:2px; }
.chip { display:inline-block; font-size:11px; padding:1px 7px; border-radius:10px; border:1px solid var(--line); color:var(--muted); margin:1px 2px 1px 0; }
.chip.g { border-color:var(--gold); color:var(--gold2); }
.legend { color:var(--muted); font-size:12px; display:flex; gap:14px; flex-wrap:wrap; margin:8px 0 0; }
.legend i { display:inline-block; width:22px; height:0; border-top:2px solid var(--sage); vertical-align:middle; margin-right:5px; }
.legend i.d { border-top:2px dashed var(--gold); }
table { border-collapse:collapse; width:100%; }
th, td { text-align:left; padding:6px 8px; border-bottom:1px solid var(--line); vertical-align:top; }
th { color:var(--sage); font-weight:normal; font-size:12px; text-transform:uppercase; letter-spacing:.4px; position:sticky; top:0; background:var(--panel); }
.tw { overflow:auto; border:1px solid var(--line); border-radius:8px; background:var(--panel); max-height:74vh; }
td.n { text-align:right; font-variant-numeric:tabular-nums; }
.muted { color:var(--muted); }
.cl { display:flex; flex-wrap:wrap; gap:4px 12px; max-height:120px; overflow:auto; border:1px solid var(--line); border-radius:6px; padding:8px; background:var(--row); }
.lvl3 { color:var(--gold2); } .lvl2 { color:var(--sage); }
.bar-s { height:8px; background:var(--row); border-radius:4px; overflow:hidden; min-width:60px; }
.bar-s span { display:block; height:100%; background:var(--gold); }
pre.md { white-space:pre-wrap; font-family:inherit; line-height:1.5; color:var(--text); max-width:900px; }
.note { color:var(--muted); font-size:13px; max-width:900px; margin:0 0 12px; }
@media (max-width: 600px) { .hero, nav, .tab { padding-left:16px; padding-right:16px; } .stats { margin-left:0; } }
</style>
</head>
<body>
<div class="hero">
  <div>
    <h1>The mother tree</h1>
    <p>Literature decides which mechanisms exist. The wording of each plan decides how precisely a commitment can be classified. Comparisons use the deepest level the compared observations share, and the finer detail is kept.</p>
  </div>
  <div class="stats" id="stats"></div>
</div>
<nav id="nav">
  <button data-t="tree" class="on">Tree</button>
  <button data-t="compare">Compare at</button>
  <button data-t="mech">Mechanisms</button>
  <button data-t="obj">Objectives</button>
  <button data-t="val">Validation</button>
</nav>

<section class="tab on" id="tree">
  <div class="bar">
    <select id="tCountry"><option value="">All countries</option></select>
    <select id="tRisk"><option value="">All risks</option></select>
    <input type="search" id="tSearch" placeholder="Find an objective or mechanism">
    <button class="btn" id="tFam">Open families</button>
    <button class="btn" id="tMech">Open mechanisms</button>
    <button class="btn" id="tCollapse">Collapse</button>
    <label class="ck"><input type="checkbox" id="tEmpty" checked> Show empty nodes</label>
    <label class="ck"><input type="checkbox" id="tStd" checked> Show Standard and goals</label>
  </div>
  <div class="layout">
    <div>
      <div id="treewrap"><div id="colhead"></div><svg id="tsvg" role="img" aria-label="Mother tree"><g id="vp"></g></svg>
        <div class="zoom"><button id="zIn" title="Zoom in">+</button><button id="zOut" title="Zoom out">−</button><button id="zFit" title="Fit the tree">Fit</button></div>
</div>
      <div class="legend"><span><i></i>canonical placement</span><span><i class="d"></i>objective placed on its family (L2): the plan does not name the channel</span><span>ringed node: closed, click to open</span><span>node size: strategies</span><span>drag or scroll to move · pinch or Ctrl/⌘ + scroll to zoom</span></div>
    </div>
    <div class="side" id="side"><h3>Read the tree</h3><p class="muted">Pillar → subpillar → mechanism family (L2) → mechanism (L3) → objective (L4). Click any node for its definition, literature and placement reasons. Gold nodes hold strategies; grey nodes are empty: the literature names the channel and no plan commits to it.</p></div>
  </div>
</section>

<section class="tab" id="compare">
  <p class="note">Pick the countries to compare. For each family the table uses the deepest level every selected country's strategies share: L3 when all of them are classified at a mechanism, otherwise L2, with the share classified finer disclosed per country.</p>
  <div class="bar"><select id="cSub"><option value="">All subpillars</option></select>
    <button class="btn" id="cAll">Select all</button><button class="btn" id="cNone">Clear</button></div>
  <div class="cl" id="cList"></div>
  <div id="cOut" style="margin-top:14px"></div>
</section>

<section class="tab" id="mech">
  <div class="bar">
    <select id="mSub"><option value="">All subpillars</option></select>
    <select id="mRisk"><option value="">All risks</option></select>
    <label class="ck"><input type="checkbox" id="mEmpty"> Empty nodes only</label>
    <input type="search" id="mSearch" placeholder="Search">
  </div>
  <div class="tw"><table id="mTab"></table></div>
</section>

<section class="tab" id="obj">
  <div class="bar">
    <select id="oLvl"><option value="">All depths</option><option value="3">L3 mechanism</option><option value="2">L2 family</option><option value="0">Standard holding</option><option value="-1">Goal held outside</option></select>
    <select id="oSub"><option value="">All subpillars</option></select>
    <input type="search" id="oSearch" placeholder="Search">
  </div>
  <div class="tw"><table id="oTab"></table></div>
</section>

<section class="tab" id="val"><pre class="md" id="valtxt"></pre></section>

<script>
const D = __DATA__;
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const SUBC = Object.fromEntries(D.subs.map(s => [s.c, s]));
const PILL = [...new Set(D.subs.map(s => s.p))];
let F = {country:"", risk:"", q:"", empty:true, std:true};
const NAMED = D.subs.filter(s => !s.std).map(s => "S:" + s.c);
let open = new Set(["root", ...PILL.map(p => "P:" + p), ...NAMED, "P:GOAL"]);
let sel = null;

// ---------- counts
function counts() {
  const c = {o:new Array(D.O.length).fill(0), m:new Array(D.M.length).fill(0), f:new Array(D.F.length).fill(0), s:{}, h:{}};
  const ci = F.country === "" ? -1 : D.C.indexOf(F.country);
  for (const s of D.S) {
    if (ci >= 0 && s[0] !== ci) continue;
    c.o[s[1]]++;
    if (s[3] >= 0) c.m[s[3]]++;
    if (s[4] >= 0) { c.f[s[4]]++; const sub = D.F[s[4]].s; c.s[sub] = (c.s[sub] || 0) + 1; }
    else if (s[5]) { c.h[s[5]] = (c.h[s[5]] || 0) + 1; if (s[5] !== "GOAL") c.s[s[5]] = (c.s[s[5]] || 0) + 1; }
  }
  return c;
}
// ---------- build tree
function riskOk(rk) { return !F.risk || rk.split(" | ").includes(F.risk); }
function build() {
  const C = counts();
  const q = F.q.toLowerCase();
  const hitObj = o => !q || o.n.toLowerCase().includes(q);
  const root = {id:"root", k:"root", label:"PV II mother tree", kids:[]};
  for (const p of PILL) {
    const pn = {id:"P:" + p, k:"pillar", label:p, kids:[], n:0};
    for (const s of D.subs.filter(x => x.p === p)) {
      if (s.std && !F.std) continue;
      const sn = {id:"S:" + s.c, k:"sub", label:s.n, code:s.c, std:s.std, kids:[], n:C.s[s.c] || 0};
      if (s.std) {
        D.O.forEach((o, i) => { if (o.h === s.c && hitObj(o)) sn.kids.push({id:"O:" + i, k:"obj", label:o.n, oi:i, n:C.o[i], direct:true}); });
      } else {
        D.F.forEach((f, fi) => {
          if (f.s !== s.c) return;
          const fn = {id:"F:" + fi, k:"fam", label:f.n, fi, kids:[], n:C.f[fi]};
          D.M.forEach((m, mi) => {
            if (m.f !== fi) return;
            if (!riskOk(m.rk)) return;
            const mn = {id:"M:" + mi, k:"mech", label:m.n, mi, kids:[], n:C.m[mi]};
            D.O.forEach((o, oi) => { if (o.m === mi && hitObj(o)) mn.kids.push({id:"O:" + oi, k:"obj", label:o.n, oi, n:C.o[oi]}); });
            if (!F.empty && mn.n === 0) return;
            if (q && !mn.kids.length && !m.n.toLowerCase().includes(q)) return;
            fn.kids.push(mn);
          });
          D.O.forEach((o, oi) => { if (o.lv === 2 && o.f === fi && hitObj(o) && (!F.risk || true)) fn.kids.push({id:"O:" + oi, k:"obj", label:o.n, oi, n:C.o[oi], direct:true}); });
          if (F.risk && !fn.kids.some(k => k.k === "mech")) return;
          if (q && !fn.kids.length && !f.n.toLowerCase().includes(q)) return;
          sn.kids.push(fn);
        });
      }
      if (q && !sn.kids.length) continue;
      pn.kids.push(sn); pn.n += sn.n;
    }
    if (pn.kids.length) root.kids.push(pn);
  }
  if (F.std) {
    const g = {id:"S:GOAL", k:"sub", label:"Goals held outside the tree", code:"GOAL", std:true, kids:[], n:C.h.GOAL || 0};
    D.O.forEach((o, i) => { if (o.h === "GOAL" && hitObj(o)) g.kids.push({id:"O:" + i, k:"obj", label:o.n, oi:i, n:C.o[i], direct:true}); });
    if (g.kids.length) root.kids.push({id:"P:GOAL", k:"pillar", label:"Outside the tree", kids:[g], n:g.n});
  }
  root.n = root.kids.reduce((a, b) => a + (b.n || 0), 0);
  return root;
}
// ---------- layout: columns sized to their widest label, links routed in the gaps between columns
const COLS = ["pillar", "sub", "fam", "mech", "obj"];
const COLNAME = {pillar:"Pillar", sub:"RHDR subpillar", fam:"L2 · mechanism family", mech:"L3 · mechanism", obj:"L4 · objective"};
const SANS = "Calibri, Carlito, 'Segoe UI', Arial, sans-serif";
const FONT = {pillar:"700 16px Cambria, Georgia, serif", sub:"700 14px " + SANS, fam:"600 13.5px " + SANS, mech:"400 13px " + SANS, obj:"400 12.5px " + SANS};
const CNT = "400 11px " + SANS;
const ROW = 30, GAP = 60, TOP = 52;
const mctx = document.createElement("canvas").getContext("2d");
const wcache = new Map();
function tw(txt, font) { const k = font + "|" + txt; if (!wcache.has(k)) { mctx.font = font; wcache.set(k, mctx.measureText(txt).width); } return wcache.get(k); }
function r(n) { return Math.max(4, Math.min(12, 3 + Math.sqrt(n.n || 0) * 0.85)); }
function labelW(n) { return tw(n.label, FONT[n.k]) + (n.n ? 6 + tw(String(n.n), CNT) : 0); }
let LAY = null, T = {x:0, y:0, k:1};
function layout(root) {
  let y = TOP; const nodes = [], links = [], col = {};
  (function walk(n, parent) {
    const kids = (open.has(n.id) || F.q) ? n.kids : [];
    n.vis = kids;
    if (n.k !== "root") { nodes.push(n); (col[n.k] = col[n.k] || []).push(n); }
    if (!kids.length) { n.y = y; y += ROW; }
    else { kids.forEach(k => walk(k, n)); n.y = (kids[0].y + kids[kids.length - 1].y) / 2; }
    if (parent && parent.k !== "root") links.push([parent, n]);
  })(root, null);
  const X = {}; let x = 24;
  for (const c of COLS) {
    if (!col[c]) continue;
    X[c] = x;
    x += Math.max(...col[c].map(n => r(n) + 8 + labelW(n))) + GAP;
  }
  nodes.forEach(n => n.x = X[n.k]);
  const byId = new Map(nodes.map(n => [n.id, n]));
  return {nodes, links, X, byId, w:x, h:y + 20};
}
function linkPath(a, b, X, offset) {
  const sx = a.x + r(a) + 8 + labelW(a) + 6;
  const nextCol = COLS[COLS.indexOf(a.k) + 1];
  const tx = (X[nextCol] !== undefined ? X[nextCol] : b.x) - 24 + (offset || 0);
  const ex = b.x - r(b) - 3, rr = 7;
  if (Math.abs(b.y - a.y) < 1) return `M${sx},${a.y} H${ex}`;
  const d = b.y > a.y ? 1 : -1, q = Math.min(rr, Math.abs(b.y - a.y) / 2);
  return `M${sx},${a.y} H${tx - q} Q${tx},${a.y} ${tx},${a.y + d * q} V${b.y - d * q} Q${tx},${b.y} ${tx + q},${b.y} H${ex}`;
}
function render(anchorId) {
  let before = null;
  if (anchorId && LAY && LAY.byId.get(anchorId)) { const n = LAY.byId.get(anchorId); before = {x:n.x * T.k + T.x, y:n.y * T.k + T.y}; }
  const root = build(); LAY = layout(root);
  const q = F.q.toLowerCase();
  let s = "";
  for (const [a, b] of LAY.links) {
    const dashed = b.direct && a.k === "fam";
    const hold = b.direct && a.k === "sub";
    s += `<path d="${linkPath(a, b, LAY.X, dashed ? 6 : 0)}" fill="none" stroke="${dashed ? "var(--gold)" : hold ? "var(--dim)" : "var(--line)"}" stroke-width="${dashed ? 1.5 : 1.3}" ${dashed ? 'stroke-dasharray="5 4"' : ""}/>`;
  }
  for (const n of LAY.nodes) {
    const empty = (n.n || 0) === 0;
    const closed = n.kids && n.kids.length && !n.vis.length;
    const fill = empty ? "var(--dim)" : (n.k === "obj" ? "var(--gold2)" : n.k === "mech" ? "var(--gold)" : "var(--sage)");
    const hit = q && n.label.toLowerCase().includes(q);
    const R = r(n);
    s += `<g class="nd" data-id="${n.id}" transform="translate(${n.x},${n.y})">
      <circle r="${R + 9}" fill="transparent"/>
      ${closed ? `<circle r="${R + 3.5}" fill="none" stroke="${fill}" stroke-width="1.4" opacity=".8"/>` : ""}
      <circle r="${R}" fill="${fill}" ${sel === n.id ? 'stroke="var(--text)" stroke-width="2"' : ""}/>
      <text class="lb" x="${R + 8}" y="4.5" style="font:${FONT[n.k]}" fill="${hit ? "var(--gold2)" : empty ? "var(--dim)" : "var(--text)"}">${esc(n.label)}${n.n ? `<tspan dx="6" style="font:${CNT}" fill="var(--muted)">${n.n}</tspan>` : ""}</text></g>`;
  }
  document.getElementById("vp").innerHTML = s;
  if (before) { const n = LAY.byId.get(anchorId); if (n) { T.x = before.x - n.x * T.k; T.y = before.y - n.y * T.k; } }
  apply();
  saveHash();
}
// ---------- pan and zoom
const wrap = document.getElementById("treewrap"), svg = document.getElementById("tsvg");
function apply() {
  document.getElementById("vp").setAttribute("transform", `translate(${T.x},${T.y}) scale(${T.k})`);
  const head = document.getElementById("colhead");
  let prev = -1e9, h = "";
  if (LAY) for (const c of COLS) {
    if (LAY.X[c] === undefined) continue;
    const left = T.x + LAY.X[c] * T.k - 6, w = tw(COLNAME[c].toUpperCase(), "400 11px " + SANS) * 1.12;
    if (left < prev + 14) continue;
    h += `<span style="left:${left}px">${COLNAME[c]}</span>`; prev = left + w;
  }
  head.innerHTML = h;
}
function zoomAt(px, py, f) {
  const k2 = Math.max(0.12, Math.min(2.5, T.k * f)); const g = k2 / T.k;
  T.x = px - (px - T.x) * g; T.y = py - (py - T.y) * g; T.k = k2; apply();
}
function home(col) {
  // readable zoom, anchored top-left; with col, the view starts at that column (earlier columns are a drag away)
  if (!LAY || !LAY.nodes.length) return;
  const minY = Math.min(...LAY.nodes.map(n => n.y));
  T.k = wrap.clientWidth < 700 ? 0.8 : col ? 0.9 : 1;
  T.x = col && LAY.X[col] !== undefined ? 24 - LAY.X[col] * T.k : 12;
  T.y = 44 - (minY - 10) * T.k; apply();
}
function fitOrHome() {
  if (!LAY || !LAY.nodes.length) return;
  const W = wrap.clientWidth, H = wrap.clientHeight;
  const maxX = Math.max(...LAY.nodes.map(n => n.x + r(n) + 8 + labelW(n))), ys = LAY.nodes.map(n => n.y);
  const k = Math.min(W / (maxX + 20), (H - 50) / (Math.max(...ys) - Math.min(...ys) + 60));
  k >= 0.7 ? fit() : home();
}
function fit() {
  if (!LAY || !LAY.nodes.length) return;
  const W = wrap.clientWidth, H = wrap.clientHeight;
  const maxX = Math.max(...LAY.nodes.map(n => n.x + r(n) + 8 + labelW(n))), minY = Math.min(...LAY.nodes.map(n => n.y)), maxY = Math.max(...LAY.nodes.map(n => n.y));
  const w = maxX + 20, h = maxY - minY + 60;
  T.k = Math.max(0.12, Math.min(1.15, W / w, (H - 50) / h));
  T.x = Math.max(8, (W - w * T.k) / 2); T.y = 40 - (minY - 16) * T.k + Math.max(0, (H - 50 - h * T.k) / 2);
  apply();
}
const ptr = new Map(); let drag = null, moved = false, pinch = null;
svg.addEventListener("pointerdown", e => {
  svg.setPointerCapture(e.pointerId); ptr.set(e.pointerId, {x:e.clientX, y:e.clientY});
  if (ptr.size === 1) { drag = {x:e.clientX, y:e.clientY, tx:T.x, ty:T.y}; moved = false; wrap.classList.add("drag"); }
  if (ptr.size === 2) { const [p1, p2] = [...ptr.values()]; pinch = {d:Math.hypot(p1.x - p2.x, p1.y - p2.y), k:T.k}; drag = null; moved = true; }
});
svg.addEventListener("pointermove", e => {
  if (!ptr.has(e.pointerId)) return; ptr.set(e.pointerId, {x:e.clientX, y:e.clientY});
  if (pinch && ptr.size === 2) {
    const [p1, p2] = [...ptr.values()]; const rect = wrap.getBoundingClientRect();
    const f = (Math.hypot(p1.x - p2.x, p1.y - p2.y) / pinch.d) * pinch.k / T.k;
    zoomAt((p1.x + p2.x) / 2 - rect.left, (p1.y + p2.y) / 2 - rect.top, f); return;
  }
  if (drag) {
    const dx = e.clientX - drag.x, dy = e.clientY - drag.y;
    if (Math.abs(dx) + Math.abs(dy) > 4) moved = true;
    T.x = drag.tx + dx; T.y = drag.ty + dy; apply();
  }
});
function endPtr(e) {
  ptr.delete(e.pointerId); if (ptr.size < 2) pinch = null;
  if (!ptr.size) {
    wrap.classList.remove("drag");
    if (drag && !moved) { const g = document.elementFromPoint(e.clientX, e.clientY)?.closest(".nd"); if (g) clickNode(g.dataset.id); }
    drag = null;
  }
}
svg.addEventListener("pointerup", endPtr); svg.addEventListener("pointercancel", endPtr);
wrap.addEventListener("wheel", e => {
  e.preventDefault(); const rect = wrap.getBoundingClientRect();
  if (e.ctrlKey || e.metaKey) zoomAt(e.clientX - rect.left, e.clientY - rect.top, Math.exp(-e.deltaY * 0.01));
  else { T.x -= e.deltaX; T.y -= e.deltaY; apply(); }
}, {passive:false});
document.getElementById("zIn").onclick = () => zoomAt(wrap.clientWidth / 2, wrap.clientHeight / 2, 1.25);
document.getElementById("zOut").onclick = () => zoomAt(wrap.clientWidth / 2, wrap.clientHeight / 2, 0.8);
document.getElementById("zFit").onclick = fit;
window.addEventListener("resize", () => apply());
function reveal(id) {
  // after opening a node, pan just enough to bring its new children into view, keeping the node itself visible
  const n = LAY.byId.get(id); if (!n || !n.vis.length) return;
  const W = wrap.clientWidth, H = wrap.clientHeight, k = T.k;
  const right = Math.max(...n.vis.map(c => c.x + r(c) + 8 + labelW(c))) * k + T.x;
  if (right > W - 16) T.x -= Math.min(right - (W - 16), n.x * k + T.x - 24);
  const top = n.vis[0].y * k + T.y, bot = n.vis[n.vis.length - 1].y * k + T.y;
  if (bot > H - 30) T.y -= Math.min(bot - (H - 30), Math.max(0, top - 44));
  if (top < 44) T.y += Math.min(44 - top, Math.max(0, (H - 30) - bot));
  apply();
}
function clickNode(id) {
  const n = LAY && LAY.byId.get(id);
  let opened = false;
  if (n && n.kids && n.kids.length && !F.q) { if (open.has(id)) open.delete(id); else { open.add(id); opened = true; } }
  sel = id; render(id); if (opened) reveal(id); showSide(id);
}
function kv(k, v) { return v ? `<div class="kv"><b>${k}</b>${v}</div>` : ""; }
function chips(s, g) { return (s || "").split(" | ").filter(Boolean).map(x => `<span class="chip ${g ? "g" : ""}">${esc(x)}</span>`).join(""); }
function strategiesOf(test, title) {
  const ci = F.country === "" ? -1 : D.C.indexOf(F.country);
  const rows = D.S.filter(s => test(s) && (ci < 0 || s[0] === ci));
  if (!rows.length) return "";
  return `<div class="kv"><b>${title || "Strategies"} (${rows.length})</b>` + rows.slice(0, 60).map(s =>
    `<div style="margin:4px 0"><span class="chip">${esc(D.C[s[0]])}</span> ${esc(s[6])}${s[7].startsWith("deepened") || s[7].startsWith("goal triage: disg") || s[7].startsWith("split") ? ` <span class="chip g" title="${esc(s[7])}">${esc(s[7].startsWith("deepened") ? "deepened" : s[7].startsWith("split") ? "split" : "re-homed")}: ${esc(s[8])}</span>` : ""}${s[9] ? ' <span class="chip">BAU</span>' : ""}</div>`).join("") +
    (rows.length > 60 ? `<div class="muted">and ${rows.length - 60} more</div>` : "") + "</div>";
}
function showSide(id) {
  const [k, v] = id.split(":"); const el = document.getElementById("side"); let h = "";
  if (k === "F") { const f = D.F[+v];
    h = `<h3>${esc(f.n)}</h3><span class="chip">${f.id} · L2 family</span><span class="chip g">${esc(SUBC[f.s].n)}</span>` +
      kv("Definition", esc(f.d)) + kv("Core variables", esc(f.cv)) + kv("Inclusion", esc(f.inc)) + kv("Exclusion", esc(f.exc)) +
      kv("Primary subpillar, reason", esc(f.why)) + kv("Secondary subpillars", chips(f.sec)) + kv("Risks", chips(f.rk, 1)) + kv("Literature", esc(f.lit)) +
      strategiesOf(s => s[4] === +v && s[2] === 2, "Strategies placed on the family (L2)");
  } else if (k === "M") { const m = D.M[+v];
    h = `<h3>${esc(m.n)}</h3><span class="chip">${m.id} · L3 mechanism</span><span class="chip">${esc(D.F[m.f].n)}</span>` +
      kv("Causal input", esc(m.i)) + kv("Transmission", esc(m.t)) + kv("Outcome", esc(m.o)) + kv("Conditions", esc(m.c)) +
      kv("Distinct from siblings", esc(m.ds)) + kv("Evidence", esc(m.e)) + kv("Risks", chips(m.rk, 1) + (m.rj ? `<div class="muted">${esc(m.rj)}</div>` : "")) +
      kv("Classification suitability", esc(m.su)) + kv("Evidence status", esc(m.ev)) + kv("Risk-tag status", esc(m.rs)) +
      kv("Conditional risk links", chips(m.cr)) + kv("Rejected risk links", chips(m.rr)) + strategiesOf(s => s[3] === +v);
  } else if (k === "O") { const o = D.O[+v];
    const lv = {3:"L3 mechanism", 2:"L2 family", 0:"Standard holding", "-1":"Goal held outside"}[o.lv];
    h = `<h3>${esc(o.n)}</h3><span class="chip">${o.id} · ${lv}</span><span class="chip">${esc(o.b)}</span><span class="chip">confidence ${esc(o.cf)}</span>${o.bau ? '<span class="chip">BAU</span>' : ""}` +
      kv("Definition", esc(o.d)) + kv("Depth reason", esc(o.r)) + kv("Candidate mechanisms", chips(o.c)) + kv("Secondary subpillar", esc(o.sr)) +
      kv("Source objectives", esc(o.src)) + kv("Merge history", esc(o.mh)) + strategiesOf(s => s[1] === +v);
  } else if (k === "S") { const s = SUBC[v];
    h = `<h3>${esc(s ? s.n : "Goals held outside the tree")}</h3>` + (s && s.std ? `<p class="muted">Standard holding branch: no literature levels, visible here and dropped from reporting.</p>` : v === "GOAL" ? `<p class="muted">Goal-shaped objectives. Each strategy was re-read: those naming a channel were re-homed; the rest are held here.</p>` : `<p class="muted">RHDR subpillar. Its families come from the literature review, filed here by their primary welfare channel.</p>`);
  } else { h = `<h3>${esc(id.slice(2) || "PV II mother tree")}</h3>`; }
  el.innerHTML = h;
}
// ---------- tree controls
function saveHash() { try { history.replaceState(null, "", "#" + new URLSearchParams({c:F.country, r:F.risk}).toString()); } catch (e) {} }
function fillSel(id, items, keep) { const s = document.getElementById(id); items.forEach(x => { const o = document.createElement("option"); o.value = x[0]; o.textContent = x[1]; s.appendChild(o); }); }
fillSel("tCountry", D.C.map(c => [c, c.replace(/_/g, " ")]));
fillSel("tRisk", D.risks.map(r => [r, r]));
["cSub", "mSub", "oSub"].forEach(id => fillSel(id, D.subs.filter(s => !s.std).map(s => [s.c, s.n])));
fillSel("mRisk", D.risks.map(r => [r, r]));
document.getElementById("tCountry").onchange = e => { F.country = e.target.value; render(); };
document.getElementById("tRisk").onchange = e => { F.risk = e.target.value; render(); home(); };
let qTimer = null;
document.getElementById("tSearch").oninput = e => { clearTimeout(qTimer); qTimer = setTimeout(() => { F.q = e.target.value.trim(); render(); fitOrHome(); }, 180); };
document.getElementById("tEmpty").onchange = e => { F.empty = e.target.checked; render(); };
document.getElementById("tStd").onchange = e => { F.std = e.target.checked; render(); };
document.getElementById("tFam").onclick = () => { D.F.forEach((f, i) => { open.delete("F:" + i); D.M.forEach((m, mi) => open.delete("M:" + mi)); }); NAMED.forEach(x => open.add(x)); open.add("P:GOAL"); render(); home(); };
document.getElementById("tMech").onclick = () => { NAMED.forEach(x => open.add(x)); D.F.forEach((f, i) => open.add("F:" + i)); render(); home("fam"); };
document.getElementById("tCollapse").onclick = () => { open = new Set(["root", ...PILL.map(p => "P:" + p), "P:GOAL"]); render(); home(); };
// ---------- compare
const cSel = new Set();
function cList() {
  document.getElementById("cList").innerHTML = D.C.map((c, i) => `<label class="ck"><input type="checkbox" data-i="${i}" ${cSel.has(i) ? "checked" : ""}> ${esc(c.replace(/_/g, " "))}</label>`).join("");
  document.querySelectorAll("#cList input").forEach(x => x.onchange = () => { x.checked ? cSel.add(+x.dataset.i) : cSel.delete(+x.dataset.i); cOut(); });
}
function cOut() {
  const el = document.getElementById("cOut"); const cs = [...cSel].sort((a, b) => a - b);
  if (cs.length < 2) { el.innerHTML = `<p class="muted">Select two or more countries.</p>`; return; }
  const sub = document.getElementById("cSub").value;
  let h = `<div class="tw"><table><tr><th>Family</th><th>Compared at</th>${cs.map(c => `<th>${esc(D.C[c].replace(/_/g, " "))}</th>`).join("")}</tr>`;
  D.F.forEach((f, fi) => {
    if (sub && f.s !== sub) return;
    const per = cs.map(c => D.S.filter(s => s[0] === c && s[4] === fi));
    if (per.every(p => !p.length)) return;
    const allL3 = per.every(p => p.length && p.every(s => s[2] === 3));
    if (allL3) {
      const ms = [...new Set(per.flat().map(s => s[3]))];
      h += `<tr><td><b>${esc(f.n)}</b><div class="muted">${esc(SUBC[f.s].n)}</div></td><td class="lvl3">L3 mechanism</td>` +
        per.map(p => `<td>${ms.map(mi => { const k = p.filter(s => s[3] === mi).length; return k ? `<div>${esc(D.M[mi].n)}: <b>${k}</b></div>` : ""; }).join("")}</td>`).join("") + "</tr>";
    } else {
      h += `<tr><td><b>${esc(f.n)}</b><div class="muted">${esc(SUBC[f.s].n)}</div></td><td class="lvl2">L2 family</td>` +
        per.map(p => { const fin = p.filter(s => s[2] === 3).length; const sh = p.length ? fin / p.length : 0;
          return `<td><b>${p.length}</b>${p.length ? `<div class="muted" style="font-size:12px">${Math.round(sh * 100)}% classified finer</div><div class="bar-s"><span style="width:${sh * 100}%"></span></div>` : ""}</td>`; }).join("") + "</tr>";
    }
  });
  el.innerHTML = h + "</table></div>";
}
document.getElementById("cSub").onchange = cOut;
document.getElementById("cAll").onclick = () => { D.C.forEach((c, i) => cSel.add(i)); cList(); cOut(); };
document.getElementById("cNone").onclick = () => { cSel.clear(); cList(); cOut(); };
// ---------- mechanisms table
function mTab() {
  const sub = document.getElementById("mSub").value, rk = document.getElementById("mRisk").value, em = document.getElementById("mEmpty").checked;
  const q = document.getElementById("mSearch").value.toLowerCase();
  const n = new Array(D.M.length).fill(0); D.S.forEach(s => { if (s[3] >= 0) n[s[3]]++; });
  let h = `<tr><th>Mechanism</th><th>Family</th><th>Input → transmission → outcome</th><th>Conditions</th><th>Evidence</th><th>Risks</th><th class="n">Strategies</th></tr>`;
  D.M.forEach((m, i) => {
    const f = D.F[m.f];
    if (sub && f.s !== sub) return; if (rk && !m.rk.split(" | ").includes(rk)) return; if (em && n[i]) return;
    if (q && !(m.n + f.n + m.e + m.i + m.o).toLowerCase().includes(q)) return;
    h += `<tr><td><b>${esc(m.n)}</b><div class="muted">${m.id}</div></td><td>${esc(f.n)}<div class="muted">${esc(SUBC[f.s].n)}</div></td><td>${esc(m.i)} → ${esc(m.t)} → ${esc(m.o)}</td><td>${esc(m.c)}</td><td>${esc(m.e)}</td><td>${chips(m.rk)}</td><td class="n">${n[i] || '<span class="muted">empty</span>'}</td></tr>`;
  });
  document.getElementById("mTab").innerHTML = h;
}
["mSub", "mRisk", "mEmpty"].forEach(id => document.getElementById(id).onchange = mTab);
document.getElementById("mSearch").oninput = mTab;
// ---------- objectives table
function oTab() {
  const lv = document.getElementById("oLvl").value, sub = document.getElementById("oSub").value, q = document.getElementById("oSearch").value.toLowerCase();
  const n = new Array(D.O.length).fill(0); D.S.forEach(s => n[s[1]]++);
  let h = `<tr><th>Objective</th><th>Canonical node</th><th>Depth reason</th><th>Basis</th><th class="n">Strategies</th></tr>`;
  D.O.forEach((o, i) => {
    if (lv !== "" && String(o.lv) !== lv) return;
    const f = o.f >= 0 ? D.F[o.f] : null;
    if (sub && (!f || f.s !== sub)) return;
    if (q && !(o.n + o.d).toLowerCase().includes(q)) return;
    const node = o.m >= 0 ? `<span class="lvl3">${esc(D.M[o.m].n)}</span><div class="muted">${esc(f.n)}</div>` : f && o.lv === 2 ? `<span class="lvl2">${esc(f.n)}</span><div class="muted">L2</div>` : `<span class="muted">${esc({SPE:"Standard People", SEC:"Standard Economy", SGO:"Standard Governance", GOAL:"Goal held outside"}[o.h] || "")}</span>`;
    h += `<tr><td><b>${esc(o.n)}</b><div class="muted">${o.id}</div></td><td>${node}</td><td>${esc(o.r)}${o.c ? `<div style="margin-top:4px">${chips(o.c)}</div>` : ""}</td><td>${esc(o.b)}<div class="muted">${esc(o.cf)}</div></td><td class="n">${n[i]}</td></tr>`;
  });
  document.getElementById("oTab").innerHTML = h;
}
["oLvl", "oSub"].forEach(id => document.getElementById(id).onchange = oTab);
document.getElementById("oSearch").oninput = oTab;
// ---------- tabs, stats, boot
document.querySelectorAll("#nav button").forEach(b => b.onclick = () => {
  document.querySelectorAll("#nav button").forEach(x => x.classList.toggle("on", x === b));
  document.querySelectorAll(".tab").forEach(t => t.classList.toggle("on", t.id === b.dataset.t));
});
const l3 = D.S.filter(s => s[2] === 3).length, empt = D.M.filter((m, i) => !D.S.some(s => s[3] === i)).length;
document.getElementById("stats").innerHTML = [[D.F.length, "families (L2)"], [D.M.length, "mechanisms (L3)"], [D.O.length, "objectives"], [D.S.length.toLocaleString(), "strategies"], [Math.round(100 * l3 / D.S.length) + "%", "strategies at L3"], [empt, "empty nodes"]]
  .map(([a, b]) => `<div class="stat"><b>${a}</b><span>${b}</span></div>`).join("");
document.getElementById("valtxt").textContent = D.validation;
try { const p = new URLSearchParams(location.hash.slice(1)); if (p.get("c")) { F.country = p.get("c"); document.getElementById("tCountry").value = F.country; } if (p.get("r")) { F.risk = p.get("r"); document.getElementById("tRisk").value = F.risk; } } catch (e) {}
render(); home(); cList(); cOut(); mTab(); oTab();
</script>
</body>
</html>
"""
out = PAGE.replace("__DATA__", json.dumps(DATA, ensure_ascii=False, separators=(",", ":")))
open(os.path.join(HERE, "mother_tree.html"), "w").write(out)
print("mother_tree.html", round(len(out) / 1e6, 2), "MB")
