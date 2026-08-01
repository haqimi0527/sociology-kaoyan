# -*- coding: utf-8 -*-
"""筛选 AI 语义检测结果：提取高置信真变体（reason 明确引用定义/同一译名）

高置信规则：reason 含 定义中/亦称/又称/别名/同一译名/不同译名/不同写法/简称/同一概念
排除误报：reason 含 但（转折）/两个/分别/两者/对应/包括/组成部分/相对/对立/类型
输出 D:/workspace/_ai_merge_confirmed.txt
"""
import json, io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

IN = "D:/workspace/_ai_semantic_merge.json"
OUT = "D:/workspace/_ai_merge_confirmed.txt"
CONCEPTS = "D:/workspace/sociology-kaoyan-app/web/data/concepts.json"

HIGH = re.compile(r'亦称|又称|别名|同一译名|不同译名|不同写法|简称|定义中|同一概念的不同表述|同一概念的不同名称|同一概念的不同译名|同一概念的不同写法')
LOW = re.compile(r'但|两个|分别|两者|对应|包括|组成部分|相对|对立|类型|前者|后者|之一|其中一个|子|整体|部分|框架|维度|方面|视角|组成部分')

def main():
    data = json.load(open(IN, encoding='utf-8'))
    cs = json.load(open(CONCEPTS, encoding='utf-8'))
    terms = {c['term'] for c in cs}

    confirmed, rejected = [], []
    for g in data['candidates']:
        reason = g.get('reason', '')
        terms_in = g.get('terms', [])
        # 去重 + 只保留库内存在的
        uniq = [t for t in dict.fromkeys(terms_in) if t in terms]
        if len(uniq) < 2:
            continue
        if HIGH.search(reason) and not LOW.search(reason):
            confirmed.append((uniq, reason, g.get('domain', '')))
        else:
            rejected.append((uniq, reason))

    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(f"高置信候选: {len(confirmed)}\n\n")
        for t, r, d in confirmed:
            f.write(f"[{d}] {'/'.join(t)} | {r}\n")
        f.write(f"\n\n排除(疑误报/需人工): {len(rejected)}\n")
        for t, r in rejected[:60]:
            f.write(f"  {'/'.join(t)} | {r[:60]}\n")

    print(f"高置信候选: {len(confirmed)}")
    for t, r, d in confirmed:
        print(f"  [{d}] {'/'.join(t)}")
    print(f"\n排除: {len(rejected)}")
    print(f"→ {OUT}")

if __name__ == '__main__':
    main()
