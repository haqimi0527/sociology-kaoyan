# -*- coding: utf-8 -*-
"""补 AI 语义检测确认的 14 组真变体（双方在库、同一概念）"""
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

CONCEPTS = "D:/workspace/sociology-kaoyan-app/web/data/concepts.json"
GROUPS = {
    "理性化": ["合理化"],                    # 韦伯 Rationalisierung
    "社会分工": ["劳动分工"],                # 涂尔干
    "生命权力": ["生命政治"],                # 福柯 biopower
    "超现实": ["超实现"],                    # 鲍德里亚 hyperrealite
    "相对剩余价值": ["相对剩余价值的生产"],  # 马克思
    "方法论个人主义": ["方法论个体主义"],    # 方法论原则
    "型构": ["构型"],                        # 埃利亚斯 figuration
    "零假设": ["原假设", "虚无假设"],        # 统计假设检验
    "准则效度": ["实用效度", "效标效度"],    # 测量效度
    "层次谬误": ["区群谬误"],                # 统计逻辑错误
    "主观抽样": ["判断抽样"],                # 非概率抽样
    "频数分布": ["频率分布"],                # 描述统计
    "焦点小组": ["专题小组"],                # 焦点小组访谈
    "沟通理性": ["交往理性（Communicative Rationality）"],  # 哈贝马斯
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
    print(f"\n补 AI 语义合并 {len(removed)} 条: {len(cs)} → {len(keep)}")

if __name__ == "__main__":
    main()
