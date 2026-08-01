# -*- coding: utf-8 -*-
"""补别名合并：定义"又称X"引用且双方在库内的同一概念（2026-08-01 复查第3轮）

跳过：研究对象~分析单位、实验刺激~自变量（考研独立考点风险）
keeper = 定义"又称"主体（被引用者为别名）
"""
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

CONCEPTS = "D:/workspace/sociology-kaoyan-app/web/data/concepts.json"
GROUPS = {
    "构造效度": ["建构效度"],
    "虚假关系": ["虚无关系"],
    "重测信度": ["再测信度"],
    "定额抽样": ["配额抽样"],
    "职业团体": ["法人团体"],
    "覆盖误差": ["抽样框误差"],
    "置信度": ["置信水平"],
    "抽样对象": ["抽样单位"],
    "随机指派": ["随机化"],
    "集体访谈": ["座谈会"],
    "象征资本": ["符号资本"],
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
    removed = []
    for kt, victims in GROUPS.items():
        k = cmap.get(kt)
        for vt in victims:
            v = cmap.get(vt)
            if not k or not v or k["id"] == v["id"]:
                print(f"  [跳过] {kt} ← {vt}"); continue
            merge_into(k, v); removed.append(v["id"]); print(f"  [合并] {vt} → {kt}")
    keep = [c for c in cs if c["id"] not in removed]
    json.dump(keep, open(CONCEPTS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n补别名合并 {len(removed)} 条: {len(cs)} → {len(keep)}")

if __name__ == "__main__":
    main()
