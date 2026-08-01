# -*- coding: utf-8 -*-
"""概念合并方案 Step5：考点粒度变体合并清单

三类合并候选:
  A 归一化精确重复组（连接词/后缀/的差异）→ 确定变体
  B 编辑距离近义（排除反义对 非X~X）→ 真变体
  C 展开性概念（XX的原因/关系/作用）→ 并入主条

原则: 反义对（正式/非正式、现实/非现实、概率/非概率）绝不合并；
     近义但笔记独立考点（机械团结/有机团结）各保留。
输出: D:/workspace/_report_synonym_merge.json/.md（待用户审批）
"""
import os, sys, io, re, json, difflib, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

CONCEPTS = "D:/workspace/sociology-kaoyan-app/web/data/concepts.json"
CLASSIFY = "D:/workspace/_report_classify.json"
OUT_JSON = "D:/workspace/_report_synonym_merge.json"
OUT_MD = "D:/workspace/_report_synonym_merge.md"

ANTI = re.compile(r'^(非|无|去|反|后|有|前|去)')
# 反义修饰词对（一个带X一个带Y → 不同考点，绝不合并）
OPPOSITE = [
    ("宏观", "微观"), ("正式", "非正式"), ("现实", "非现实"), ("直接", "间接"),
    ("内部", "外部"), ("绝对", "相对"), ("利己", "利他"), ("显性", "隐性"),
    ("主观", "客观"), ("内在", "外在"), ("总体", "具体"), ("上层", "下层"),
    ("简单", "复杂"), ("正向", "反向"), ("正向", "负向"), ("积极", "消极"),
]
EXCLUDE_TERMS = {  # 近义但必须独立保留（笔记独立考点）
    "机械团结", "有机团结", "正功能", "反功能", "显功能", "潜功能",
    "正式组织", "非正式组织", "正式群体", "非正式群体", "概率抽样", "非概率抽样",
    "定类", "定序", "定距", "定比", "自变量", "因变量", "主我", "客我",
    "个人", "个人主义（托克维尔）", "个人主义",
    "利己型自杀", "利他型自杀", "宿命型自杀", "失范型自杀",
    "剩余价值", "绝对剩余价值", "相对剩余价值",
    "方法论个体主义", "方法论集体主义", "社会化", "再社会化",
    "角色间的冲突", "角色内的冲突", "社会过程", "社会工作", "教育社会学",
    "社会", "社会学", "社会主义", "社会理论", "社会研究", "社会现象",
    "资本", "资本主义", "结构", "结构主义", "社会舆论控制", "社会控制的度",
}
# 整对排除（编辑距离近义但不同考点）
PAIR_EXCLUDE = {
    frozenset(["个人", "个人主义"]),
    frozenset(["社会结构", "宏观社会结构"]),
    frozenset(["社会结构", "现代社会结构"]),
    frozenset(["现代社会", "现代社会结构"]),
    frozenset(["资本", "资本主义"]),
    frozenset(["结构", "结构主义"]),
    frozenset(["社会", "社会主义"]),
    frozenset(["社会控制", "社会舆论控制"]),
    frozenset(["主文化~亚文化", "主文化~反文化"]),
    frozenset(["主文化与亚文化", "主文化与反文化"]),
    frozenset(["组织的正式结构", "组织的非正式结构"]),
    frozenset(["非抽样误差", "抽样框误差"]),
    frozenset(["结构观察", "非结构式观察"]),
    frozenset(["民族国家", "非民族国家化"]),
    frozenset(["功能性客体系统", "变态功能性客体系统"]),
    frozenset(["现代社会", "现代社会化"]),
    frozenset(["抽样误差", "抽样框误差"]),
    frozenset(["社会工作间接工作方法", "社会工作直接工作方法"]),
    frozenset(["自觉角色", "不自觉角色"]),
    frozenset(["社会系统", "跨社会系统"]),
    frozenset(["行动系统", "外部行动系统"]),
    frozenset(["行动系统", "内部行动系统"]),
    frozenset(["群体关系", "群体内部关系"]),
    frozenset(["精英内部循环", "精英外部循环"]),
    frozenset(["精英循环论", "精英内部循环"]),
    frozenset(["精英循环论", "精英外部循环"]),
}

def is_opposite_pair(a, b):
    """两个归一化词带反义修饰词（宏观/微观、利己/利他）→ 不同考点"""
    for p1, p2 in OPPOSITE:
        if a.startswith(p1) and b.startswith(p2):
            return True
        if a.startswith(p2) and b.startswith(p1):
            return True
    return False

def norm(t):
    t = str(t or '').replace('（','(').replace('）',')')
    t = re.sub(r'\(.*?\)', '', t)
    t = re.sub(r'[　 \t]+', '', t)
    t = re.sub(r'[与和及\-－—]', '~', t)
    # 去后缀仅限 ≥4 字（保护"社会/资本/结构"等 2-3 字核心词不被削成同一键）
    if len(t) >= 4:
        t = re.sub(r'[型性式]?(主义|论|理论|学说|思想|概念|研究|类型|体系|模式|现象|学)$', '', t)
    t = t.strip(' \t\n*#△^←→√※.·、—-—:："“”\'‘’')
    return t

def _strip_mod(t):
    """去掉反义前缀 + 式/性/化 修饰，用于反义对宽松比较"""
    t = re.sub(r'^(非|无|去|反|后|有|前)', '', t)
    t = re.sub(r'[式性化]', '', t)
    return t

def is_antipair(a, b):
    """反义对判定：一个带 非/无/去/反/后 前缀另一个不带（宽松：去修饰后比较）"""
    for x, y in ((a, b), (b, a)):
        if ANTI.match(x):
            xr = _strip_mod(x)
            yr = _strip_mod(y)
            if xr == yr or (len(xr) >= 3 and len(yr) >= 3 and (xr in yr or yr in xr)):
                return True
    return False

def main():
    cs = json.load(open(CONCEPTS, encoding='utf-8'))
    classify = json.load(open(CLASSIFY, encoding='utf-8'))
    cls_by_id = {r['id']: r['classification'] for r in classify}
    cmap = {c['id']: c for c in cs}

    # 排除碎片/垃圾（step2 已删）
    delete_terms = {r['term'] for r in json.load(open("D:/workspace/_report_delete_fragments.json", encoding='utf-8'))}
    active = [c for c in cs if c['term'] not in delete_terms]

    # A 归一化精确重复
    exact = collections.defaultdict(list)
    for c in active:
        n = norm(c['term'])
        if len(n) >= 2:
            exact[n].append(c)
    groups = []
    for n, items in exact.items():
        uniq = {c['term'] for c in items}
        if len(uniq) > 1:
            if any(t in EXCLUDE_TERMS for t in uniq):
                continue  # 含超泛化词/独立考点 → 不自动合并
            groups.append({"type": "A精确", "key": n, "members": items})

    # B 近义（跨组）：编辑距离 ≥0.85 + 强过滤；只对 ≥4 字 key（短 key 靠 A 精确）
    keys = list(exact.keys())
    added = set()
    for i in range(len(keys)):
        for j in range(i+1, len(keys)):
            a, b = keys[i], keys[j]
            if len(a) < 4 or len(b) < 4:
                continue
            if abs(len(a)-len(b)) > 4 or min(len(a), len(b)) < 3:
                continue
            if is_antipair(a, b) or is_opposite_pair(a, b):
                continue
            if frozenset([a, b]) in PAIR_EXCLUDE:
                continue
            r = difflib.SequenceMatcher(None, a, b).ratio()
            if r < 0.80:
                continue
            members = exact[a] + exact[b]
            terms = {c['term'] for c in members}
            if terms - EXCLUDE_TERMS != terms and len(terms & EXCLUDE_TERMS) == len(terms):
                continue  # 全在排除表
            if any(t in EXCLUDE_TERMS for t in terms):
                continue
            gkey = frozenset([a, b])
            if gkey in added:
                continue
            added.add(gkey)
            groups.append({"type": "B近义", "key": f"{a} ~ {b}", "members": members})

    # C 展开性概念（单独列出，并入其主条）
    SUFFIX = re.compile(r'的(原因|根源|因素|影响|作用|关系|类型|程度|强度|过程|构成|形成|条件|后果|分类|特点|功能|意义|性质|本质|来源|变迁|发展|产生|方式|结构|层次|问题|结果|前提|基础|机制)$')
    expanded = [c for c in active if SUFFIX.search(c['term'])]

    # 每组选 keeper：正典优先 > 定义最长 > 无后缀优先
    def keeper_rank(c):
        cls = cls_by_id.get(c['id'], '')
        rank = 0
        if cls in ('CANON_CORE',): rank += 10
        elif cls in ('CANON_XMIND', 'CANON_HIGHFREQ'): rank += 8
        elif cls == 'REVIEW': rank += 5
        return (rank, len(c.get('definition','') or ''), len(c['term']))

    out_groups = []
    total_merge = 0
    for g in groups:
        members = sorted(g['members'], key=keeper_rank, reverse=True)
        keeper = members[0]
        merged = members[1:]
        if not merged:
            continue
        total_merge += len(merged)
        out_groups.append({
            "type": g['type'], "key": g['key'],
            "keeper": {"id": keeper['id'], "term": keeper['term'], "chapter": keeper.get('chapter',''),
                       "def_len": len(keeper.get('definition','') or '')},
            "merged": [{"id": m['id'], "term": m['term'], "chapter": m.get('chapter',''),
                        "def_len": len(m.get('definition','') or '')} for m in merged],
        })

    json.dump({"groups": out_groups, "expanded": [c['term'] for c in expanded]},
              open(OUT_JSON, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    L = [f"# Step5 考点粒度合并清单", f"\n变体组 {len(out_groups)}，合并 {total_merge} 条；展开概念 {len(expanded)} 条", ""]
    L.append("## A/B 变体组")
    for g in out_groups:
        L.append(f"\n**[{g['type']}] {g['key']}** → 保留「{g['keeper']['term']}」({g['keeper']['def_len']}字)")
        L.append(f"   合并: {', '.join(m['term'] for m in g['merged'])}")
    L.append(f"\n## C 展开性概念（并入对应主条）")
    for t in expanded:
        L.append(f"- {t}")
    with open(OUT_MD, 'w', encoding='utf-8') as f:
        f.write('\n'.join(L))

    print(f"变体组: {len(out_groups)} 组, 合并 {total_merge} 条")
    print(f"展开概念: {len(expanded)} 条")
    print(f"预计收敛: {len(active) - total_merge - len(expanded)} 条")
    print(f"→ {OUT_JSON}\n→ {OUT_MD}")

if __name__ == '__main__':
    main()
