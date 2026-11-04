"""Write the reviewers' workbook of tree v4: python3 tree_xlsx.py [out.xlsx]"""
import json, os, re, sys, collections
HERE = os.path.dirname(os.path.abspath(__file__))
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

d = json.load(open(os.path.join(HERE, 'tree_v4.json'), encoding='utf-8'))
G, F, L, P = d['groups'], d['families'], d['levers'], d['pathways']
gby = {g['group_id']: g for g in G}
fby = {f['family_id']: f for f in F}
lby = {l['lever_id']: l for l in L}
forder = {f['family_id']: i for i, f in enumerate(F)}
pby = {p['pathway_id']: p for p in P}
MERGED = d['meta'].get('merged_pathways', {})
cw = json.load(open(os.path.join(HERE, 'inputs', 'reviewer_crosswalk.json'), encoding='utf-8'))
GRADES = ['unbacked', 'thin', 'backed', 'well backed']

def j(v):
    if v is None: return ''
    if isinstance(v, list): return '; '.join(str(x) for x in v)
    return v

HFILL = PatternFill('solid', fgColor='DCE6F1')
BAND = PatternFill('solid', fgColor='F3F6FA')
TOP = Border(top=Side(style='thin', color='808080'))

def sheet(wb, title, headers, rows, kinds, freeze, band_key=None):
    ws = wb.create_sheet(title)
    ws.append(headers)
    for c in ws[1]:
        c.font = Font(bold=True); c.fill = HFILL
        c.alignment = Alignment(wrap_text=True, vertical='top')
    width = {'id': 9, 'name': 36, 'long': 55, 'short': 16, 'num': 11}
    for i, k in enumerate(kinds, 1):
        ws.column_dimensions[get_column_letter(i)].width = width[k]
    prev, banded = None, False
    for r in rows:
        ws.append([j(v) for v in r])
        rn = ws.max_row
        key = r[band_key] if band_key is not None else None
        newblock = band_key is not None and key != prev
        if newblock and prev is not None: banded = not banded
        for i, k in enumerate(kinds, 1):
            c = ws.cell(rn, i)
            c.alignment = Alignment(wrap_text=k in ('name', 'long'), vertical='top')
            if band_key is not None:
                if newblock and prev is not None: c.border = TOP
                if banded: c.fill = BAND
        prev = key
    ws.freeze_panes = freeze
    ws.auto_filter.ref = ws.dimensions
    return ws

wb = Workbook()
rm = wb.active; rm.title = 'Read me'
lines = [
 ('PV II mother tree v4: levers (draft for review, 3 November 2026)', 'title'),
 ('', None),
 ('The tree has four levels under the RHDR pillars and subpillars: group (L1) > family (L2) > lever (L3) > pathway (L4).', None),
 ('A lever is what a government does that moves its family\'s purpose, in a plan\'s own grain. The lever is where a plan\'s strategy is placed.', None),
 ('The pathways under a lever are the literature behind it (causal input, transmission, outcome, conditions, citations). They are an optional depth, not the placement level.', None),
 ('Each lever has two tests, "joins when" and "joins not". They are prose and are judged by meaning, not by keywords. Some tests refer to sibling pathways by their L3-nnn id (shown in the pathway_id column).', None),
 ('Lever short names were cut automatically from the bridge phrase (the full phrase is in "lever full phrase"). Some read as cut off: please rename them.', None),
 ('Mechanism citations (on the pathway rows) are as cited by the earlier reviewer draft and are mostly not independently verified; the evidence_status column says which.', None),
 ('Intervention evidence (on the lever rows, scan of 3 November 2026 in two passes): a systematic review or flagship evaluation of the action itself, with a finding written from the text that was read, a strength rating (strong, mixed, thin, none found), the study design, how directly the source fits the lever (direct, partial, loose), the basis (what in the text supports the finding) and how much of the source was read (abstract or full text). Please challenge the source, the fit and the rating.', None),
 ('Framework columns (on the lever rows, read 3 November 2026 from the full texts): what the framework document behind the group (Inclusion Matters, the Human Development Reports 1990 and 1994, Changing Wealth of Nations with the IPCC AR6 summaries and the ILO just-transition guidelines, the Growth Report and WDR 2020, WDR 2009, WDR 2008 with Finance for All? and Inclusive Growth Analytics, WDR 2017 with WDR 2004, Fox 2015 and DLP 2018) says about the action, on which printed page, and the references it cites for it, checked against its own reference list. Where the document does not discuss the action, "framework says" says so. The governance groups (anticipation, adaptation, agility) have no framework document yet: the Future-Ready Governance Index is still in development.', None),
 ('Thesis literature (on the lever rows): papers from the economics literature library (firm dynamics, misallocation, entrepreneurship, mobility, microenterprise; mostly RCTs and natural experiments) whose intervention or setting matches the lever, with the identification design and a one-line finding. Only 24 levers have a match; the library is about firms and workers, not about most of the tree.', None),
 ('Ids: levers are LV-001 to LV-229. Pathways keep their earlier ids (L3-001 to L3-266) so earlier outputs still join; in v4 they sit one level below the lever (L4). The "joins not" tests point to sibling pathways by those L3 ids.', None),
 ('What we ask of reviewers:', 'bold'),
 ('  1. Check each lever\'s name and its joins when / joins not tests.', None),
 ('  2. Say if a lever is missing under a family, or if two levers are really one.', None),
 ('  3. Check each pathway\'s causal input, transmission and outcome, and its citation.', None),
 ('  4. Write comments in the "Reviewer comment" column (last column of every sheet).', None),
 ('', None),
 ('Sheets', 'bold'),
 ('Tree: one row per pathway (263), grouped by group, family and lever; a grey line and shading mark each new lever block.', None),
 ('Levers: one row per lever (229), the placement level, with its tests, pathways, evidence, risks, text cues and Thai entry points.', None),
 ('Codebook: one row per lever (229) in tree order, in the structure the independent reviewer used: definition, framework anchor, causal mechanism and scope conditions (from the pathways), include and exclude tests, competing levers, plan-language examples, intervention evidence, thesis papers, theory anchors, framework references, Thai strategies on the lever, threats to validity and backing grade. The observable indicators column is empty: reviewers write the indicators.', None),
 ('Backing: one row per lever (229), the gaps first (unbacked, thin, backed, well backed), with the four sources behind the grade. Score: framework discussed 2, weak 1, not discussed or no document 0; evidence strong 3, mixed 2, thin 1, none found 0; fit partial -0.5, loose -1; at least one thesis paper +1. Grade: 4.5 or more well backed, 3 or more backed, 1.5 or more thin, below 1.5 unbacked. Thai strategies are shown for information and do not count.', None),
 ('Backing summary: levers by backing grade, for each subpillar and in all.', None),
 ('Theory anchors: the independent reviewer\'s 27 references (review of 4 November 2026), with the families that carry each one and the reviewer levers it was linked to. A family carries a reference as core or complementary when the reviewer linked it to a lever that maps onto the family, and as secondary when the family is only a secondary match; the family\'s levers inherit its anchors.', None),
 ('Reviewer crosswalk: the independent reviewer\'s 18 levers mapped onto our subpillars, groups and families, with a note on where the cut differs.', None),
 ('Families: one row per family (60), with definition, examples, plan words and its lever ids.', None),
 ('Groups: one row per group (33), with the published framework it draws on (basis) and its definition.', None),
]
for t, s in lines:
    rm.append([t]); c = rm.cell(rm.max_row, 1)
    if s == 'title': c.font = Font(bold=True, size=14)
    elif s == 'bold': c.font = Font(bold=True)
rm.column_dimensions['A'].width = 150

# Tree
th = ['pillar','subpillar','group_id','group','group framework','family_id','family','family definition','lever_id','lever','lever full phrase','joins when','joins not','intervention evidence','evidence finding','evidence strength','design','fit to lever','basis','framework says','framework references','thesis literature','pathway_id','pathway','causal input','transmission','outcome','conditions','distinction','evidence (citations)','evidence_status','risks','Reviewer comment']
tk = ['name','name','id','name','long','id','name','long','id','name','long','long','long','long','long','name','name','name','long','long','long','long','id','name','long','long','long','long','long','long','name','name','long']
Ps = sorted(P, key=lambda p: (forder[p['family_id']], p['lever_id'], p['pathway_id']))
trows = []
for p in Ps:
    l, f, g = lby[p['lever_id']], fby[p['family_id']], gby[p['group_id']]
    trows.append([p['pillar'], p['subpillar'], g['group_id'], g['group'], g.get('basis',''), f['family_id'], f['family'], f.get('definition',''),
                  l['lever_id'], l['lever'], l['lever_full'], l['joins_when'], l['joins_not'],
                  l.get('intervention_evidence',''), l.get('evidence_finding',''), l.get('evidence_strength',''), l.get('evidence_design',''), l.get('evidence_fit',''), l.get('evidence_basis',''), l.get('framework_says',''), '; '.join(l.get('framework_refs') or []), l.get('thesis_citations',''), p['pathway_id'], p['pathway'],
                  p['causal_input'], p['transmission'], p['outcome'], p['conditions'], p['distinction'], p['evidence'], p['evidence_status'], p['risks'], ''])
sheet(wb, 'Tree', th, trows, tk, 'J2', band_key=8)

lh = ['lever_id','pillar','subpillar','group_id','group','family_id','family','lever','lever full phrase','joins when','joins not','intervention evidence','evidence finding','evidence strength','design','fit to lever','basis','read','source verified','source url','framework source','framework where','framework says','framework references','thesis literature','thesis findings','backing grade','theory anchors','n_pathways','pathways','mechanism evidence','risks','text_cues','entry_points','Reviewer comment']
lk = ['id','name','name','id','name','id','name','name','long','long','long','long','long','name','name','name','long','name','name','long','name','name','long','long','long','long','name','long','num','long','long','name','long','long','long']
lrows = [[l['lever_id'], l['pillar'], l['subpillar'], l['group_id'], l['group'], l['family_id'], l['family'], l['lever'], l['lever_full'],
          l['joins_when'], l['joins_not'], l.get('intervention_evidence',''), l.get('evidence_finding',''), l.get('evidence_strength',''), l.get('evidence_design',''), l.get('evidence_fit',''), l.get('evidence_basis',''), l.get('evidence_checked',''), l.get('evidence_verified',''), l.get('evidence_url',''),
          l.get('framework_source',''), l.get('framework_where',''), l.get('framework_says',''), '; '.join(l.get('framework_refs') or []),
          l.get('thesis_citations',''), ' | '.join(r.get('finding','') for r in (l.get('thesis_refs') or []) if r.get('finding')),
          l.get('backing_grade',''), l.get('theory_anchor_ids',''), l['n_pathways'], l['pathways'], l['evidence'], l['risks'], l['text_cues'], l['entry_points'], ''] for l in L]
sheet(wb, 'Levers', lh, lrows, lk, 'B2')

# Codebook: the independent reviewer's structure, filled from the tree
def lever_of(pid):
    pid = MERGED.get(pid, pid)
    return pby[pid]['lever_id'] if pid in pby else None

missing_ids = []
def competing(l):
    out = []
    for pid in re.findall(r'L3-\d{3}', l['joins_not'] or ''):
        lid = lever_of(pid)
        if lid is None:
            missing_ids.append((l['lever_id'], pid)); continue
        if lid != l['lever_id'] and lid not in out: out.append(lid)
    return '; '.join('%s %s' % (x, lby[x]['lever']) for x in out)

def threats(l):
    t = []
    fs = l.get('framework_status', '')
    if fs == 'weak': t.append('framework anchor weak')
    if fs == 'not discussed': t.append('framework document does not discuss this lever')
    if fs == 'none': t.append('no framework document yet')
    if l.get('evidence_fit') in ('partial', 'loose'): t.append('evidence fit ' + l['evidence_fit'])
    if l.get('evidence_strength') == 'thin': t.append('evidence thin')
    if l.get('evidence_strength') in ('none found', ''): t.append('no intervention-level source found')
    if l.get('evidence_checked') == 'abstract': t.append('source read in abstract only')
    return '; '.join(t)

CB_STATUS = 'draft codebook 4 November 2026: definitions, tests, mechanisms and literature filled from the tree; indicators to be written by reviewers'
ch = ['lever_id','pillar','subpillar','group','family','lever','operational definition','framework anchor','what the framework says','causal mechanism','scope conditions','include when','exclude when','competing levers','plan-language examples','intervention evidence','evidence finding','thesis papers','theory anchors','framework references','Thai strategies on this lever','observable indicators','threats to validity','backing grade','status','Reviewer comment']
ck = ['id','name','name','name','name','name','long','long','long','long','long','long','long','long','long','long','long','long','long','long','num','long','long','name','long','long']
crows = []
for l in L:
    pws = [pby[x] for x in l['pathway_ids'] if x in pby]
    anchor = ', '.join(x for x in (l.get('framework_source',''), l.get('framework_where','')) if x) or 'No framework document published yet'
    ev = l.get('intervention_evidence','')
    tags = ', '.join(x for x in (l.get('evidence_strength',''), l.get('evidence_design',''), 'fit ' + l['evidence_fit'] if l.get('evidence_fit') else '') if x)
    crows.append([l['lever_id'], l['pillar'], l['subpillar'], l['group'], l['family'], l['lever'], l['lever_full'], anchor, l.get('framework_says',''),
                  ' | '.join('%s: %s -> %s -> %s' % (p['pathway'], p['causal_input'], p['transmission'], p['outcome']) for p in pws),
                  ' | '.join(p['conditions'] for p in pws if p['conditions']), l['joins_when'], l['joins_not'], competing(l),
                  '; '.join(l.get('entry_points') or []), ev + (' [%s]' % tags if ev and tags else ''), l.get('evidence_finding',''),
                  l.get('thesis_citations',''), l.get('theory_anchor_ids',''), '; '.join(l.get('framework_refs') or []), l.get('thai_strategies', 0),
                  '', threats(l), l.get('backing_grade',''), CB_STATUS, ''])
sheet(wb, 'Codebook', ch, crows, ck, 'G2')

# Backing: the gaps first
bh = ['lever_id','lever','family_id','family','subpillar','framework status','evidence strength','evidence fit','thesis papers (n)','theory anchors (n)','Thai strategies','backing score','backing grade','Reviewer comment']
bk = ['id','name','id','name','name','name','name','name','num','num','num','num','name','long']
bL = sorted(L, key=lambda l: (GRADES.index(l['backing_grade']), l['lever_id']))
brows = [[l['lever_id'], l['lever'], l['family_id'], l['family'], l['subpillar_code'], l['framework_status'], l.get('evidence_strength',''), l.get('evidence_fit',''),
          l.get('thesis_n', 0), l.get('theory_n', 0), l.get('thai_strategies', 0), l['backing_score'], l['backing_grade'], ''] for l in bL]
sheet(wb, 'Backing', bh, brows, bk, 'C2', band_key=12)

# Backing summary (a separate sheet: the sheet() helper writes its header on the first row)
sh = ['subpillar','name','well backed','backed','thin','unbacked','levers']
sk = ['id','name','num','num','num','num','num']
srows = []
for sp in d['subpillars']:
    ls = [l for l in L if l['subpillar_code'] == sp['code']]
    c = collections.Counter(l['backing_grade'] for l in ls)
    srows.append([sp['code'], sp['name'], c['well backed'], c['backed'], c['thin'], c['unbacked'], len(ls)])
c = collections.Counter(l['backing_grade'] for l in L)
srows.append(['All', 'All levers', c['well backed'], c['backed'], c['thin'], c['unbacked'], len(L)])
sheet(wb, 'Backing summary', sh, srows, sk, 'C2')

# Theory anchors: the independent reviewer's references
fam_of = collections.defaultdict(list)
for f in F:
    for a in f.get('theory_anchors') or []: fam_of[a['ref_id']].append(f['family_id'])
lev_of = collections.defaultdict(list)
for ln in cw['links']:
    if ln['reviewer_lever'] not in lev_of[ln['ref_id']]: lev_of[ln['ref_id']].append(ln['reviewer_lever'])
ah = ['ref_id','author','year','title','venue','strand','kind','contribution','in framework pass','our families','reviewer levers','url','Reviewer comment']
ak = ['id','name','num','long','name','name','name','long','long','long','name','long','long']
arows = [[r['ref_id'], r.get('author',''), r.get('year',''), r.get('title',''), r.get('venue',''), r.get('strand',''), r.get('kind',''), r.get('contribution',''),
          r.get('in_framework_pass',''), fam_of[r['ref_id']], lev_of[r['ref_id']], r.get('url',''), ''] for r in cw['references']]
sheet(wb, 'Theory anchors', ah, arows, ak, 'B2')

xh = ['code','name','our subpillar','our groups','our families','secondary families','note','Reviewer comment']
xk = ['id','name','id','long','long','long','long','long']
xrows = [[r['code'], r['name'], r.get('our_subpillar',''), r.get('groups') or [], r.get('families') or [], r.get('secondary_families') or [], r.get('note',''), ''] for r in cw['reviewer_levers']]
sheet(wb, 'Reviewer crosswalk', xh, xrows, xk, 'B2')

fh = ['family_id','family','group_id','group','subpillar','pillar','definition','examples','plan_words','n_levers','lever_ids','n_pathways','pathway_ids','risks','Reviewer comment']
fk = ['id','name','id','name','name','name','long','long','long','num','long','num','long','name','long']
frows = [[f['family_id'], f['family'], f['group_id'], f['group'], f['subpillar'], f['pillar'], f.get('definition',''), f.get('examples',''), f.get('plan_words',''),
          f['n_levers'], f['lever_ids'], f['n_pathways'], f['pathway_ids'], f['risks'], ''] for f in F]
sheet(wb, 'Families', fh, frows, fk, 'C2')

gh = ['group_id','group','subpillar','pillar','framework (basis)','definition','n_families','family_ids','n_levers','Reviewer comment']
gk = ['id','name','name','name','long','long','num','long','num','long']
grows = [[g['group_id'], g['group'], g['subpillar'], g['pillar'], g.get('basis',''), g.get('definition',''), g['n_families'], g['family_ids'], g['n_levers'], ''] for g in G]
sheet(wb, 'Groups', gh, grows, gk, 'C2')

# checks
assert len(crows)==229 and len(brows)==229 and len(arows)==27 and len(xrows)==18
assert len(ch)==len(ck) and len(bh)==len(bk) and len(ah)==len(ak) and len(xh)==len(xk) and len(sh)==len(sk) and len(lh)==len(lk)
if missing_ids: print('joins_not names L3 ids that no longer exist:', missing_ids)
assert len(trows)==263 and len(lrows)==229 and len(frows)==60 and len(grows)==33
assert all(r[8] for r in trows)
cnt = collections.Counter(r[8] for r in trows)
assert all(cnt[l['lever_id']]==l['n_pathways'] for l in L) and set(cnt)==set(lby)
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'PVII_mother_tree_v4_levers.xlsx')
os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
wb.save(out)
print('saved', out)
