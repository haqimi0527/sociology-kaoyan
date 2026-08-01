# -*- coding: utf-8 -*-
"""补内容层合并：定义互相引用/几乎相同的变体（2026-08-01 复查第2轮）

扫描：定义里含"又称X/也叫X/亦称X/即X"且 X 是库内 term → 别名关系候选
合并：确认的 5 组 + 别名扫描发现的
"""
import json, io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

CONCEPTS = "D:/workspace/sociology-kaoyan-app/web/data/concepts.json"

# 确认合并: keeper ← victim
GROUPS = {
    "隐性内容": ["隐形内容"],
    "单尾检验": ["单边检验"],
    "还原论": ["简化论"],
    "研究问题的创新性": ["问题的创造性"],
    "生活史研究": ["个人生活史研究"],
}

def merge_into(k, v):
    vdef = v.get("definition") or ""; kdef = k.get("definition") or ""
    if vdef and vdef != kdef:
        k["definition_long"] = ((k.get("definition_long") or "") + "\n" + vdef).strip()
    rel = [r for r in (k.get("related") or []) if isinstance(r, dict)]
    rt = {r.get("term") for r in rel}
    if v["term"] not in rt and v["term"] != k["term"]:
        rel.append({"id": v.get("id"), "relation": "alias", "term": v["term"]}); rt.add(v["term"])
    for r in (v.get("related") or []):
        if isinstance(r, dict) and r.get("term") and r["term"] not in rt:
            rel.append(r); rt.add(r["term"])
    k["related"] = rel
    kt = set(k.get("tags") or []); kt.update(v.get("tags") or []); k["tags"] = sorted(kt)

def main():
    cs = json.load(open(CONCEPTS, encoding="utf-8"))
    cmap = {c["term"]: c for c in cs}

    # 扫描"又称X/也叫X"别名引用
    alias_refs = []
    for c in cs:
        d = c.get("definition") or ""
        m = re.search(r'(又称|也叫|亦称|又名|别称)[：: ]?([^，。；,;]{2,10})', d)
        if m:
            ref = m.group(2).strip().rstrip('。')
            if ref in cmap and cmap[ref]['id'] != c['id']:
                alias_refs.append((c['term'], ref))

    removed = []
    for kt, victims in GROUPS.items():
        k = cmap.get(kt)
        for vt in victims:
            v = cmap.get(vt)
            if not k or not v or k['id'] == v['id']:
                print(f"  [跳过] {kt} ← {vt}"); continue
            merge_into(k, v); removed.append(v['id']); print(f"  [合并] {vt} → {kt}")

    keep = [c for c in cs if c['id'] not in removed]
    json.dump(keep, open(CONCEPTS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n补合并 {len(removed)} 条: {len(cs)} → {len(keep)}")
    print(f"\n别名引用扫描(未合并，供参考): {len(alias_refs)}")
    for a, b in alias_refs[:30]:
        print(f"  {a} →又称→ {b}")

if __name__ == "__main__":
    main()
