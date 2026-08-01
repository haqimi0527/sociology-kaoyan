# -*- coding: utf-8 -*-
"""共享专业词检测：定义共享 ≥3 个专业词但 term 不同 → 内容相近候选
只读，输出 D:/workspace/_shared_word_pairs.txt
"""
import json, io, sys, re
from collections import defaultdict
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

CONCEPTS = "D:/workspace/sociology-kaoyan-app/web/data/concepts.json"
OUT = "D:/workspace/_shared_word_pairs.txt"
STOP = set("的与和及了在是这那之对从而并由或" + "社会" + "理论" + "概念" + "研究" + "方法" + "主义" + "主要" + "认为" + "提出" + "一种" + "进行" + "通过" + "包括" + "具有" + "表示" + "成为" + "人们" + "之间" + "不同" + "关系" + "过程" + "发展" + "形成")

def words(d):
    d = re.sub(r'\s+', '', d or '')
    out = set()
    # 2-4 字词（简单滑窗 + 去停用）
    for n in (4, 3, 2):
        for i in range(len(d) - n + 1):
            w = d[i:i+n]
            if w in STOP: continue
            out.add(w)
    return out

def main():
    cs = json.load(open(CONCEPTS, encoding='utf-8'))
    act = [(c['term'], (c.get('definition') or ''), words(c.get('definition') or '')) for c in cs]
    act = [x for x in act if len(x[1]) >= 30]
    print(f"定义≥30字: {len(act)} / {len(cs)}")

    pairs = []
    N = len(act)
    # O(n^2) 共享词≥3
    for i in range(N):
        for j in range(i+1, N):
            ta, da, wa = act[i]
            tb, db, wb = act[j]
            if ta == tb: continue
            inter = wa & wb
            if len(inter) >= 4 and len(wa) >= 6 and len(wb) >= 6:
                r = len(inter) / min(len(wa), len(wb))
                if r >= 0.35:
                    pairs.append((round(r, 2), ta, tb, len(inter), sorted(inter)[:8]))

    pairs.sort(key=lambda x: -x[0])
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(f"共享专业词候选: {len(pairs)}\n\n")
        for r, ta, tb, n, inter in pairs:
            f.write(f"[{r}] {ta} ~ {tb} (共享{n}词: {','.join(inter)})\n")
    print(f"共享词候选: {len(pairs)}")
    print("Top 40:")
    for r, ta, tb, n, inter in pairs[:40]:
        print(f"  [{r}] {ta} ~ {tb} (共享{n}: {','.join(inter[:5])})")

if __name__ == '__main__':
    main()
