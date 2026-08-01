# -*- coding: utf-8 -*-
"""概念合并方案 Step1：三档四分类初筛

档位:
  CANON_CORE    - term 归一化 ∈ 正典清单 S0/A 级（核心笔记概念）→ 保留
  CANON_XMIND   - term 归一化 ∈ 正典清单 B 级（南大 XMind，含框架噪声）→ 审核保留
  CANON_HIGHFREQ- 不在正典 但 exam_frequency=high → 保留(真题兜底)
  REVIEW        - 完全不在正典 且 非高频 → 待审区（细分来源: 空源/教材/笔记lcwiki/其他）

输出: D:/workspace/_report_classify.json/.md（只读，不改 concepts.json）
"""
import os, sys, io, re, json, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

CONCEPTS = "D:/workspace/sociology-kaoyan-app/web/data/concepts.json"
CANON = "D:/workspace/_canonical_names.json"
OUT_JSON = "D:/workspace/_report_classify.json"
OUT_MD = "D:/workspace/_report_classify.md"

# 变体后缀归一（拟剧论→戏剧、精英循环论→精英循环）
SUFFIXES = ("理论", "学说", "思想", "主义", "概念", "研究", "论", "观")

def norm(t):
    t = str(t or "").replace('（', '(').replace('）', ')')
    t = re.sub(r'\(.*?\)', '', t)
    t = re.sub(r'[　 \t]+', '', t)
    t = t.strip(' \t\n*#△^←→√※.·、—-—:："“”\'‘’')
    return t

def norm_variant(t):
    """去括号+去变体后缀"""
    n = norm(t)
    for suf in SUFFIXES:
        if n.endswith(suf) and len(n) > len(suf) + 1:
            return n[:-len(suf)]
    return n

def load():
    cs = json.load(open(CONCEPTS, encoding='utf-8'))
    canon = json.load(open(CANON, encoding='utf-8'))
    # 正典分档
    core = {}  # norm_variant -> term
    xmind = {}
    for x in canon:
        prio = x.get('priority', '')
        t = x.get('term', '')
        n = norm_variant(t)
        if n and len(n) >= 2:
            if prio in ('S0', 'A'):
                core.setdefault(n, t)
            else:
                xmind.setdefault(n, t)
    return cs, core, xmind

def src_class(source):
    """待审区来源细分"""
    s = (source or "").strip()
    if not s:
        return "空源"
    if "杨善华_下卷" in s:
        return "教材杨下卷"
    if "杨善华_笔记" in s:
        return "笔记杨"
    if "lcwiki" in s:
        return "lcwiki"
    if re.search(r"笔记|名词解释|背诵|考点|人大_|南大|华中师|风笑天|XMind|论文映射", s):
        return "笔记/lcwiki"
    return "教材其他"

def main():
    cs, core, xmind = load()
    # 反向查 core/xmind 的 term（用于 reason）
    core_rev = {v: k for k, v in core.items()}
    xmind_rev = {v: k for k, v in xmind.items()}

    rows = []
    stats = collections.Counter()
    for c in cs:
        term = c.get('term', '')
        n = norm(term)
        nv = norm_variant(term)
        source = c.get('source_text', '') or ''
        freq = c.get('exam_frequency', '') or c.get('frequency', '')
        deflen = len(c.get('definition', '') or '')

        if nv in core or n in core:
            cls = "CANON_CORE"
            reason = f"核心笔记概念: {core.get(nv, core.get(n, ''))}"
        elif nv in xmind or n in xmind:
            cls = "CANON_XMIND"
            reason = f"南大XMind笔记: {xmind.get(nv, xmind.get(n, ''))}"
        elif freq == 'high':
            cls = "CANON_HIGHFREQ"
            reason = "真题高频(不在正典清单)"
        else:
            cls = "REVIEW"
            reason = f"待审·{src_class(source)}"

        stats[cls] += 1
        rows.append({
            "id": c.get('id', ''),
            "term": term,
            "chapter": c.get('chapter', ''),
            "source_text": source,
            "exam_frequency": freq,
            "proponent": c.get('proponent', ''),
            "definition_len": deflen,
            "classification": cls,
            "reason": reason,
        })

    with open(OUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)

    # 待审区细分
    review = [r for r in rows if r['classification'] == 'REVIEW']
    rev_src = collections.Counter(r['source_text'][:18] if r['source_text'] else '空源' for r in review)

    # MD
    L = ["# 概念合并 Step1 四分类初筛", ""]
    L.append(f"总数: {len(cs)}")
    L.append(f"CANON_CORE(核心笔记): {stats['CANON_CORE']}")
    L.append(f"CANON_XMIND(南大XMind): {stats['CANON_XMIND']}")
    L.append(f"CANON_HIGHFREQ(真题高频): {stats['CANON_HIGHFREQ']}")
    L.append(f"REVIEW(待审): {len(review)}")
    L.append(f"\n保底保留 = {stats['CANON_CORE']} + {stats['CANON_XMIND']} + {stats['CANON_HIGHFREQ']} = {stats['CANON_CORE']+stats['CANON_XMIND']+stats['CANON_HIGHFREQ']}")
    L.append(f"\n## 待审区来源分布")
    for s, n in rev_src.most_common(15):
        L.append(f"- {n:4d}  {s}")
    L.append(f"\n## 待审区前 50 条")
    for r in review[:50]:
        L.append(f"- [{r['classification']}] {r['term']} | src={r['source_text'][:20] or '空'} | def={r['definition_len']}字 | freq={r['exam_frequency']}")
    with open(OUT_MD, 'w', encoding='utf-8') as f:
        f.write('\n'.join(L))

    print(f"总数: {len(cs)}")
    for k in ("CANON_CORE", "CANON_XMIND", "CANON_HIGHFREQ", "REVIEW"):
        print(f"  {k}: {stats[k]}")
    print(f"保底保留: {stats['CANON_CORE']+stats['CANON_XMIND']+stats['CANON_HIGHFREQ']}")
    print(f"→ {OUT_JSON}\n→ {OUT_MD}")

if __name__ == '__main__':
    main()
