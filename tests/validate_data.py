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

    # Semantic quality counters
    sem_warn = Counter()

    for i, c in enumerate(data):
        if not isinstance(c, dict): err(f"concepts[{i}] not a dict"); continue
        for field in ['id', 'term', 'definition']:
            if field not in c or not c[field]:
                err(f"concepts[{i}] missing '{field}' (term={str(c.get('term','?'))[:30]})")
        if c.get('id'): ids.append(c['id'])
        else: no_id += 1

        # === Semantic quality checks (warnings only, not hard errors) ===
        term = c.get('term', '').strip()
        definition = c.get('definition', '').strip()
        source = c.get('source_text', '').strip()

        # 1. Definition must not start with narrative markers
        if definition and definition[:1] in '在根据随着关于从对':
            sem_warn['narrative_start'] += 1

        # 2. Definition length: 15-500 chars
        if len(definition) < 15:
            sem_warn['def_too_short'] += 1
        elif len(definition) > 500:
            sem_warn['def_too_long'] += 1

        # 3. Term must not be a chapter title
        import re
        if re.match(r'^(第[一二三四五六七八九十\d]+[章节篇]|[一二三四五六七八九十\d]+[、.\)）]|\d+[\.\、])', term):
            sem_warn['term_is_chapter'] += 1

        # 4. Definition must not contain textbook language
        if any(w in definition[:120] for w in ['本章', '本书', '该书']):
            sem_warn['textbook_language'] += 1

        # 5. Definition should contain at least one sentence-ending period
        if len(definition) >= 20 and '。' not in definition:
            sem_warn['no_period'] += 1

        # 6. source_text should be non-empty (informational)
        if not source:
            sem_warn['no_source_text'] += 1

    dupes = [id_ for id_, count in Counter(ids).items() if count > 1]
    for d in dupes: err(f"concepts.json duplicate id: {d}")
    print(f"  [OK] concepts.json: {len(data)} entries, {len(dupes)} dupes, {no_id} missing-id")

    # === 方向3 增强 5 项 ===
    # 7. ERROR 定义前60字(去空白)查重（白名单豁免）
    # 白名单：tests/config/approved_def_prefix_dups.json
    approved_def_terms = set()
    approved_path = os.path.join(os.path.dirname(__file__), 'config', 'approved_def_prefix_dups.json')
    if os.path.exists(approved_path):
        try:
            _approved = json.load(open(approved_path, encoding='utf-8')).get('approved', [])
            for g in _approved:
                approved_def_terms.update(g.get('terms', []))
        except (json.JSONDecodeError, IOError):
            pass
    def_prefix = Counter()
    def_prefix_terms = {}
    for c in data:
        d = c.get('definition', '') or ''
        if len(d) < 20:
            continue
        key = re.sub(r'\s+', '', d[:60])
        def_prefix[key] += 1
        if key not in def_prefix_terms:
            def_prefix_terms[key] = c.get('term', '')
    for key, cnt in def_prefix.items():
        if cnt > 1:
            # 组内所有 term 都在白名单 → 豁免
            group_terms = [c.get('term', '') for c in data
                           if re.sub(r'\s+', '', (c.get('definition', '') or '')[:60]) == key]
            if all(t in approved_def_terms for t in group_terms):
                continue
            err(f"定义前60字重复: '{def_prefix_terms[key]}' 等 {cnt} 条 → {key[:30]}...")

    # 8. WARN term规范化查重（去括号/标点后重复，排除精确同名）
    norm_terms = Counter()
    norm_terms_example = {}
    for c in data:
        t = c.get('term', '').strip()
        nt = re.sub(r'[（）()\s,，。、；;：:]', '', t)
        if nt:
            norm_terms[nt] += 1
            if nt not in norm_terms_example:
                norm_terms_example[nt] = t
    for nt, cnt in norm_terms.items():
        if cnt > 1:
            sem_warn['term_norm_dup'] += 1
            if cnt == 2:  # 只 warn，不打断
                pass
    # 打印 term 规范化重复组
    term_norm_groups = [(t, c_) for t, c_ in norm_terms.items() if c_ > 1]
    if term_norm_groups:
        print(f"  [WARN] term规范化重复组: {len(term_norm_groups)}")
        for t, c_ in term_norm_groups[:8]:
            print(f"         '{norm_terms_example[t]}' x{c_}")

    # 9. ERROR chapter顶层白名单 {理论,方法,概论,未分类,''(空)}
    bad_top = Counter()
    for c in data:
        ch = c.get('chapter', '') or ''
        top = ch.split('/')[0] if ch else ''
        if top and top not in ('理论', '方法', '概论', '未分类'):
            bad_top[top] += 1
    if bad_top:
        err(f"chapter顶层白名单违规: {dict(bad_top)}")

    # 10. WARN term碎片检测
    from collections import Counter as _C
    frag_cnt = 0
    for c in data:
        t = (c.get('term', '') or '').strip()
        # 残句/泛化词特征
        if (t.endswith(('的', '之', '中', '下', '与', '及', '或'))
                or re.match(r'^(一是|二是|三是|不同之处|具体来说|如下|包括|分为|在于)', t)
                or re.match(r'^例\d+', t)
                or '如何' in t or '怎样' in t or '为什么' in t
                or t in ('过程与步骤', '作用与重要性', '要求与问题', '怎么做', '解决措施', '优缺点')):
            frag_cnt += 1
            sem_warn['term_fragment'] += 1
    if frag_cnt:
        print(f"  [WARN] term碎片: {frag_cnt} 条")

    # 11. WARN 人名目录检测（理论/ 直接挂学者名）
    scholar_dir_cnt = 0
    import sys as _sys
    try:
        _sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from pipeline.utils.concept_utils import SCHOLAR_NAMES
    except ImportError:
        SCHOLAR_NAMES = set()
    for c in data:
        ch = c.get('chapter', '') or ''
        parts = [p for p in ch.split('/') if p]
        if parts and parts[0] == '理论' and len(parts) == 2 and parts[1] in SCHOLAR_NAMES:
            scholar_dir_cnt += 1
            sem_warn['scholar_dir'] += 1
    if scholar_dir_cnt:
        print(f"  [WARN] 人名目录(理论/学者名): {scholar_dir_cnt} 条")

    # Print semantic warnings
    if sem_warn:
        total_warn = sum(sem_warn.values())
        print(f"  [WARN] Semantic quality issues: {total_warn} total")
        for k, v in sem_warn.most_common():
            print(f"         {k}: {v}")

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
                if k in ('concepts', 'ungrouped_concepts') and isinstance(v, list):
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
        'concepts.json': (1_000_000, 3_000_000),
        'exams.json': (500_000, 1_500_000),
        'politics.json': (500_000, 1_000_000),
        'english-vocab.json': (500_000, 1_500_000),
        'concept-taxonomy.json': (40_000, 100_000),
        'politics-essay.json': (50_000, 200_000),
        'theory-topics.json': (50_000, 300_000),
        'methods-questions.json': (100_000, 2_500_000),
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
