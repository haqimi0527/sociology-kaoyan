# -*- coding: utf-8 -*-
"""自检统一出口：audit_runner

把 Layer A（数据完整性）/ B（语义）/ C（结构铁律）/ D（taxonomy）全部规则
收进一个 runner，产出结构化 JSON + 人读 MD，退出码带语义。

用法（Git Bash）:
  python pipeline/audit_runner.py                # 默认 --report
  python pipeline/audit_runner.py --strict       # 全部 WARN 视为 blocker
  python pipeline/audit_runner.py --check-structure  # 单跑结构规则
  python pipeline/audit_runner.py --all          # 聚合 A/B/C/D 全量（同默认+明细）

退出码:
  0 = 真PASS（无 ERROR 且无 blocker WARN）
  1 = FAIL（有 ERROR）
  2 = REVIEW（无 ERROR 但有 blocker WARN 须人审）
"""
import json, os, sys, io, re
from collections import Counter, defaultdict

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, 'web', 'data')
CONFIG_DIR = os.path.join(BASE, 'pipeline', 'config')
UTILS_DIR = os.path.join(BASE, 'pipeline', 'utils')
sys.path.insert(0, BASE)
sys.path.insert(0, UTILS_DIR)

REPORT_JSON = os.path.join(os.environ.get('TEMP_DIR', 'D:/workspace'), '_audit_report.json')
REPORT_MD = os.path.join(os.environ.get('TEMP_DIR', 'D:/workspace'), '_audit_report.md')

# ============ 配置加载 ============

def load_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)

RULES = load_json(os.path.join(CONFIG_DIR, 'audit_rules.json'))
ALIAS = load_json(os.path.join(CONFIG_DIR, 'translation_aliases.json'))
BLOCKER_WARNS = set(RULES['exit_policy']['blocker_warns'])

# 正典学者清单（from translation_aliases canonical keys）
CANONICAL = set(ALIAS['canonical'].keys())
# 正典别名→正典名（最长优先匹配）
ALIAS_TO_CANON = {}
for canon, aliases in ALIAS['canonical'].items():
    for a in aliases:
        ALIAS_TO_CANON[a] = canon
    ALIAS_TO_CANON[canon] = canon
ALIAS_KEYS = sorted(ALIAS_TO_CANON.keys(), key=len, reverse=True)
SCHOOL_ALIASES = {k: v for k, v in ALIAS['school_aliases'].items() if not k.startswith('_')}
NOISE_STRIP = ALIAS['proponent_noise']['strip']
NOISE_SPLIT = ALIAS['proponent_noise']['split']
NOISE_REPLACE = {k: v for k, v in ALIAS['proponent_noise']['full_replace'].items()}


# ============ finding ============

class Finding:
    __slots__ = ('rule', 'category', 'severity', 'blocker', 'id', 'term',
                 'chapter', 'proponent', 'suggestion', 'detail')

    def __init__(self, rule, category, severity, blocker, id='', term='',
                 chapter='', proponent='', suggestion='', detail=''):
        self.rule = rule
        self.category = category
        self.severity = severity
        self.blocker = blocker
        self.id = id
        self.term = term
        self.chapter = chapter
        self.proponent = proponent
        self.suggestion = suggestion
        self.detail = detail

    def to_dict(self):
        return {
            'rule': self.rule, 'category': self.category, 'severity': self.severity,
            'blocker': self.blocker, 'id': self.id, 'term': self.term,
            'chapter': self.chapter, 'proponent': self.proponent,
            'suggestion': self.suggestion, 'detail': self.detail,
        }


FINDINGS = []


def add(rule, category, severity, term='', chapter='', proponent='',
        suggestion='', detail='', id=''):
    """加一条 finding；severity 从注册表覆盖（注册表优先）。"""
    meta = RULES['rules'].get(rule, {})
    sev = meta.get('severity', severity)
    blocker = bool(meta.get('blocker', False))
    if not suggestion and 'suggestion_template' in meta:
        suggestion = meta['suggestion_template']
    FINDINGS.append(Finding(rule, category, sev, blocker, id=id, term=term,
                            chapter=chapter, proponent=proponent,
                            suggestion=suggestion, detail=detail))


# ============ 译名归一 ============

def clean_noise(s):
    """去 proponent 注解噪声（只去确认名单，不做通用括号删除）"""
    s = s or ''
    for noise in NOISE_STRIP:
        s = s.replace(noise, '')
    return s.strip(' 　，、；。')


def normalize_proponent(prop_str):
    """归一 proponent → (canonical 学者集合, unmapped 名字集合)

    1) 整值 full_replace 替换
    2) 去注解噪声
    3) 按分隔符拆多作者
    4) 逐段最长别名匹配 canonical；未命中 → unmapped
    """
    prop_str = (prop_str or '').strip()
    if prop_str in NOISE_REPLACE:
        prop_str = NOISE_REPLACE[prop_str]
    prop_str = clean_noise(prop_str)
    if not prop_str:
        return set(), set()

    # 按分隔符拆分
    pieces = [prop_str]
    for sep in NOISE_SPLIT:
        new_pieces = []
        for p in pieces:
            new_pieces.extend(p.split(sep))
        pieces = new_pieces
    pieces = [p.strip(' 　，、；。()（）') for p in pieces]
    pieces = [p for p in pieces if p]

    canon_found = set()
    unmapped = set()
    for p in pieces:
        matched = None
        for alias in ALIAS_KEYS:
            if alias in p:
                matched = ALIAS_TO_CANON[alias]
                break
        if matched:
            canon_found.add(matched)
        else:
            unmapped.add(p)
    return canon_found, unmapped


def normalize_school_name(school):
    """学派别名 → 正典学派名"""
    return SCHOOL_ALIASES.get(school, school)


# ============ 规则实现（Layer A: 数据完整性） ============

def check_duplicate_id(concepts):
    ids = [c.get('id') for c in concepts]
    for i, cnt in Counter(ids).items():
        if cnt > 1 and i:
            add('duplicate_id', 'data', 'ERROR', term=i, detail=f'id {i} 出现 {cnt} 次')


def check_missing_field(concepts):
    for i, c in enumerate(concepts):
        for field in ['id', 'term', 'definition']:
            if field not in c or not c[field]:
                add('missing_field', 'data', 'ERROR', term=str(c.get('term', '?'))[:30],
                    detail=f'concepts[{i}] 缺 {field}')


# ============ Layer B: 语义 ============

def check_narrative_start(concepts):
    for c in concepts:
        d = (c.get('definition') or '').strip()
        if d and d[:1] in '在根据随着关于从对':
            add('narrative_start', 'semantic', 'WARN', term=c.get('term', ''),
                chapter=c.get('chapter', ''), id=c.get('id', ''),
                detail=f'定义开头: {d[:40]}')


def check_def_length(concepts):
    from pipeline.utils.concept_utils import is_fragment_term
    for c in concepts:
        d = (c.get('definition') or '').strip()
        term = c.get('term', '')
        if len(d) < 15:
            frag = is_fragment_term(term)
            kind = '碎片' if frag else '真概念短定义(KEEP/人审)'
            add('def_too_short_classified', 'semantic', 'WARN', term=term,
                chapter=c.get('chapter', ''), id=c.get('id', ''),
                detail=f'定义{len(d)}字: {d} [分类:{kind}]')
        elif len(d) > 500:
            add('def_too_long', 'semantic', 'WARN', term=term,
                chapter=c.get('chapter', ''), id=c.get('id', ''),
                detail=f'定义{len(d)}字，超500')
        elif len(d) >= 20 and '。' not in d:
            add('def_no_period', 'semantic', 'WARN', term=term,
                chapter=c.get('chapter', ''), id=c.get('id', ''), detail='无句号')


def check_textbook_language(concepts):
    for c in concepts:
        d = (c.get('definition') or '')
        if any(w in d[:120] for w in ['本章', '本书', '该书']):
            add('textbook_language', 'semantic', 'WARN', term=c.get('term', ''),
                chapter=c.get('chapter', ''), id=c.get('id', ''),
                detail=f'教材语言: {d[:50]}')


def check_no_source_text(concepts):
    for c in concepts:
        if not (c.get('source_text') or '').strip():
            add('no_source_text', 'semantic', 'INFO', term=c.get('term', ''),
                chapter=c.get('chapter', ''), id=c.get('id', ''))


def check_term_is_chapter(concepts):
    for c in concepts:
        t = c.get('term', '')
        if re.match(r'^(第[一二三四五六七八九十\d]+[章节篇]|[一二三四五六七八九十\d]+[、.\)）]|\d+[\.\、])', t):
            add('term_is_chapter', 'semantic', 'ERROR', term=t,
                chapter=c.get('chapter', ''), id=c.get('id', ''))


def check_term_fragment(concepts):
    from pipeline.utils.concept_utils import is_fragment_term, classify_fragment
    for c in concepts:
        t = (c.get('term') or '').strip()
        if classify_fragment(t):
            add('term_fragment', 'semantic', 'WARN', term=t,
                chapter=c.get('chapter', ''), id=c.get('id', ''),
                detail=f'碎片规则: {classify_fragment(t)}')
        elif is_fragment_term(t):
            add('term_fragment', 'semantic', 'WARN', term=t,
                chapter=c.get('chapter', ''), id=c.get('id', ''), detail='碎片特征')


def check_term_norm_dup(concepts):
    norm = defaultdict(list)
    for c in concepts:
        t = (c.get('term') or '').strip()
        nt = re.sub(r'[（）()\s,，。、；;：:]', '', t)
        if nt:
            norm[nt].append(t)
    for nt, ts in norm.items():
        if len(ts) > 1 and len(set(ts)) > 1:
            add('term_norm_dup', 'semantic', 'WARN',
                term=', '.join(sorted(set(ts))), detail=f'norm后: {nt} x{len(set(ts))}')


def check_duplicate_def_prefix(concepts):
    # 定义前60字查重（白名单豁免）
    approved_terms = set()
    approved_path = os.path.join(BASE, 'tests', 'config', 'approved_def_prefix_dups.json')
    if os.path.exists(approved_path):
        try:
            for g in load_json(approved_path).get('approved', []):
                approved_terms.update(g.get('terms', []))
        except Exception:
            pass
    groups = defaultdict(list)
    for c in concepts:
        d = (c.get('definition') or '')
        if len(d) >= 20:
            key = re.sub(r'\s+', '', d[:60])
            groups[key].append(c)
    for key, cs in groups.items():
        if len(cs) > 1:
            terms = [c.get('term', '') for c in cs]
            if all(t in approved_terms for t in terms):
                continue
            add('duplicate_def_prefix', 'data', 'ERROR', term=', '.join(terms),
                detail=f'定义前60字重复: {key[:30]}... x{len(cs)}')


# ============ Layer C: 结构铁律 ============

def parse_chapter(ch):
    return [p for p in (ch or '').split('/') if p]


def check_chapter_top_whitelist(concepts):
    for c in concepts:
        parts = parse_chapter(c.get('chapter'))
        if parts and parts[0] not in ('理论', '方法', '概论', '未分类'):
            add('chapter_top_whitelist', 'structure', 'ERROR', term=c.get('term', ''),
                chapter=c.get('chapter', ''), id=c.get('id', ''),
                detail=f'顶层: {parts[0]}')


def check_empty_chapter(concepts):
    for c in concepts:
        if not (c.get('chapter') or '').strip():
            add('empty_chapter', 'structure', 'ERROR', term=c.get('term', ''),
                id=c.get('id', ''))


def check_structure(concepts, taxonomy=None):
    """3段/2段 chapter 结构检查：scholar_dir_3seg / era_mismatch /
    school_direct / unknown_3seg_name"""
    # 正典学派名（从 taxonomy theory 域顶层键提取；无 taxonomy 时退回别名表）
    canonical_schools = set()
    if taxonomy:
        for era_data in (taxonomy.get('theory', {}) or {}).values():
            canonical_schools.update(era_data.keys())
    canonical_schools.update(SCHOOL_ALIASES.values())
    canonical_schools.update({'其他古典学者', '其他现代学者', '其他当代学者',
                              '古典综合', '现代综合', '当代综合', '理论综合',
                              '理论对比', '理论前沿'})

    for c in concepts:
        ch = c.get('chapter', '')
        parts = parse_chapter(ch)
        if not parts or parts[0] != '理论':
            continue
        term = c.get('term', '')
        cid = c.get('id', '')

        if len(parts) == 3:
            era, name = parts[1], parts[2]
            if name in CANONICAL:
                # 学者直挂缺学派层
                add('scholar_dir_3seg', 'structure', 'WARN', term=term, chapter=ch,
                    id=cid, detail=f'学者直挂缺学派层: {name} 在 {era}')
            elif normalize_school_name(name) in canonical_schools:
                # 学派直挂（归一后是正典学派）
                add('school_direct_needs_scholar', 'structure', 'WARN', term=term,
                    chapter=ch, id=cid, detail=f'学派直挂: {name}')
            elif name not in canonical_schools:
                # 未知3段名
                add('unknown_3seg_name', 'structure', 'WARN', term=term, chapter=ch,
                    id=cid, detail=f'未知3段名: {name}')
        elif len(parts) == 2:
            if parts[1] in CANONICAL:
                add('scholar_dir_3seg', 'structure', 'WARN', term=term, chapter=ch,
                    id=cid, detail=f'2段学者直挂: {parts[1]}')


def check_era_mismatch(concepts, taxonomy):
    """chapter 时期 vs 正典时期（需 taxonomy 时期映射）"""
    # 正典时期名（taxonomy 键名，全名）→ 短名
    era_full_to_short = {}
    if taxonomy:
        for k in taxonomy.get('theory', {}):
            era_full_to_short[k] = re.sub(r'\s*\(.*?\)\s*$', '', k)
    # 兜底：短名 → 短名
    for short in ('古典时期', '现代时期', '当代时期', '综合'):
        era_full_to_short.setdefault(short, short)

    for c in concepts:
        parts = parse_chapter(c.get('chapter'))
        if not parts or parts[0] != '理论' or len(parts) < 3:
            continue
        era, name = parts[1], parts[2]
        if name not in CANONICAL:
            continue
        # 正典里该学者的正确时期
        canon_era = None
        for full_era, era_data in (taxonomy.get('theory', {}) if taxonomy else {}).items():
            for sch, sch_data in era_data.items():
                if name in sch_data.get('scholars', {}):
                    canon_era = era_full_to_short.get(full_era, full_era)
                    break
            if canon_era:
                break
        if canon_era and era != canon_era and era in era_full_to_short.values():
            add('era_mismatch', 'structure', 'WARN', term=c.get('term', ''),
                chapter=c.get('chapter', ''), id=c.get('id', ''),
                detail=f'时期 {era} ≠ 正典 {canon_era}')


# ============ Layer D: taxonomy ============

def collect_taxonomy_ids(taxonomy):
    theory_ids, methods_ids, intro_ids = set(), set(), set()
    for era_data in (taxonomy.get('theory', {}) or {}).values():
        for sch_data in era_data.values():
            for sdata in sch_data.get('scholars', {}).values():
                theory_ids.update(sdata.get('concepts', []))
            theory_ids.update(sch_data.get('ungrouped_concepts', []))
    for phase_data in (taxonomy.get('methods', {}) or {}).values():
        for cdata in phase_data.get('categories', {}).values():
            methods_ids.update(cdata.get('concepts', []))
    for tdata in (taxonomy.get('intro', {}) or {}).values():
        intro_ids.update(tdata.get('concepts', []))
    return theory_ids, methods_ids, intro_ids


def check_taxonomy(concepts, taxonomy):
    if not taxonomy:
        return
    cmap = {c['id']: c for c in concepts}
    theory_ids, methods_ids, intro_ids = collect_taxonomy_ids(taxonomy)
    classified = theory_ids | methods_ids | intro_ids
    all_ids = set(c['id'] for c in concepts)

    # unclassified
    unclass = all_ids - classified
    for cid in unclass:
        c = cmap.get(cid, {})
        add('unclassified', 'taxonomy', 'ERROR', term=c.get('term', cid),
            chapter=c.get('chapter', ''), id=cid)

    # 跨域重复
    overlap = (theory_ids & methods_ids) | (theory_ids & intro_ids) | (methods_ids & intro_ids)
    for cid in overlap:
        c = cmap.get(cid, {})
        add('cross_domain_dup', 'taxonomy', 'ERROR', term=c.get('term', cid), id=cid)

    # theory-in-methods / methods-in-theory
    theory_signals = ['古典时期', '现代时期', '当代时期', '韦伯', '涂尔干', '马克思',
                      '齐美尔', '帕森斯', '布迪厄', '福柯', '吉登斯', '哈贝马斯', '常人方法学', '现象学']
    for cid in methods_ids:
        c = cmap.get(cid)
        if c:
            ch = c.get('chapter', '')
            matched = [s for s in theory_signals if s in ch]
            if matched:
                add('theory_in_methods', 'taxonomy', 'ERROR', term=c.get('term', ''),
                    chapter=ch, id=cid, detail=f'理论信号 {matched}')
    for cid in theory_ids | intro_ids:
        c = cmap.get(cid)
        if c:
            ch = c.get('chapter', '')
            if '研究方法' in ch or '社会学研究方法' in ch or ch.startswith('方法/'):
                add('methods_in_theory', 'taxonomy', 'ERROR', term=c.get('term', ''),
                    chapter=ch, id=cid)

    # 空节点
    for era_data in (taxonomy.get('theory', {}) or {}).values():
        for sch, sch_data in era_data.items():
            for sname, sdata in sch_data.get('scholars', {}).items():
                if not sdata.get('concepts'):
                    add('empty_taxonomy_node', 'taxonomy', 'ERROR',
                        detail=f'学者 {sname} 0 概念')


# ============ Layer D: proponent 一致性 ============

def get_assigned_scholar(cid, taxonomy):
    """从 taxonomy 反查概念挂靠的正典学者"""
    for era_data in (taxonomy.get('theory', {}) or {}).values():
        for sch, sch_data in era_data.items():
            for sname, sdata in sch_data.get('scholars', {}).items():
                if cid in sdata.get('concepts', []):
                    return sname
    return None


def check_proponent(concepts, taxonomy):
    """proponent-mismatch + proponent-noise + proponent-chapter-consistency"""
    cmap = {c['id']: c for c in concepts}
    for c in concepts:
        prop = (c.get('proponent') or '').strip()
        if not prop:
            continue
        cid = c.get('id', '')
        canon_found, unmapped = normalize_proponent(prop)

        # proponent 噪声（残片/非人名）
        raw = prop
        if raw in NOISE_REPLACE or any(n in raw for n in NOISE_STRIP):
            add('proponent_noise', 'semantic', 'WARN', term=c.get('term', ''),
                chapter=c.get('chapter', ''), id=cid, proponent=raw,
                detail=f'含噪声')

        # chapter 里的学者
        parts = parse_chapter(c.get('chapter'))
        chapter_scholars = set()
        for p in parts:
            if p in CANONICAL:
                chapter_scholars.add(p)
            else:
                for alias in ALIAS_KEYS:
                    if p and alias in p:
                        chapter_scholars.add(ALIAS_TO_CANON[alias])
                        break

        # proponent 未命中 chapter 任一学者 → 一致性
        if canon_found and chapter_scholars and not (canon_found & chapter_scholars):
            add('proponent_chapter_consistency', 'taxonomy', 'WARN',
                term=c.get('term', ''), chapter=c.get('chapter', ''), id=cid,
                proponent=prop,
                detail=f'proponent[{",".join(sorted(canon_found))}] 未在 chapter {parts}')

        # taxonomy assigned vs proponent（译名归一后）
        if taxonomy:
            assigned = get_assigned_scholar(cid, taxonomy)
            if assigned and assigned in CANONICAL and canon_found and assigned not in canon_found:
                add('proponent_mismatch', 'taxonomy', 'WARN', term=c.get('term', ''),
                    chapter=c.get('chapter', ''), id=cid, proponent=prop,
                    detail=f'assigned={assigned} but proponent={prop}')


# ============ 报告输出 ============

def compute_exit_code(findings, strict=False):
    errors = [f for f in findings if f.severity == 'ERROR']
    if errors:
        return 1
    blockers = [f for f in findings if f.blocker and f.severity == 'WARN']
    if blockers or strict:
        return 2
    return 0


def write_report(findings, out_json, out_md):
    entries = [f.to_dict() for f in findings]
    by_severity = Counter(f.severity for f in findings)
    by_rule = Counter(f.rule for f in findings)
    by_category = Counter(f.category for f in findings)
    blockers = [e for e in entries if e['severity'] == 'ERROR' or (e['blocker'] and e['severity'] == 'WARN')]

    report = {
        'summary': {
            'total': len(entries),
            'by_severity': dict(by_severity),
            'by_rule': dict(by_rule.most_common()),
            'by_category': dict(by_category),
            'blocker_count': len(blockers),
        },
        'blockers': blockers,
        'entries': entries,
    }
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=1)

    # MD
    lines = ['# 数据审计报告', '']
    lines.append(f'**总 finding: {len(entries)}** | ERROR: {by_severity.get("ERROR",0)} '
                 f'| WARN: {by_severity.get("WARN",0)} | INFO: {by_severity.get("INFO",0)}')
    lines.append(f'**需处理(blocker): {len(blockers)}**\n')
    lines.append('## 需处理清单（ERROR + blocker WARN）\n')
    if blockers:
        lines.append('| rule | severity | term | chapter | suggestion | detail |')
        lines.append('|---|---|---|---|---|---|')
        for e in blockers:
            lines.append(f"| {e['rule']} | {e['severity']} | {e['term'][:25]} | "
                         f"{e['chapter'][:30]} | {e['suggestion'][:40]} | {e['detail'][:40]} |")
    else:
        lines.append('*无*\n')
    lines.append('\n## 参考区（普通 WARN + INFO）\n')
    refs = [e for e in entries if not (e['severity'] == 'ERROR' or (e['blocker'] and e['severity'] == 'WARN'))]
    if refs:
        lines.append('| rule | severity | 数量 |')
        lines.append('|---|---|---|')
        rc = Counter((e['rule'], e['severity']) for e in refs)
        for (r, s), n in sorted(rc.items()):
            lines.append(f'| {r} | {s} | {n} |')
    else:
        lines.append('*无*')
    lines.append('\n## 按规则分布\n')
    for r, n in by_rule.most_common():
        lines.append(f'- {r}: {n}')
    with open(out_md, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f'  报告 → {out_json}')
    print(f'  摘要 → {out_md}')


# ============ main ============

def main():
    args = sys.argv[1:]
    strict = '--strict' in args
    check_structure_only = '--check-structure' in args

    concepts = load_json(os.path.join(DATA_DIR, 'concepts.json'))
    tax_path = os.path.join(DATA_DIR, 'concept-taxonomy.json')
    taxonomy = load_json(tax_path) if os.path.exists(tax_path) else None

    if check_structure_only:
        check_structure(concepts, taxonomy)
        check_era_mismatch(concepts, taxonomy)
        check_chapter_top_whitelist(concepts)
        check_empty_chapter(concepts)
    else:
        # Layer A
        check_duplicate_id(concepts)
        check_missing_field(concepts)
        check_duplicate_def_prefix(concepts)
        # Layer B
        check_narrative_start(concepts)
        check_def_length(concepts)
        check_textbook_language(concepts)
        check_no_source_text(concepts)
        check_term_is_chapter(concepts)
        check_term_fragment(concepts)
        check_term_norm_dup(concepts)
        # Layer C
        check_chapter_top_whitelist(concepts)
        check_empty_chapter(concepts)
        check_structure(concepts, taxonomy)
        check_era_mismatch(concepts, taxonomy)
        # Layer D
        check_taxonomy(concepts, taxonomy)
        check_proponent(concepts, taxonomy)

    write_report(FINDINGS, REPORT_JSON, REPORT_MD)

    code = compute_exit_code(FINDINGS, strict=strict)
    by_sev = Counter(f.severity for f in FINDINGS)
    print(f'\n=== 审计结果: ERROR={by_sev.get("ERROR",0)} WARN={by_sev.get("WARN",0)} '
          f'INFO={by_sev.get("INFO",0)} → exit {code} ===')
    if code == 0:
        print('[PASS] 0 ERROR / 0 blocker WARN')
    elif code == 1:
        print('[FAIL] 有 ERROR，见 D:/workspace/_audit_report.md')
    else:
        print('[REVIEW] 0 ERROR 但有 blocker WARN 须人审，见 D:/workspace/_audit_report.md')
    return code


if __name__ == '__main__':
    sys.exit(main())
