# -*- coding: utf-8 -*-
"""补漏合并：译名/虚字归一发现的漏网变体（2026-08-01 复查）"""
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

CONCEPTS = "D:/workspace/sociology-kaoyan-app/web/data/concepts.json"
GROUPS = {
    "自杀类型论": ["自杀类型"], "模式变量": ["模式变项"],
    "宿命型自杀": ["宿命性自杀"], "祛魅": ["除魅"],
    "内局群体与外局群体": ["内局群体和外局群体"], "关系论": ["关系主义"],
    "抽样": ["抽样方法"], "非概率抽样": ["非概率抽样方法"],
    "失范型自杀": ["失范性自杀"], "压力-分化模式": ["压力—分化模式"],
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
    print(f"\n补合并 {len(removed)} 条: {len(cs)} → {len(keep)}")

if __name__ == "__main__":
    main()
