# -*- coding: utf-8 -*-
"""定义内容相似度检测：term 不同但 definition 高度相似的概念对

方法：definition 去空白 → 前 80 字 difflib ratio ≥0.6 且 term 不同 → 候选
只读，输出 D:/workspace/_def_similar_pairs.txt
"""
import json, io, sys, re, difflib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

CONCEPTS = "D:/workspace/sociology-kaoyan-app/web/data/concepts.json"
OUT = "D:/workspace/_def_similar_pairs.txt"

def nospace(d):
    return re.sub(r'\s+', '', d or '')

def main():
    cs = json.load(open(CONCEPTS, encoding='utf-8'))
    # 只保留定义 ≥20 字的
    act = [(c['id'], c['term'], nospace(c.get('definition') or '')) for c in cs]
    act = [x for x in act if len(x[2]) >= 20]
    print(f"定义≥20字: {len(act)} / {len(cs)}")

    # 前10字hash桶（相似定义大概率前10字同），桶内 difflib
    from collections import defaultdict
    buckets = defaultdict(list)
    for cid, t, d in act:
        buckets[d[:10]].append((cid, t, d))

    pairs = []
    for key, items in buckets.items():
        for i in range(len(items)):
            for j in range(i+1, len(items)):
                a, b = items[i], items[j]
                if a[1] == b[1]:
                    continue
                # 前 80 字相似度
                r = difflib.SequenceMatcher(None, a[2][:80], b[2][:80]).ratio()
                if r >= 0.6:
                    pairs.append((round(r, 2), a[1], b[1], a[2][:50], b[2][:50]))

    pairs.sort(key=lambda x: -x[0])
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(f"定义相似候选: {len(pairs)}\n\n")
        for r, ta, tb, da, db in pairs:
            f.write(f"[{r}] {ta} ~ {tb}\n  A: {da}\n  B: {db}\n\n")
    print(f"定义相似候选(前80字≥0.6): {len(pairs)}")
    print(f"→ {OUT}")
    print("\nTop 40:")
    for r, ta, tb, da, db in pairs[:40]:
        print(f"  [{r}] {ta} ~ {tb}")

if __name__ == '__main__':
    main()
