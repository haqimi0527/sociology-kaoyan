"""
Comprehensive taxonomy audit — checks ALL error categories at once.
"""
import json, sys, re, os
from collections import defaultdict, Counter

sys.stdout.reconfigure(encoding='utf-8')

with open(os.path.join(os.path.dirname(__file__), '..', 'web', 'data', 'concept-taxonomy.json'), 'r', encoding='utf-8') as f:
    tx = json.load(f)
with open(os.path.join(os.path.dirname(__file__), '..', 'web', 'data', 'concepts.json'), 'r', encoding='utf-8') as f:
    concepts = json.load(f)
cmap = {c['id']: c for c in concepts}

issues = []
def issue(sev, cat, msg):
    issues.append((sev, cat, msg))

# ===== 1. Collect IDs per domain =====
ALL_SCHOLARS = set()
theory_ids, methods_ids, intro_ids = set(), set(), set()
for era_n, era in tx['theory'].items():
    for sch_n, sch in era.items():
        for sname, sdata in sch.get('scholars', {}).items():
            ALL_SCHOLARS.add(sname)
            for cid in sdata['concepts']:
                theory_ids.add(cid)
for ph_n, ph in tx['methods'].items():
    for cat_n, cat in ph['categories'].items():
        for cid in cat['concepts']:
            methods_ids.add(cid)
for topic, tdata in tx['intro'].items():
    for cid in tdata['concepts']:
        intro_ids.add(cid)

CLASSIFIED = theory_ids | methods_ids | intro_ids
UNCLASSIFIED = set(c['id'] for c in concepts) - CLASSIFIED

# ===== 2. CHECKS =====

# 2a: Domain mismatch — theory chapter path in methods
theory_signals = ['古典时期', '现代时期', '当代时期', '韦伯', '涂尔干', '马克思', '齐美尔',
                  '帕森斯', '布迪厄', '福柯', '吉登斯', '哈贝马斯', '常人方法学', '现象学']
for cid in methods_ids:
    c = cmap.get(cid)
    if not c: continue
    ch = c.get('chapter', '')
    matched = [s for s in theory_signals if s in ch]
    if matched:
        issue('ERR', 'theory-in-methods',
              f"{c['term']}: chapter={ch} (theory signals: {matched}) but in METHODS")

# 2b: Methods chapter path in theory/intro
for cid in theory_ids | intro_ids:
    c = cmap.get(cid)
    if not c: continue
    ch = c.get('chapter', '')
    if '研究方法' in ch or '社会学研究方法' in ch or ch.startswith('方法/'):
        issue('ERR', 'methods-in-theory',
              f"{c['term']}: chapter={ch} but in theory/intro")

# 2c: Intro without 概论 chapter
for cid in intro_ids:
    c = cmap.get(cid)
    if not c: continue
    if '概论' not in c.get('chapter', ''):
        issue('WARN', 'intro-no-概论', f"{c['term']}: chapter={c.get('chapter')}")

# ===== 3. Scholar vs chapter conflict =====
for cid in theory_ids:
    c = cmap.get(cid)
    if not c: continue
    ch = c.get('chapter', '')
    assigned = None
    for era_n, era in tx['theory'].items():
        for sch_n, sch in era.items():
            for sname, sdata in sch.get('scholars', {}).items():
                if cid in sdata['concepts']:
                    assigned = sname
    if not assigned: continue
    for other in ALL_SCHOLARS:
        if other != assigned and other in ch:
            if assigned in ch:
                continue  # Both in chapter, co-located
            issue('WARN', 'scholar-chapter-conflict',
                  f"{c['term']}: assigned={assigned} but chapter has {other} ({ch})")

# ===== 4. Short/dangerous keywords =====
with open(os.path.join(os.path.dirname(__file__), '..', 'scripts', 'build_taxonomy.py'), 'r', encoding='utf-8') as f:
    build_src = f.read()

all_kws_raw = re.findall(r'"keywords":\s*\[(.*?)\]', build_src, re.DOTALL)
all_kws = []
for match in all_kws_raw:
    kws = re.findall(r'"([^"]+)"', match)
    all_kws.extend(kws)
unique_kws = set(all_kws)

# 1-2 char keywords (excluding known acronyms)
known_short = {'ANT', 'PPS', 'Z分数', 'P值', 'p值', 't检验', 'F检验'}
dangerous_short = [kw for kw in unique_kws if len(kw) <= 2 and kw not in known_short]
if dangerous_short:
    issue('WARN', 'short-keywords', f'{len(dangerous_short)} keywords <=2 chars: {dangerous_short}')

# ===== 5. Empty string guards in build script =====
# Check for 'in scholarname' patterns without non-empty guard
suspect_lines = 0
for line in build_src.split('\n'):
    stripped = line.strip()
    if 'scholar_name in' in stripped or 'school_name in' in stripped:
        if ' and ' not in stripped:
            suspect_lines += 1
if suspect_lines:
    issue('WARN', 'unguarded-in', f'{suspect_lines} lines with potential unguarded "in" checks')

# ===== 6. Scholar concept count anomalies =====
for era_n, era in tx['theory'].items():
    for sch_n, sch in era.items():
        for sname, sdata in sch.get('scholars', {}).items():
            n = len(sdata['concepts'])
            if n > 50:
                issue('WARN', 'scholar-heavy', f'{sname}: {n} concepts (>{50}, possible keyword over-match)')
            elif n == 0:
                issue('ERR', 'scholar-empty', f'{sname}: 0 concepts in {era_n[:4]}/{sch_n}')

# ===== 7. Empty method categories =====
for ph_n, ph in tx['methods'].items():
    for cat_n, cat in ph['categories'].items():
        if len(cat['concepts']) == 0:
            issue('ERR', 'method-cat-empty', f'{ph_n}/{cat_n}: 0 concepts')

# ===== 8. Cross-domain duplicates =====
overlap = (theory_ids & methods_ids) | (theory_ids & intro_ids) | (methods_ids & intro_ids)
if overlap:
    for cid in overlap:
        c = cmap.get(cid)
        issue('ERR', 'cross-domain-dup', f"{c['term'] if c else cid} in multiple domains")

# ===== 9. Numbered chapters (should be named) =====
num_ch = 0
for c in concepts:
    for p in c.get('chapter', '').split('/'):
        if re.match(r'^第[一二三四五六七八九十百\d]+章$', p):
            num_ch += 1
            break
if num_ch:
    issue('WARN', 'numbered-chapters', f'{num_ch} concepts use numbered chapters (should be topic names)')

# ===== 10. Empty fields in concepts =====
for field in ['term', 'definition', 'chapter']:
    cnt = sum(1 for c in concepts if not c.get(field))
    if cnt:
        issue('ERR', f'empty-{field}', f'{cnt} concepts have empty {field}')

cnt_no_tags = sum(1 for c in concepts if not c.get('tags'))
cnt_no_prop = sum(1 for c in concepts if not c.get('proponent'))
if cnt_no_tags: issue('INFO', 'empty-tags', f'{cnt_no_tags} concepts have no tags')
if cnt_no_prop: issue('INFO', 'empty-proponent', f'{cnt_no_prop} concepts have no proponent')

# ===== 11. Chapter path anomalies =====
for c in concepts:
    ch = c.get('chapter', '')
    if '//' in ch:
        issue('WARN', 'double-slash', f"{c['term']}: chapter has '//' -> {ch}")

# ===== 12. Unclassified concepts check =====
if UNCLASSIFIED:
    for cid in UNCLASSIFIED:
        c = cmap.get(cid)
        if c:
            issue('INFO', 'unclassified', f"{c['term']} (chapter={c.get('chapter','')})")

# ===== 13. Proponent vs assigned scholar mismatch =====
for cid in theory_ids:
    c = cmap.get(cid)
    if not c: continue
    prop = (c.get('proponent') or '').strip()
    if not prop: continue
    # Find assigned
    assigned = None
    for era_n, era in tx['theory'].items():
        for sch_n, sch in era.items():
            for sname, sdata in sch.get('scholars', {}).items():
                if cid in sdata['concepts']:
                    assigned = sname
    if assigned and assigned not in prop and prop not in assigned:
        # Check if any proponent name is in assigned or vice versa (e.g. shared concept)
        prop_names = [x.strip() for x in prop.split('/')]
        if assigned not in prop_names:
            issue('WARN', 'proponent-mismatch',
                  f"{c['term']}: assigned={assigned} but proponent={prop}")

# ===== PRINT =====
print('=' * 60)
print(f'TAXONOMY AUDIT: {len(issues)} total issues')
print(f'  ERR:  {sum(1 for s,_,_ in issues if s == "ERR")}')
print(f'  WARN: {sum(1 for s,_,_ in issues if s == "WARN")}')
print(f'  INFO: {sum(1 for s,_,_ in issues if s == "INFO")}')
print('=' * 60)

for sev in ['ERR', 'WARN', 'INFO']:
    items = [(c, m) for s, c, m in issues if s == sev]
    if items:
        print(f'\n--- {sev} ({len(items)}) ---')
        for cat, msg in sorted(items):
            print(f'  [{cat}] {msg}')

if not issues:
    print('\n>>> ZERO ISSUES FOUND <<<')
