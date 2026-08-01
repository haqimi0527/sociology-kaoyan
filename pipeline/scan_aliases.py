# -*- coding: utf-8 -*-
"""全面别名引用扫描：定义里"又称X/亦称X/简称X/即X/又名X"且 X 是库内概念 → 别名合并候选

只读，输出 D:/workspace/_alias_scan.json
"""
import json, io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

CONCEPTS = "D:/workspace/sociology-kaoyan-app/web/data/concepts.json"
OUT = "D:/workspace/_alias_scan.json"

def main():
    cs = json.load(open(CONCEPTS, encoding='utf-8'))
    cmap = {c['term']: c for c in cs}
    # 排序由长到短，优先匹配长 term
    sorted_terms = sorted(cmap.keys(), key=len, reverse=True)

    found = {}
    for c in cs:
        d = c.get('definition') or ''
        # 找"又称X"等引用，X 匹配库内 term
        for m in re.finditer(r'(又称|亦称|也叫|又名|别称|简称为|简称|即)([^，。；,;：:（(]{2,20})', d):
            ref = m.group(2).strip()
            # 匹配库内 term（精确或最长前缀）
            matched = None
            for t in sorted_terms:
                if t == ref or ref.startswith(t) and len(t) >= len(ref) - 2:
                    matched = t
                    break
            if matched and matched != c['term']:
                key = (c['term'], matched)
                found[key] = f"{c['term']} 定义称 {matched} 为别名"

    # 去重排序
    pairs = sorted(found.keys(), key=lambda x: x[0])
    json.dump([{"term": a, "alias": b} for a, b in pairs],
              open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f"定义别名引用: {len(pairs)} 对")
    for a, b in pairs:
        print(f"  {a} → 别名 → {b}")
    print(f"→ {OUT}")

if __name__ == '__main__':
    main()
