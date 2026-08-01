"""
数据语义合理性校验 — Layer 0-B：格式正确但内容可能是 AI 编造的。
6 条规则覆盖题干幻觉、年份合理性、分值一致性、概念名噪声、重复定义。
用法: python tests/validate_data_semantic.py
"""
import json
import os
import sys
from collections import Counter, defaultdict

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'web', 'data')
ERRORS = []
WARNS = []

def err(msg):
    ERRORS.append(msg)
    print(f"  [ERROR] {msg}")

def warn(msg):
    WARNS.append(msg)
    print(f"  [WARN]  {msg}")

def ok(msg):
    print(f"  [OK]    {msg}")

def load(name):
    path = os.path.join(DATA_DIR, name)
    if not os.path.exists(path):
        err(f"{name} file not found")
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        err(f"{name} parse error: {e}")
        return None


# ===== Rule 1: exams — 题干幻觉检测 =====
def check_exam_hallucination():
    """
    检测 DeepSeek 编造题目的常见痕迹：
    - 非真实地名（"卢店"）
    - AI 模板句式（"某市""假设有一所学校""某研究者"）
    - 明显编造的学校/机构名
    """
    data = load('exams.json')
    if not data:
        return

    hallucination_patterns = [
        (r'卢店', '疑似编造地名'),
        (r'某市', 'AI模板句式'),
        (r'假设有一所', 'AI模板句式'),
        (r'某研究者', 'AI模板句式（可能正常）'),
    ]

    import re
    hits = defaultdict(list)
    for i, e in enumerate(data):
        q = e.get('question', '')
        for pat, reason in hallucination_patterns:
            if re.search(pat, q):
                hits[pat].append((i, e.get('school', '?'), e.get('year', '?'), q[:60]))

    total = sum(len(v) for v in hits.values())
    if total > 0:
        for pat, entries in hits.items():
            for idx, school, year, snippet in entries[:5]:
                warn(f"幻觉检测 [{pat}]: exams[{idx}] {school} {year}: {snippet}...")
            if len(entries) > 5:
                warn(f"  ... and {len(entries) - 5} more matches for '{pat}'")
    ok(f"Rule 1 (hallucination): {total} suspicious patterns found")


# ===== Rule 2: exams — 年份合理性 =====
def check_exam_year():
    data = load('exams.json')
    if not data:
        return

    bad_years = []
    for i, e in enumerate(data):
        year = e.get('year')
        if year is None:
            continue
        if not isinstance(year, int) or year < 1990 or year > 2026:
            bad_years.append((i, e.get('school', '?'), year, e.get('question', '')[:60]))

    for idx, school, year, snippet in bad_years:
        err(f"年份异常: exams[{idx}] {school} year={year}: {snippet}...")

    # 年份分布
    years = [e['year'] for e in data if isinstance(e.get('year'), int)]
    if years:
        from collections import Counter
        yc = Counter(years)
        # 某一年题目数异常多
        avg = len(data) / max(1, len(yc))
        for y, cnt in yc.most_common(5):
            if cnt > avg * 5:
                warn(f"年份分布异常: {y}年有{cnt}题（均值≈{avg:.0f}），可能数据合并错误")

    ok(f"Rule 2 (year): {len(bad_years)} out-of-range, years {min(years)}-{max(years)}")


# ===== Rule 3: exams — 学校年份跨度 =====
def check_school_year_span():
    data = load('exams.json')
    if not data:
        return

    school_years = defaultdict(set)
    for e in data:
        school = (e.get('school') or '').strip()
        year = e.get('year')
        if school and isinstance(year, int):
            school_years[school].add(year)

    for school, years in sorted(school_years.items()):
        if not years:
            continue
        span = max(years) - min(years)
        if span > 30:
            warn(f"学校年份跨度过大: {school} {min(years)}-{max(years)} (跨度{span}年)，"
                 f"请确认是否不同学校数据错误合并")
        elif span == 0:
            warn(f"学校只有单一年份: {school} ({min(years)}年)，可能缺少其他年份数据")

    ok(f"Rule 3 (school span): {len(school_years)} schools checked")


# ===== Rule 4: exams — 题型分值一致性 =====
def check_exam_score():
    data = load('exams.json')
    if not data:
        return

    # 常见分值范围（宽松）
    expected_scores = {
        '名词解释': (3, 10),
        '简答': (5, 20),
        '论述': (10, 40),
        '计算': (5, 25),
        '设计题': (10, 30),
        '单选': (1, 5),
        '多选': (1, 5),
        '判断': (1, 5),
        '辨析': (5, 15),
        '选择': (1, 5),
        '填空': (1, 5),
        '分析': (10, 30),
    }

    bad_scores = []
    null_count = 0
    for i, e in enumerate(data):
        score = e.get('score')
        typ = (e.get('type') or '').strip()
        if score is None:
            null_count += 1
            continue
        if not isinstance(score, (int, float)):
            bad_scores.append((i, typ, score, '非数字'))
            continue
        if typ in expected_scores:
            lo, hi = expected_scores[typ]
            if score < lo or score > hi:
                bad_scores.append((i, typ, score, f'预期 {lo}-{hi}'))

    for idx, typ, score, reason in bad_scores[:10]:
        school = data[idx].get('school', '?')
        warn(f"分值异常: exams[{idx}] {school} {typ} score={score} ({reason})")

    ok(f"Rule 4 (score): {len(bad_scores)} abnormal scores, {null_count}/{len(data)} null")


# ===== Rule 5: concepts — 概念名噪声 =====
def check_concept_name_noise():
    data = load('concepts.json')
    if not data:
        return

    import re
    # 不应出现的噪声模式
    noise_patterns = [
        (r'^\d+[\.\、\)]\s*', '编号前缀'),
        (r'（[^）]*(?:重点|掌握|必考|背诵|了解|熟悉)[^）]*）', '标记后缀'),
        (r'[①②③④⑤⑥⑦⑧⑨⑩]', '序号符号'),
    ]

    noisy = []
    for i, c in enumerate(data):
        term = c.get('term', '')
        for pat, reason in noise_patterns:
            if re.search(pat, term):
                noisy.append((i, c.get('id', '?'), term, reason))
                break

    for idx, cid, term, reason in noisy[:20]:
        warn(f"概念名噪声 [{reason}]: concepts[{idx}] id={cid}: '{term}'")

    ok(f"Rule 5 (name noise): {len(noisy)} noisy concept names")


# ===== Rule 6: concepts — 定义前60字(去空白)重复 =====
def check_duplicate_definitions():
    data = load('concepts.json')
    if not data:
        return

    import re
    # 定义前60字（去空白）相同 → 疑似重复/共用引导语
    def_map = defaultdict(list)
    for i, c in enumerate(data):
        d = c.get('definition', '')
        if len(d) > 20:
            key = re.sub(r'\s+', '', d[:60])
            def_map[key].append((i, c.get('term', '?'), c.get('id', '?')))

    dupes = []
    for d, entries in def_map.items():
        if len(entries) > 1:
            names = [e[1] for e in entries]
            dupes.append((names, d[:60]))

    for names, snippet in dupes:
        warn(f"定义前60字重复: {', '.join(names)} -> \"{snippet}...\"")

    ok(f"Rule 6 (dup defs): {len(dupes)} groups with same 60-char prefix")


# ===== Rule 7 (bonus): politics stem length anomaly =====
def check_politics_stems():
    """题干过短或过长可能表示 OCR 问题"""
    data = load('politics.json')
    if not data:
        return

    stems = [(i, p.get('id', '?'), p.get('stem', '')) for i, p in enumerate(data)]
    too_short = [(i, pid, s) for i, pid, s in stems if len(s) < 15]
    too_long = [(i, pid, s) for i, pid, s in stems if len(s) > 500]

    for idx, pid, stem in too_short[:5]:
        warn(f"题干过短 ({len(stem)}字): politics[{idx}] id={pid}: '{stem}'")
    for idx, pid, stem in too_long[:5]:
        warn(f"题干过长 ({len(stem)}字): politics[{idx}] id={pid}: '{stem[:60]}...'")

    ok(f"Rule 7 (stem length): {len(too_short)} too short, {len(too_long)} too long")


# ===== Rule 8 (bonus): exams type vs subject consistency =====
def check_subject_consistency():
    """method(s) subject 应该对应方法题型，theory 对应理论题型"""
    data = load('exams.json')
    if not data:
        return

    method_types = {'计算', '设计题'}
    theory_types = {'名词解释', '简答', '论述', '辨析', '分析'}

    mismatches = []
    for i, e in enumerate(data):
        subject = (e.get('subject') or '').strip()
        typ = (e.get('type') or '').strip()
        if subject in ('methods', 'method') and typ in theory_types:
            continue  # 方法卷也可以考理论概念题，正常
        if subject == 'theory' and typ in method_types:
            mismatches.append((i, e.get('school', '?'), subject, typ))

    for idx, school, subject, typ in mismatches[:10]:
        warn(f"科目-题型不匹配: exams[{idx}] {school} subject={subject} type={typ}")

    ok(f"Rule 8 (subject/type): {len(mismatches)} mismatches")


# ===== main =====
def main():
    print("=" * 50)
    print("Layer 0-B: Semantic Validation")
    print("=" * 50)

    check_exam_hallucination()
    check_exam_year()
    check_school_year_span()
    check_exam_score()
    check_concept_name_noise()
    check_duplicate_definitions()
    check_politics_stems()
    check_subject_consistency()

    print()
    if ERRORS:
        print(f">>> {len(ERRORS)} ERROR(S), {len(WARNS)} WARNING(S) <<<")
        for e in ERRORS:
            print(f"   [ERROR] {e}")
        for w in WARNS:
            print(f"   [WARN]  {w}")
        sys.exit(1)
    elif WARNS:
        print(f">>> PASS ({len(WARNS)} warning(s), non-fatal) <<<")
        for w in WARNS:
            print(f"   [WARN]  {w}")
        sys.exit(0)
    else:
        print(">>> ALL CHECKS PASSED <<<")
        sys.exit(0)


if __name__ == '__main__':
    main()
