// The country forest: each country drawn as its own plant in its own landscape, on the one structure of tree v4.
// Ported from the mirror-forests page of 22 October 2026 (PV2/support/golden_tree/art/v2/china_bamboo), which drew
// tree v1; the scenes and plants are that page's, unchanged. Here a stem is a live family, the nodes along it are its
// levers (gold where a strategy in view sits on one), and each leaf is one strategy in view (gold on a lever, green
// on the family only). Stems stand in three stands (economy, people, governance) and ten clumps (the subpillars).
// Inlined by viewer.py at /*FOREST*/; draws into the <svg id="forest"> of the country explorer.
const Forest = (() => {
const NS = "http://www.w3.org/2000/svg";
const ORDER = ["SMG", "PFA", "MCH"], STAND = { SMG: "ECONOMY", PFA: "PEOPLE", MCH: "GOVERNANCE" };
// one plant and one landscape per country. The Asia-Pacific entries are the mirror-forests page's; the fourteen
// outside Asia-Pacific (marked *) were added on 18 November 2026 from the same plants and scenes, for review.
const C = {
  china: { plant: "bamboo", scene: "bamboo", line: "Bamboo: separate culms, one rhizome beneath them." },
  mongolia: { plant: "grass", scene: "steppe", line: "Feather grass on the open steppe." },
  brunei: { plant: "emergent", scene: "rainforest", line: "Dipterocarps above the Borneo rainforest." },
  cambodia: { plant: "palm", var: "sugar", scene: "paddy", line: "Sugar palms standing in the rice fields." },
  indonesia: { plant: "palm", scene: "volcano", line: "Palms in the rainforest below the volcano." },
  malaysia: { plant: "emergent", scene: "rainforest", line: "Dipterocarps rising out of the rainforest canopy." },
  myanmar: { plant: "emergent", var: "teak", scene: "teak", line: "Teak on the misted hills." },
  philippines: { plant: "palm", scene: "terraces", line: "Coconut palms above the rice terraces." },
  thailand: { plant: "rice", scene: "paddy", line: "Rice in the flooded paddy, heads heavy with grain." },
  timor_leste: { plant: "emergent", var: "eucalypt", scene: "savanna", line: "Eucalypts on the dry hills." },
  vietnam: { plant: "lotus", scene: "karst", line: "Lotus in still water among the karst towers." },
  afghanistan: { plant: "conifer", var: "poplar", scene: "desert", line: "Poplars along a river in the dry mountains." },
  bangladesh: { plant: "mangrove", scene: "delta", line: "Mangroves on the Sundarbans delta." },
  bhutan: { plant: "conifer", scene: "himalaya", line: "Blue pine below the Himalayan snowline." },
  india: { plant: "banyan", scene: "banyan", line: "One banyan, its pillar roots standing as a grove." },
  iran: { plant: "conifer", var: "cypress", scene: "desert", line: "Cypresses in a garden at the edge of the desert." },
  maldives: { plant: "palm", scene: "atoll", line: "Coconut palms on a coral atoll." },
  nepal: { plant: "conifer", scene: "himalaya", line: "Fir forest below the Himalayan peaks." },
  pakistan: { plant: "palm", var: "date", scene: "desert", line: "Date palms along the Indus." },
  sri_lanka: { plant: "emergent", var: "shade", scene: "terraces", line: "Shade trees over the tea terraces." },
  fiji: { plant: "palm", scene: "island", line: "Coconut palms on a high island." },
  kiribati: { plant: "palm", scene: "atoll", line: "Coconut palms on a low atoll." },
  marshall_islands: { plant: "palm", scene: "atoll", line: "Coconut palms on a ring of coral." },
  nauru: { plant: "palm", scene: "island", line: "Palms on a raised coral island." },
  palau: { plant: "mangrove", scene: "karstwater", line: "Mangroves among the Rock Islands." },
  papua_new_guinea: { plant: "palm", var: "fern", scene: "rainforest", line: "Tree ferns in the highland cloud forest." },
  samoa: { plant: "palm", scene: "island", line: "Coconut palms on a volcanic island." },
  solomon_islands: { plant: "palm", var: "fern", scene: "island", line: "Tree ferns on a forested island." },
  tonga: { plant: "palm", scene: "atoll", line: "Coconut palms on a coral island." },
  tuvalu: { plant: "palm", scene: "atoll", line: "Coconut palms a metre above the sea." },
  vanuatu: { plant: "banyan", scene: "banyan", line: "A banyan grove, many roots under one canopy." },
  brazil: { plant: "emergent", scene: "rainforest", line: "Emergents above the Amazon canopy.", added: 1 },
  colombia: { plant: "palm", scene: "himalaya", line: "Wax palms below the Andean peaks.", added: 1 },
  peru: { plant: "grass", scene: "steppe", line: "Ichu grass on the high Andean puna.", added: 1 },
  jamaica: { plant: "palm", scene: "island", line: "Coconut palms on a Caribbean island.", added: 1 },
  egypt: { plant: "palm", var: "date", scene: "desert", line: "Date palms along the Nile.", added: 1 },
  morocco: { plant: "conifer", scene: "himalaya", line: "Cedars below the Atlas snowline.", added: 1 },
  ethiopia: { plant: "emergent", var: "shade", scene: "terraces", line: "Shade trees over the highland coffee.", added: 1 },
  ghana: { plant: "emergent", scene: "rainforest", line: "Emergents above the West African forest.", added: 1 },
  kenya: { plant: "emergent", scene: "savanna", line: "Acacias on the savanna.", added: 1 },
  nigeria: { plant: "palm", scene: "rainforest", line: "Oil palms in the forest belt.", added: 1 },
  rwanda: { plant: "emergent", var: "shade", scene: "terraces", line: "Trees on the terraced hills.", added: 1 },
  serbia: { plant: "conifer", scene: "teak", line: "Spruce on the misted hills.", added: 1 },
  kazakhstan: { plant: "grass", scene: "steppe", line: "Feather grass on the Kazakh steppe.", added: 1 },
  uzbekistan: { plant: "conifer", var: "poplar", scene: "desert", line: "Poplars along an oasis canal.", added: 1 },
  laos: { plant: "rice", scene: "karst", line: "Sticky rice in the paddies below the limestone hills.", added: 1 },
};
const FALLBACK = { plant: "emergent", scene: "rainforest", line: "" };
const WORDS = {
  bamboo: ["CULMS", "LEAVES", "a shoot that has not broken ground"], palm: ["PALMS", "LEAFLETS", "a seedling"],
  rice: ["STALKS", "GRAINS", "a seedling just above the water"], lotus: ["STEMS", "PETALS", "a bud still under water"],
  banyan: ["PILLAR ROOTS", "LEAVES", "an aerial root that has not reached the ground"], mangrove: ["STEMS", "LEAVES", "a propagule in the mud"],
  conifer: ["TRUNKS", "NEEDLE TUFTS", "a seedling"], emergent: ["TRUNKS", "LEAVES", "a sapling"],
  grass: ["STALKS", "AWNS", "a tuft not yet in flower"],
};
const W = 1760, H = 990, GROUND = 720, TOP_MIN = 120;
let seed = 7;
const rnd = () => ((seed = (seed * 16807) % 2147483647) - 1) / 2147483646;
const el = (tag, attrs = {}, parent) => { const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); if (parent) parent.appendChild(e); return e; };
const mixc = (a, b, t) => `rgb(${a.map((v, i) => Math.round(v + (b[i] - v) * t)).join(",")})`;
const GOLD = "#d4a72c", GOLD2 = "#f1d58a", LEAF = "#5f9a80", GOLD_RGB = [212, 167, 44];
const lc = s => (s.l3 ? GOLD : LEAF), la = s => (s.l3 ? .92 : .75);
const share = f => f.strats.filter(s => s.l3).length / Math.max(1, f.strats.length);
function grad(defs, id, stops) {
  const g = el("linearGradient", { id, x1: 0, y1: 0, x2: 0, y2: 1 }, defs);
  stops.forEach(([o, c, a]) => el("stop", { offset: o, "stop-color": c, "stop-opacity": a ?? 1 }, g));
}
function leafPath(x, y, ang, L, wr = .16) {
  const w = L * wr, c = Math.cos(ang), s = Math.sin(ang), nx = -s, ny = c, tx = x + c * L, ty = y + s * L;
  return `M${x},${y} Q${x + c * L * .45 + nx * w},${y + s * L * .45 + ny * w} ${tx},${ty} Q${x + c * L * .45 - nx * w},${y + s * L * .45 - ny * w} ${x},${y}Z`;
}
function stemShape(g, pt, w, taper, fillc, steps = 24) {
  const L = [], R = [];
  for (let i = 0; i <= steps; i++) {
    const t = i / steps, [px, py] = pt(t), ww = w * (1 - taper * t) / 2;
    L.push(`${px - ww},${py}`); R.unshift(`${px + ww},${py}`);
  }
  el("path", { d: `M${L.join(" L")} L${R.join(" L")}Z`, fill: fillc }, g);
}
function nodes(g, f, pt, w, taper, t0 = 0, t1 = 1) {
  const ms = f.mechs.length ? f.mechs : [{ n: 0 }];
  ms.forEach((m, i) => {
    const t = t0 + (t1 - t0) * (i + 1) / (ms.length + 1), [px, py] = pt(t), ww = w * (1 - taper * t) / 2 + 1.5;
    if (m.n) {
      el("circle", { class: "mnode", "data-m": m.id, cx: px, cy: py, r: 6 + Math.sqrt(m.n) * 2.2, fill: "url(#glow)" }, g);
      el("line", { x1: px - ww - 1, y1: py, x2: px + ww + 1, y2: py, stroke: GOLD2, "stroke-width": 2.4 }, g);
    } else el("line", { x1: px - ww, y1: py, x2: px + ww, y2: py, stroke: "#06110d", "stroke-width": 1.4, opacity: .8 }, g);
  });
}
const bark = (f, base = [62, 122, 98], p = 1.3) => mixc(base, GOLD_RGB, share(f) ** p);
const quad = (a, c, b, t) => [(1 - t) ** 2 * a[0] + 2 * (1 - t) * t * c[0] + t * t * b[0], (1 - t) ** 2 * a[1] + 2 * (1 - t) * t * c[1] + t * t * b[1]];

// ---------------------------------------------------------------- landscapes
function forestBand(bg, y0, n, r, col, a) { for (let x = -40; x < W + 40; x += 18 + rnd() * 26) for (let j = 0; j < n; j++) el("circle", { cx: x + (rnd() - .5) * 60, cy: y0 - rnd() * 80, r: r * (.5 + rnd()), fill: col, opacity: a }, bg); }
function ridge(bg, base, peaks, fill, snow) {
  let d = `M-10,${base}`;
  for (let x = -10; x <= W + 10; x += 10) {
    let h = 0; peaks.forEach(([px, ph, pw]) => (h = Math.max(h, ph * Math.max(0, 1 - Math.abs(x - px) / pw) ** 1.2)));
    d += ` L${x},${base - h - rnd() * 6}`;
  }
  el("path", { d: d + ` L${W + 10},${base}Z`, fill }, bg);
  if (snow) el("path", { d: d + ` L${W + 10},${base}Z`, fill: "url(#snow)" }, bg);
}
function sea(bg, y) { el("rect", { x: 0, y, width: W, height: GROUND - y, fill: "url(#water)" }, bg); for (let i = 0; i < 180; i++) { const yy = y + 4 + rnd() ** 1.4 * (GROUND - y - 8), xx = rnd() * W; el("line", { x1: xx, y1: yy, x2: xx + 20 + rnd() * 90, y2: yy, stroke: "#cfe3d6", "stroke-opacity": .05 + rnd() * .12 }, bg); } }
function distantPalm(bg, x, y0, h, a) {
  el("line", { x1: x, y1: y0, x2: x + (rnd() - .5) * 20, y2: y0 - h, stroke: "#3e7a62", "stroke-width": 2.2, opacity: a }, bg);
  for (let k = 0; k < 9; k++) { const d = (k - 4) / 4; el("path", { d: `M${x},${y0 - h} q${d * 18},-12 ${d * 34},${6 + Math.abs(d) * 14}`, stroke: "#3e7a62", "stroke-width": 1.4, fill: "none", opacity: a }, bg); }
}
const SCENE = {
  mother(bg) { ridge(bg, GROUND, [[300, 120, 500], [900, 80, 600], [1500, 140, 500]], "#0b1d16"); el("rect", { x: 0, y: GROUND - 260, width: W, height: 230, fill: "url(#mist)" }, bg); },
  bamboo(bg) {
    [[0.10, 520, 1.2], [0.16, 430, 1.8], [0.22, 330, 2.4]].forEach(([a, top, w]) => {
      for (let x = -10; x < W + 10; x += 9 + rnd() * 16) { const h = GROUND - top - rnd() * 160, lean = (rnd() - .5) * 30; el("path", { d: `M${x},${GROUND} Q${x + lean * .3},${(GROUND + h) / 2} ${x + lean},${h}`, stroke: "#3e7a62", "stroke-width": w, fill: "none", opacity: a }, bg); }
      el("rect", { x: 0, y: GROUND - top - 60, width: W, height: 200, fill: "url(#mist)" }, bg);
    });
  },
  volcano(bg) {
    el("path", { d: `M300,${GROUND - 170} L760,250 Q800,228 840,250 L1360,${GROUND - 170}Z`, fill: "#0d211a", opacity: .9 }, bg);
    for (let i = 0; i < 14; i++) el("path", { d: `M${790 + rnd() * 20},236 q${(rnd() - .5) * 60},${-60 - rnd() * 40} ${(rnd() - .5) * 120},${-110 - rnd() * 40}`, stroke: "#cfe3d6", "stroke-opacity": .06, "stroke-width": 8 + rnd() * 10, fill: "none", "stroke-linecap": "round" }, bg);
    for (let k = 0; k < 3; k++) { forestBand(bg, GROUND - 120 + k * 50, 24, 9, "#3e7a62", .05 + .04 * k); el("rect", { x: 0, y: GROUND - 300 + k * 50, width: W, height: 220, fill: "url(#mist)" }, bg); }
  },
  rainforest(bg) { for (let k = 0; k < 4; k++) { forestBand(bg, GROUND - 260 + k * 70, 10, 12, "#3e7a62", .05 + .03 * k); } el("rect", { x: 0, y: GROUND - 420, width: W, height: 260, fill: "url(#mist)" }, bg); },
  teak(bg) { ridge(bg, GROUND, [[200, 260, 500], [800, 200, 600], [1400, 280, 520]], "#0c1f18"); el("rect", { x: 0, y: GROUND - 330, width: W, height: 220, fill: "url(#mist)" }, bg); ridge(bg, GROUND, [[500, 130, 600], [1200, 150, 600]], "#0e231b"); el("rect", { x: 0, y: GROUND - 200, width: W, height: 200, fill: "url(#mist)" }, bg); },
  paddy(bg) { for (let x = 30; x < W; x += 140 + rnd() * 160) distantPalm(bg, x, GROUND - 70, 140 + rnd() * 70, .4); el("rect", { x: 0, y: GROUND - 74, width: W, height: 4, fill: "#3e7a62", opacity: .4 }, bg); el("rect", { x: 0, y: GROUND - 300, width: W, height: 260, fill: "url(#mist)" }, bg); },
  terraces(bg) {
    ridge(bg, GROUND, [[400, 420, 700], [1300, 380, 700]], "#0c1f18");
    for (let k = 0; k < 18; k++) { const y = GROUND - 30 - k * 22; el("path", { d: `M0,${y} C400,${y - 30 + rnd() * 20} 900,${y + 20} 1300,${y - 20} S1700,${y} ${W},${y - 10}`, stroke: "#8db8a0", "stroke-opacity": .14, fill: "none" }, bg); }
    el("rect", { x: 0, y: GROUND - 300, width: W, height: 220, fill: "url(#mist)" }, bg);
  },
  karst(bg) {
    [[80, 330, 110], [260, 220, 140], [470, 380, 90], [640, 260, 130], [900, 340, 100], [1080, 200, 150], [1300, 300, 120], [1480, 240, 140], [1680, 360, 110]].forEach(([x, top, w], i) =>
      el("path", { d: `M${x - w},${GROUND - 60} C${x - w * .9},${top + 80} ${x - w * .6},${top} ${x},${top} C${x + w * .55},${top} ${x + w * .85},${top + 90} ${x + w},${GROUND - 60}Z`, fill: i % 2 ? "#0c1f19" : "#0f2620" }, bg));
    el("rect", { x: 0, y: GROUND - 260, width: W, height: 230, fill: "url(#mist)" }, bg);
  },
  karstwater(bg) { SCENE.karst(bg); },
  delta(bg) { for (let x = -20; x < W + 20; x += 30 + rnd() * 30) { const h = 40 + rnd() * 40; el("ellipse", { cx: x, cy: GROUND - 60 - h * .6, rx: 30 + rnd() * 20, ry: h * .5, fill: "#3e7a62", opacity: .14 }, bg); } el("rect", { x: 0, y: GROUND - 240, width: W, height: 220, fill: "url(#mist)" }, bg); },
  himalaya(bg) {
    ridge(bg, GROUND - 120, [[100, 420, 380], [520, 560, 420], [980, 480, 400], [1420, 600, 420], [1760, 440, 380]], "#0d1d1e", true);
    el("rect", { x: 0, y: GROUND - 380, width: W, height: 260, fill: "url(#mist)" }, bg);
    ridge(bg, GROUND, [[300, 220, 500], [1100, 260, 600], [1700, 200, 400]], "#0a1914");
    for (let x = 0; x < W; x += 14 + rnd() * 20) { const y = GROUND - 30 - rnd() * 120, h = 30 + rnd() * 30; el("path", { d: `M${x},${y} l-8,${h} l16,0Z`, fill: "#3e7a62", opacity: .14 }, bg); }
  },
  steppe(bg) { for (let k = 0; k < 3; k++) { const y = GROUND - 220 + k * 70; el("path", { d: `M0,${y} C500,${y - 50} 1100,${y + 30} ${W},${y - 30} L${W},${GROUND} L0,${GROUND}Z`, fill: ["#0c1a13", "#0e1f15", "#102317"][k] }, bg); } for (let i = 0; i < 90; i++) { const y = 140 + rnd() * 340, x = rnd() * W; el("path", { d: `M${x},${y} q${120 + rnd() * 200},${(rnd() - .5) * 30} ${300 + rnd() * 500},${(rnd() - .5) * 20}`, stroke: "#cfe3d6", "stroke-opacity": .04 + rnd() * .06, fill: "none" }, bg); } },
  desert(bg) { ridge(bg, GROUND - 60, [[200, 300, 420], [700, 240, 380], [1250, 340, 450], [1700, 260, 400]], "#16190f"); el("rect", { x: 0, y: GROUND - 300, width: W, height: 240, fill: "url(#mist)" }, bg); for (let k = 0; k < 2; k++) { const y = GROUND - 30 + k * 10; el("path", { d: `M0,${y} C400,${y - 40} 800,${y + 10} 1200,${y - 30} S1600,${y - 10} ${W},${y - 20} L${W},${GROUND} L0,${GROUND}Z`, fill: k ? "#1a1c11" : "#141710" }, bg); } },
  savanna(bg) { ridge(bg, GROUND, [[300, 200, 600], [1100, 240, 650], [1700, 180, 500]], "#131a10"); for (let x = 20; x < W; x += 60 + rnd() * 120) { const y = GROUND - 30 - rnd() * 80; el("line", { x1: x, y1: y, x2: x, y2: y - 30, stroke: "#3e7a62", opacity: .3 }, bg); el("ellipse", { cx: x, cy: y - 38, rx: 18, ry: 10, fill: "#3e7a62", opacity: .2 }, bg); } el("rect", { x: 0, y: GROUND - 260, width: W, height: 220, fill: "url(#mist)" }, bg); },
  atoll(bg) { sea(bg, GROUND - 160); el("rect", { x: 0, y: GROUND - 40, width: W, height: 40, fill: "#1a2a22" }, bg); for (let x = 20; x < W; x += 70 + rnd() * 120) distantPalm(bg, x, GROUND - 40, 70 + rnd() * 50, .35); },
  island(bg) { sea(bg, GROUND - 160); el("path", { d: `M250,${GROUND - 160} C500,${GROUND - 460} 900,${GROUND - 520} 1150,${GROUND - 330} S1500,${GROUND - 200} 1650,${GROUND - 160}Z`, fill: "#0c1f18" }, bg); forestBand(bg, GROUND - 200, 12, 9, "#3e7a62", .08); el("rect", { x: 0, y: GROUND - 60, width: W, height: 60, fill: "#1a2a22" }, bg); },
  banyan(bg) {
    for (let i = 0; i < 2600; i++) { const x = rnd() * W, y = 110 + Math.abs((rnd() + rnd() + rnd()) / 3 - .5) * 400 + Math.sin(x / 140) * 18; el("ellipse", { cx: x, cy: y, rx: 6 + rnd() * 8, ry: 3 + rnd() * 4, fill: "#3e7a62", opacity: .12 + rnd() * .16, transform: `rotate(${rnd() * 180} ${x} ${y})` }, bg); }
    el("path", { d: `M-20,236 C400,200 900,262 1300,222 S1700,214 1790,236`, stroke: "#3e7a62", "stroke-width": 22, fill: "none", opacity: .9 }, bg);
  },
};
const WATER = { paddy: 1, karst: 1, karstwater: 1, delta: 1 };

// ---------------------------------------------------------------- plants
const PLANT = {
  bamboo(g, o, f, n, hgt, w, pt) {
    const col = bark(f); stemShape(g, pt, w, .55, col); nodes(g, f, pt, w, .55);
    f.strats.forEach((s, i) => {
      const [px, py] = pt(Math.min(1, .55 + .45 * ((i * .618) % 1) ** .7)), side = i % 2 ? 1 : -1;
      const ang = side > 0 ? -.35 + rnd() * .9 : Math.PI + .35 - rnd() * .9, bl = 6 + rnd() * 14, bx = px + side * bl, by = py - bl * .35;
      el("line", { x1: px, y1: py, x2: bx, y2: by, stroke: col, "stroke-width": 1, opacity: .7 }, g);
      el("path", { d: leafPath(bx, by, ang + (rnd() - .5) * .4, 24 + rnd() * 16), fill: lc(s), opacity: la(s) }, g);
    });
  },
  palm(g, o, f, n, hgt, w, pt, v) {
    const fern = v === "fern", col = bark(f, fern ? [80, 96, 74] : [70, 104, 88]);
    stemShape(g, pt, w * (fern ? .9 : 1.25), fern ? .1 : .3, col); nodes(g, f, pt, w * 1.1, .3, 0, .92);
    if (v === "date") for (let i = 0; i < 10; i++) { const [px, py] = pt(.1 + i * .08); el("line", { x1: px - w * .7, y1: py, x2: px + w * .7, y2: py - 4, stroke: "#06110d", opacity: .5 }, g); }
    const [tx, ty] = pt(1), k = Math.max(fern ? 5 : 3, Math.ceil(n / (fern ? 3 : 4)));
    let i = 0;
    for (let j = 0; j < k; j++) {
      const d = k === 1 ? 0 : (j / (k - 1)) * 2 - 1, L = (fern ? 40 : 46) + rnd() * 26;
      const a = [tx, ty], b = [tx + d * L * 1.15, ty + L * ((fern ? .75 : .55) * Math.abs(d) - .2)], c = [tx + d * L * .55, ty - L * (v === "sugar" ? .25 : .45)];
      el("path", { d: `M${a} Q${c} ${b}`, stroke: col, "stroke-width": 2.6, fill: "none" }, g);
      if (fern) el("path", { d: `M${b[0]},${b[1]} a4,4 0 1 1 ${d * 6},4`, stroke: col, fill: "none" }, g);
      const per = Math.ceil((n - i) / (k - j));
      for (let q = 0; q < per && i < n; q++, i++) {
        const [px, py] = quad(a, c, b, (q + 1) / (per + 1)), s = f.strats[i], side = q % 2 ? 1 : -1;
        el("path", { d: leafPath(px, py, Math.PI / 2 + side * (fern ? .9 : .5) - d * .5, (fern ? 13 : 22) + rnd() * 7, fern ? .25 : .2), fill: lc(s), opacity: la(s) }, g);
      }
    }
  },
  rice(g, o, f, n, hgt, w, pt) {
    const col = bark(f, [86, 140, 108], 1.2), ww = Math.max(2.5, w * .6);
    stemShape(g, pt, ww, .4, col); nodes(g, f, pt, ww, .4, 0, .8);
    for (let k = 0; k < 3; k++) { const [px, py] = pt(.15 + k * .12), side = k % 2 ? 1 : -1; el("path", { d: leafPath(px, py, -Math.PI / 2 + side * (.5 + rnd() * .3), 60 + rnd() * 50, .05), fill: "#3e7a62", opacity: .7 }, g); }
    const [tx, ty] = pt(1), side = Math.round(o.x) % 2 ? 1 : -1, L = 30 + Math.sqrt(n) * 14, a = [tx, ty], b = [tx + side * L * .8, ty + L * .7], c = [tx + side * L * .55, ty - L * .25];
    el("path", { d: `M${a} Q${c} ${b}`, stroke: col, "stroke-width": 1.4, fill: "none" }, g);
    f.strats.forEach((s, i) => { const [px, py] = quad(a, c, b, (i + 1) / (n + 1)), sd = i % 2 ? 1 : -1; el("ellipse", { cx: px + sd * 4, cy: py + 2, rx: 5, ry: 2.6, fill: lc(s), opacity: la(s), transform: `rotate(${60 * sd + side * 30} ${px + sd * 4} ${py + 2})` }, g); });
  },
  grass(g, o, f, n, hgt, w, pt) {
    const col = bark(f, [110, 130, 96], 1.2);
    stemShape(g, pt, Math.max(2, w * .45), .5, col); nodes(g, f, pt, Math.max(2, w * .45), .5, 0, .7);
    f.strats.forEach((s, i) => {  // a plume of awns streaming downwind
      const [px, py] = pt(.7 + .3 * (i + 1) / (n + 1)), L = 30 + rnd() * 40;
      el("path", { d: `M${px},${py} q${L * .5},${-6 + rnd() * 6} ${L},${4 + rnd() * 12}`, stroke: lc(s), "stroke-width": 1.3, fill: "none", opacity: la(s) }, g);
    });
  },
  lotus(g, o, f, n, hgt, w, pt) {
    const col = bark(f, [70, 120, 96]), ww = Math.max(2.5, w * .55);
    stemShape(g, pt, ww, .2, col); nodes(g, f, pt, ww, .2, 0, .85);
    const pad = 18 + Math.sqrt(n) * 4, [bx] = pt(0);
    el("ellipse", { cx: bx + (rnd() - .5) * 30, cy: GROUND + 4, rx: pad, ry: pad * .28, fill: "#2e5e4b", opacity: .85 }, g);
    const [tx, ty] = pt(1), R = 10 + Math.sqrt(n) * 3.4;
    f.strats.forEach((s, i) => { const ring = i % 3, a = -Math.PI / 2 + (((i * .618) % 1) - .5) * (2.2 + ring * .5); el("path", { d: leafPath(tx, ty + 4, a, R * (1 - ring * .18), .32), fill: lc(s), opacity: la(s) * (1 - ring * .12) }, g); });
    el("circle", { cx: tx, cy: ty + 2, r: 3.4, fill: GOLD2 }, g);
  },
  banyan(g, o, f, n, hgt, w, pt) {
    stemShape(g, pt, w, -.1, bark(f, [70, 110, 90])); nodes(g, f, pt, w, -.1);
    const [tx, ty] = pt(1);
    f.strats.forEach(s => { const a = rnd() * Math.PI * 2, r = Math.sqrt(rnd()) * (14 + Math.sqrt(n) * 5); el("path", { d: leafPath(tx + Math.cos(a) * r, ty - 18 + Math.sin(a) * r * .6, rnd() * Math.PI * 2, 16 + rnd() * 6, .32), fill: lc(s), opacity: la(s) }, g); });
  },
  mangrove(g, o, f, n, hgt, w, pt) {
    const col = bark(f, [70, 110, 90]);
    stemShape(g, pt, w, .4, col); nodes(g, f, pt, w, .4, .15, .85);
    const [bx, by] = pt(.18);
    for (let k = 0; k < 4 + Math.round(Math.sqrt(n)); k++) {  // prop roots arching into the water
      const side = k % 2 ? 1 : -1, sp = 10 + rnd() * (14 + w * 2), yy = by + rnd() * 30;
      el("path", { d: `M${bx},${yy} q${side * sp * .6},${-14} ${side * sp},${GROUND - yy}`, stroke: col, "stroke-width": 1.4, fill: "none", opacity: .85 }, g);
    }
    const [tx, ty] = pt(1), R = 22 + Math.sqrt(n) * 7;
    f.strats.forEach(s => { const a = Math.PI + rnd() * Math.PI, r = Math.sqrt(rnd()) * R; el("path", { d: leafPath(tx + Math.cos(a) * r * 1.3, ty + 6 + Math.sin(a) * r * .7, rnd() * 6.3, 16 + rnd() * 6, .38), fill: lc(s), opacity: la(s) }, g); });
  },
  conifer(g, o, f, n, hgt, w, pt, v) {
    const col = bark(f, [70, 100, 84]);
    stemShape(g, pt, w, .7, col); nodes(g, f, pt, w, .7, 0, .9);
    const narrow = v === "cypress" || v === "poplar", spread = narrow ? 14 + Math.sqrt(n) * 3 : 26 + Math.sqrt(n) * 7;
    f.strats.forEach((s, i) => {  // tufts on tiers that shorten towards the top
      const t = .3 + .7 * ((i * .618) % 1), [px, py] = pt(t), side = i % 2 ? 1 : -1, L = spread * (1.1 - t) * (.6 + rnd() * .5);
      const ex = px + side * L, ey = py + (narrow ? -L * .4 : L * .25);
      el("line", { x1: px, y1: py, x2: ex, y2: ey, stroke: col, "stroke-width": .9, opacity: .7 }, g);
      if (v === "poplar") el("path", { d: leafPath(ex, ey, -Math.PI / 2 + side * .3, 9 + rnd() * 4, .45), fill: lc(s), opacity: la(s) }, g);
      else for (let k = -1; k <= 1; k++) el("line", { x1: ex, y1: ey, x2: ex + side * 10 * Math.cos(k * .6), y2: ey - 10 * Math.sin(k * .6) + 2, stroke: lc(s), "stroke-width": 1.8, opacity: la(s) }, g);
    });
  },
  emergent(g, o, f, n, hgt, w, pt, v) {
    const col = bark(f, v === "eucalypt" ? [120, 130, 110] : [70, 104, 88]);
    stemShape(g, pt, w * 1.1, .35, col); nodes(g, f, pt, w * 1.1, .35, 0, .9);
    const [tx, ty] = pt(1), R = (v === "teak" ? 22 : 18) + Math.sqrt(n) * (v === "eucalypt" ? 6 : 8);
    for (let k = 0; k < 3; k++) { const side = k - 1; el("line", { x1: tx, y1: ty + 6, x2: tx + side * R * .7, y2: ty - R * .35, stroke: col, "stroke-width": 1.3 }, g); }
    f.strats.forEach(s => {  // a cauliflower crown: each leaf one strategy
      const a = Math.PI + rnd() * Math.PI, r = Math.sqrt(rnd()) * R, x = tx + Math.cos(a) * r * 1.35, y = ty - R * .2 + Math.sin(a) * r * .75;
      if (v === "teak") el("ellipse", { cx: x, cy: y, rx: 8, ry: 6, fill: lc(s), opacity: la(s) }, g);
      else el("path", { d: leafPath(x, y, v === "eucalypt" ? Math.PI / 2 + (rnd() - .5) * .6 : rnd() * 6.3, v === "eucalypt" ? 18 : 15, v === "eucalypt" ? .14 : .34), fill: lc(s), opacity: la(s) }, g);
    });
  },
};

// ---------------------------------------------------------------- one tab

// ---------------------------------------------------------------- one country
// rows: the strategies in view, as the page holds them (r[4] family, r[5] lever). D: the tree data. pick(o): what a
// click on a stem or a gold node opens in the page's panel ({ f } or { v }).
function draw(svg, slug, name, rows, D, pick) {
  const cfg = C[slug] || FALLBACK, isB = cfg.plant === "banyan";
  seed = 7;
  svg.innerHTML = "";
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  const live = D.families.filter(f => f.lever_ids.length);
  const byF = {};
  rows.forEach(r => { if (r[4]) (byF[r[4]] ||= []).push(r); });
  // one leaf per strategy, or per k strategies when the plans in view hold more than the canvas can carry
  const tot = live.reduce((a, f) => a + (byF[f.family_id] || []).length, 0), per = Math.max(1, Math.ceil(tot / 2400));
  const fams = live.map(f => {
    const rs = byF[f.family_id] || [], used = {};
    rs.forEach(r => r[5] && (used[r[5]] = (used[r[5]] || 0) + 1));
    const strats = [];
    for (let i = 0; i < rs.length; i += per) { const b = rs.slice(i, i + per); strats.push({ l3: b.filter(r => r[5]).length * 2 >= b.length }); }
    return { id: f.family_id, name: f.family, sub: f.subpillar_code, n: rs.length, nl: rs.filter(r => r[5]).length, strats,
             mechs: f.lever_ids.map(id => ({ id, n: used[id] || 0 })) };
  });
  const famBySub = {};
  fams.forEach(f => (famBySub[f.sub] ||= []).push(f));
  const scale = Math.max(1, ...fams.map(f => f.strats.length));
  svg.setAttribute("aria-label", `${name}: ${cfg.line} One stem per family, ${tot.toLocaleString("en-GB")} strategies in view.`);

  const defs = el("defs", {}, svg);
  grad(defs, "f-sky", [[0, "#06110d"], [1, "#0c2219"]]);
  grad(defs, "mist", [[0, "#10241c", 0], [.5, "#10241c", .5], [1, "#10241c", 0]]);
  grad(defs, "water", [[0, "#0d2a2c"], [1, "#06141a"]]);
  grad(defs, "snow", [[0, "#cfe3d6", .5], [.35, "#cfe3d6", 0]]);
  const glow = el("radialGradient", { id: "glow" }, defs);
  el("stop", { offset: 0, "stop-color": GOLD, "stop-opacity": .55 }, glow); el("stop", { offset: 1, "stop-color": GOLD, "stop-opacity": 0 }, glow);
  el("rect", { x: 0, y: 0, width: W, height: GROUND, fill: "url(#f-sky)" }, svg);
  SCENE[cfg.scene](el("g", { "aria-hidden": "true" }, svg));

  const slots = [], clumpX = {}, standX = {};
  let x = 70;
  ORDER.forEach((p, pi) => {
    if (pi) x += 78;
    const sx0 = x;
    D.subpillars.filter(s => s.pillar === p && famBySub[s.code]).forEach((s, si) => {
      if (si) x += 26;
      // inside a clump the stems stand in their framework families (the groups of Jude's layer), a small gap between
      const cx0 = x, mine = new Set(famBySub[s.code].map(f => f.id)), FB = Object.fromEntries(famBySub[s.code].map(f => [f.id, f]));
      D.groups.filter(g => g.subpillar_code === s.code && g.family_ids.some(id => mine.has(id))).forEach((g, gi) => {
        if (gi) x += 7;
        g.family_ids.filter(id => mine.has(id)).forEach(id => { slots.push({ f: FB[id], x: x + 12.5, p, s, g }); x += 25; });
      });
      clumpX[s.code] = [cx0, x];
    });
    standX[p] = [sx0, x];
  });
  const sc = (W - 70) / x;
  slots.forEach(o => (o.x *= sc));
  for (const k in clumpX) clumpX[k] = clumpX[k].map(v => v * sc);
  for (const k in standX) standX[k] = standX[k].map(v => v * sc);

  const ground = el("g", {}, svg);
  el("rect", { x: 0, y: GROUND, width: W, height: H - GROUND, fill: WATER[cfg.scene] ? "url(#water)" : cfg.scene === "atoll" || cfg.scene === "island" ? "#14221b" : "#081510" }, ground);
  if (WATER[cfg.scene]) for (let i = 0; i < 260; i++) { const yy = GROUND + 4 + rnd() ** 1.5 * 150, xx = rnd() * W; el("line", { x1: xx, y1: yy, x2: xx + 20 + rnd() * 80, y2: yy, stroke: "#cfe3d6", "stroke-opacity": .05 + rnd() * .12 }, ground); }
  el("line", { x1: 0, y1: GROUND, x2: W, y2: GROUND, stroke: "#8db8a0", "stroke-opacity": .35 }, ground);
  const RZ = GROUND + 44;
  el("path", { d: `M${standX.SMG[0] - 20},${RZ} L${standX.MCH[1] + 20},${RZ}`, stroke: "#3e7a62", "stroke-width": 5, fill: "none", "stroke-linecap": "round" }, ground);
  D.subpillars.filter(s => clumpX[s.code]).forEach(s => {
    const [a, b] = clumpX[s.code], mid = (a + b) / 2;
    slots.filter(o => o.s.code === s.code).forEach(o => el("path", { d: `M${o.x},${GROUND} L${o.x},${RZ - 16} Q${o.x},${RZ - 4} ${mid},${RZ}`, stroke: "#8db8a0", "stroke-opacity": .5, "stroke-width": 1.2, fill: "none" }, ground));
    el("circle", { cx: mid, cy: RZ, r: 6, fill: "#06110d", stroke: "#cfe3d6", "stroke-width": 1.4 }, ground);
    const t = el("text", { x: mid, y: RZ + 34, "text-anchor": "middle", fill: "#cfe3d6", "font-family": "Jura, sans-serif", "font-size": 12.5 }, ground);
    let line = "", out = [];
    s.name.replace("Reform Leadership, Coalitions and Civic Engagement", "Reform Leadership and Coalitions").split(" ")
      .forEach(wd => { if ((line + " " + wd).trim().length > Math.max(12, (b - a) / 7.2)) { out.push(line.trim()); line = ""; } line += " " + wd; });
    out.push(line.trim());
    out.forEach((r, k) => (el("tspan", { x: mid, dy: k ? 15 : 0 }, t).textContent = r));
  });
  ORDER.forEach(p => {
    const [a, b] = standX[p], mid = (a + b) / 2, yb = H - 92;
    el("path", { d: `M${a + 2},${yb - 10} L${a + 2},${yb} L${b - 2},${yb} L${b - 2},${yb - 10}`, stroke: GOLD, "stroke-opacity": .7, "stroke-width": 1.4, "stroke-dasharray": "2 5", fill: "none" }, ground);
    el("text", { x: mid, y: H - 40, "text-anchor": "middle", fill: GOLD, "font-family": "Italiana, Didot, Georgia, serif", "font-size": 40, "letter-spacing": 12 }, ground).textContent = STAND[p];
  });

  const forest = el("g", {}, svg);
  slots.forEach(o => {
    const f = o.f, n = f.strats.length;
    const g = el("g", { class: "culm", tabindex: 0, role: "button", "aria-label": `${f.name}: ${f.n} strategies, ${f.nl} on a lever` }, forest);
    el("title", {}, g).textContent = `${f.name} (${o.g.group})\n${f.n.toLocaleString("en-GB")} strategies · ${f.nl.toLocaleString("en-GB")} on a lever · ${f.mechs.filter(m => m.n).length} of ${f.mechs.length} levers reached`;
    g.addEventListener("click", e => { const m = e.target.closest(".mnode"); pick(m ? { v: m.dataset.m } : { f: f.id }); });
    g.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); pick({ f: f.id }); } });
    if (!n) {
      if (isB) { el("path", { d: `M${o.x},236 q${(rnd() - .5) * 10},60 0,${90 + rnd() * 50}`, stroke: "#cfe3d6", "stroke-opacity": .5, "stroke-dasharray": "2 3", fill: "none" }, g); el("rect", { x: o.x - 11, y: 230, width: 22, height: 160, fill: "transparent" }, g); }
      else { el("path", { d: `M${o.x - 6},${GROUND} L${o.x},${GROUND - 26} L${o.x + 6},${GROUND}Z`, fill: "none", stroke: "#cfe3d6", "stroke-opacity": .55, "stroke-dasharray": "2 3" }, g); el("rect", { x: o.x - 11, y: GROUND - 34, width: 22, height: 34, fill: "transparent" }, g); }
      return;
    }
    const r = Math.sqrt(n / scale);
    let hgt = 150 + (GROUND - TOP_MIN - 150) * r, w = 3.5 + 7 * r;
    if (cfg.plant === "rice" || cfg.plant === "grass") hgt *= .8;
    if (isB) { hgt = GROUND - 236; w = 3 + 12 * r; }
    const lean = isB ? 0 : cfg.scene === "steppe" ? .08 : (rnd() - .5) * .10 + (o.p === "SMG" ? -.03 : o.p === "MCH" ? .03 : 0);
    const pt = t => [o.x + lean * hgt * t + Math.sin(t * 2.2) * 40 * lean, GROUND - hgt * t];
    const hit = el("rect", { fill: "transparent" }, g);
    PLANT[cfg.plant](g, o, f, n, hgt, w, pt, cfg.var);
    const [tx, ty] = pt(1);
    Object.entries({ x: Math.min(o.x, tx) - 16, y: isB ? 150 : ty - 30, width: Math.abs(tx - o.x) + 32, height: GROUND - (isB ? 150 : ty - 30) }).forEach(([k, v]) => hit.setAttribute(k, v));
  });
  const [stemW, leafW, emptyW] = WORDS[cfg.plant];
  return {
    line: cfg.line, added: !!cfg.added, per,
    key: [
      ["STANDS", "economy left, people centre, governance right"],
      ["CLUMPS", "the ten named subpillars, joined underground; inside each, the stems stand in their framework families"],
      [stemW, `one per live family (${live.length}); ${isB ? "thickness" : "height"} grows with the strategies on it`],
      ["NODES", "one per lever of the family; gold where a strategy in view sits on it"],
      [leafW, per > 1 ? `one per ${per} strategies; gold where most of them are on a lever` : "one per strategy; gold on a lever, green on the family only"],
      ["EMPTY", `${emptyW}: a family no strategy in view reaches`],
    ],
  };
}
return { draw, has: slug => slug in C };
})();
