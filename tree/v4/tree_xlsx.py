"""Write the reviewers' workbook of tree v4: python3 tree_xlsx.py [out.xlsx]"""
import json, os, sys, collections
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
 ('Framework columns (on the lever rows): what the framework document behind the group (Inclusion Matters, the Human Development Reports, inclusive wealth, the Growth Report, the WDRs, the Future-Ready Governance Index) says about the action, where, and the references it cites for it, copied from its reference list.', None),
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
 ('Families: one row per family (60), with definition, examples, plan words and its lever ids.', None),
 ('Groups: one row per group (33), with the published framework it draws on (basis) and its definition.', None),
]
for t, s in lines:
    rm.append([t]); c = rm.cell(rm.max_row, 1)
    if s == 'title': c.font = Font(bold=True, size=14)
    elif s == 'bold': c.font = Font(bold=True)
rm.column_dimensions['A'].width = 150

# Tree
th = ['pillar','subpillar','group_id','group','group framework','family_id','family','family definition','lever_id','lever','lever full phrase','joins when','joins not','intervention evidence','evidence finding','evidence strength','design','fit to lever','basis','framework says','framework references','pathway_id','pathway','causal input','transmission','outcome','conditions','distinction','evidence (citations)','evidence_status','risks','Reviewer comment']
tk = ['name','name','id','name','long','id','name','long','id','name','long','long','long','long','long','name','name','name','long','long','long','id','name','long','long','long','long','long','long','name','name','long']
Ps = sorted(P, key=lambda p: (forder[p['family_id']], p['lever_id'], p['pathway_id']))
trows = []
for p in Ps:
    l, f, g = lby[p['lever_id']], fby[p['family_id']], gby[p['group_id']]
    trows.append([p['pillar'], p['subpillar'], g['group_id'], g['group'], g.get('basis',''), f['family_id'], f['family'], f.get('definition',''),
                  l['lever_id'], l['lever'], l['lever_full'], l['joins_when'], l['joins_not'],
                  l.get('intervention_evidence',''), l.get('evidence_finding',''), l.get('evidence_strength',''), l.get('evidence_design',''), l.get('evidence_fit',''), l.get('evidence_basis',''), l.get('framework_says',''), '; '.join(l.get('framework_refs') or []), p['pathway_id'], p['pathway'],
                  p['causal_input'], p['transmission'], p['outcome'], p['conditions'], p['distinction'], p['evidence'], p['evidence_status'], p['risks'], ''])
sheet(wb, 'Tree', th, trows, tk, 'J2', band_key=8)

lh = ['lever_id','pillar','subpillar','group_id','group','family_id','family','lever','lever full phrase','joins when','joins not','intervention evidence','evidence finding','evidence strength','design','fit to lever','basis','read','source verified','source url','framework source','framework where','framework says','framework references','n_pathways','pathways','mechanism evidence','risks','text_cues','entry_points','Reviewer comment']
lk = ['id','name','name','id','name','id','name','name','long','long','long','long','long','name','name','name','long','name','name','long','name','name','long','long','num','long','long','name','long','long','long']
lrows = [[l['lever_id'], l['pillar'], l['subpillar'], l['group_id'], l['group'], l['family_id'], l['family'], l['lever'], l['lever_full'],
          l['joins_when'], l['joins_not'], l.get('intervention_evidence',''), l.get('evidence_finding',''), l.get('evidence_strength',''), l.get('evidence_design',''), l.get('evidence_fit',''), l.get('evidence_basis',''), l.get('evidence_checked',''), l.get('evidence_verified',''), l.get('evidence_url',''),
          l.get('framework_source',''), l.get('framework_where',''), l.get('framework_says',''), '; '.join(l.get('framework_refs') or []),
          l['n_pathways'], l['pathways'], l['evidence'], l['risks'], l['text_cues'], l['entry_points'], ''] for l in L]
sheet(wb, 'Levers', lh, lrows, lk, 'B2')

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
assert len(trows)==263 and len(lrows)==229 and len(frows)==60 and len(grows)==33
assert all(r[8] for r in trows)
cnt = collections.Counter(r[8] for r in trows)
assert all(cnt[l['lever_id']]==l['n_pathways'] for l in L) and set(cnt)==set(lby)
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'PVII_mother_tree_v4_levers.xlsx')
os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
wb.save(out)
print('saved', out)
