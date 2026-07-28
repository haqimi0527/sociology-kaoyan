# -*- coding: utf-8 -*-
"""Layer 0: Data integrity validation"""
import json, os, sys, io
from collections import Counter

# Force UTF-8 on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'web', 'data')
ERRORS = []

def err(msg):
    ERRORS.append(msg)
    print(f"  [FAIL] {msg}")

def load(name):
    path = os.path.join(DATA_DIR, name)
    if not os.path.exists(path):
        err(f"{name} not found")
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        err(f"{name} JSON parse error: {e}")
        return None

def check_concepts():
    data = load('concepts.json')
    if not data: return
    ids, no_id = [], 0
    for i, c in enumerate(data):
        if not isinstance(c, dict): err(f"concepts[{i}] not a dict"); continue
        for field in ['id', 'term', 'definition']:
            if field not in c or not c[field]:
                err(f"concepts[{i}] missing '{field}' (term={str(c.get('term','?'))[:30]})")
        if c.get('id'): ids.append(c['id'])
        else: no_id += 1
    dupes = [id_ for id_, count in Counter(ids).items() if count > 1]
    for d in dupes: err(f"concepts.json duplicate id: {d}")
    print(f"  [OK] concepts.json: {len(data)} entries, {len(dupes)} dupes, {no_id} missing-id")

def check_exams():
    data = load('exams.json')
    if not data: return
    valid_types = {'名词解释', '简答', '论述', '计算', '设计题', '单选', '多选', '判断',
                   '其他', '填空', '选择', '辨析', '分析'}  # actual types found in data
    missing = 0
    for i, e in enumerate(data):
        if not isinstance(e, dict): err(f"exams[{i}] not a dict"); continue
        for field in ['school', 'year', 'type', 'question']:
            if field not in e or e[field] is None:
                err(f"exams[{i}] missing '{field}' (school={e.get('school','?')})")
                missing += 1
        t = e.get('type', '')
        if t and t not in valid_types:
            err(f"exams[{i}] (school={e.get('school','?')}) unknown type: '{t}'")
        y = e.get('year')
        if y is not None:
            if not isinstance(y, int): err(f"exams[{i}] year is not int: {y}")
            elif y > 2026: err(f"exams[{i}] (school={e.get('school','?')}) future year: {y}, type={t}, q={str(e.get('question',''))[:50]}")
            elif y < 1990: err(f"exams[{i}] (school={e.get('school','?')}) too-old year: {y}")
    schools = set(e.get('school', '') for e in data if isinstance(e, dict))
    print(f"  [OK] exams.json: {len(data)} questions, {missing} incomplete, {len(schools)} schools")

def check_politics():
    data = load('politics.json')
    if not data: return
    ids = []
    for i, p in enumerate(data):
        if not isinstance(p, dict): err(f"politics[{i}] not a dict"); continue
        for field in ['id', 'module', 'stem', 'options', 'answer']:
            if field not in p: err(f"politics[{i}] missing '{field}' (id={p.get('id','?')})")
        if isinstance(p.get('options'), list) and isinstance(p.get('answer'), int):
            if p['answer'] < 0 or p['answer'] >= len(p['options']):
                err(f"politics[{i}] id={p.get('id','?')} answer idx {p['answer']} out of range (options len={len(p['options'])})")
        if p.get('id'): ids.append(p['id'])
    dupes = [id_ for id_, count in Counter(ids).items() if count > 1]
    for d in dupes: err(f"politics.json duplicate id: {d}")
    modules = set(p.get('module', '') for p in data if isinstance(p, dict))
    print(f"  [OK] politics.json: {len(data)} questions, {len(dupes)} dupes, modules: {modules}")

def check_vocab():
    data = load('english-vocab.json')
    if not data: return
    bad = 0
    for i, v in enumerate(data[:100]):
        if not isinstance(v, dict): err(f"vocab[{i}] not a dict"); continue
        if 'word' not in v or not v.get('word'): err(f"vocab[{i}] missing word"); bad += 1
        if 'meaning' not in v or not v.get('meaning'): err(f"vocab[{i}] ({str(v.get('word','?'))[:20]}) missing meaning"); bad += 1
    words = [(v.get('word', '').strip() if isinstance(v, dict) else '') for v in data]
    # case-sensitive: 'march'(行进) and 'March'(三月) are different words
    wdupes = [w for w, c in Counter(words).items() if c > 1 and w]
    for w in wdupes[:10]: err(f"vocab duplicate word: '{w}' ({Counter(words)[w]} times)")
    print(f"  [OK] english-vocab.json: {len(data)} words, {bad} bad, {len(wdupes)} duplicate words")

def check_taxonomy():
    """concept-taxonomy.json: verify structure, cross-ref with concepts.json"""
    data = load('concept-taxonomy.json')
    if not data: return
    if not isinstance(data, dict):
        err("concept-taxonomy.json top-level is not dict"); return
    # check required domains
    for domain in ['theory', 'methods', 'intro']:
        if domain not in data:
            err(f"concept-taxonomy.json missing domain: {domain}")
    # check _meta
    meta = data.get('_meta', {})
    print(f"  [OK] taxonomy: {meta.get('total_concepts','?')} total, {meta.get('classified','?')} classified, {meta.get('unclassified','?')} unclassified")
    # collect all concept IDs from taxonomy (stored as string IDs in 'concepts' arrays)
    tax_ids = set()
    def collect(node):
        if isinstance(node, list):
            for item in node:
                if isinstance(item, str) and item.startswith('c_'):
                    tax_ids.add(item)
                elif isinstance(item, dict) and 'id' in item:
                    tax_ids.add(item['id'])
        elif isinstance(node, dict):
            for k, v in node.items():
                if k == 'concepts' and isinstance(v, list):
                    for item in v:
                        if isinstance(item, str):
                            tax_ids.add(item)
                else:
                    collect(v)
    for domain in ['theory', 'methods', 'intro']:
        collect(data[domain])
    # cross-ref with concepts.json
    concepts = load('concepts.json')
    if concepts:
        concept_ids = {c['id'] for c in concepts if isinstance(c, dict) and 'id' in c}
        missing_in_concepts = tax_ids - concept_ids
        missing_in_tax = concept_ids - tax_ids
        if missing_in_concepts:
            for mid in list(missing_in_concepts)[:10]:
                err(f"taxonomy id {mid} not found in concepts.json")
        if missing_in_tax:
            expected_unclassified = meta.get('unclassified', 0)
            if len(missing_in_tax) != expected_unclassified:
                err(f"taxonomy missing {len(missing_in_tax)} concepts (expected {expected_unclassified})")
            else:
                print(f"  [OK] taxonomy covers {len(tax_ids)} concepts, {len(missing_in_tax)} unclassified (matches _meta)")
        else:
            print(f"  [OK] taxonomy covers all {len(tax_ids)} concepts")

def check_file_sizes():
    expected = {
        'concepts.json': (1_000_000, 2_000_000),
        'exams.json': (500_000, 1_500_000),
        'politics.json': (500_000, 1_000_000),
        'english-vocab.json': (500_000, 1_500_000),
        'concept-taxonomy.json': (40_000, 100_000),
        'politics-essay.json': (50_000, 200_000),
        'theory-topics.json': (50_000, 300_000),
        'methods-questions.json': (100_000, 500_000),
    }
    for fname, (lo, hi) in expected.items():
        path = os.path.join(DATA_DIR, fname)
        if not os.path.exists(path): continue
        size = os.path.getsize(path)
        if size < lo: err(f"{fname} size {size:,} < min {lo:,}")
        elif size > hi: err(f"{fname} size {size:,} > max {hi:,}")
        else: print(f"  [OK] {fname}: {size:,} bytes")

def main():
    print("Layer 0: Data Integrity Check")
    print("=" * 50)
    check_concepts()
    check_exams()
    check_politics()
    check_vocab()
    check_taxonomy()
    check_file_sizes()
    if ERRORS:
        print(f"\n[FAIL] {len(ERRORS)} errors found")
        sys.exit(1)
    print(f"\n[PASS] All data checks passed")
    sys.exit(0)

if __name__ == '__main__':
    main()
