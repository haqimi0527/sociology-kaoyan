# -*- coding: utf-8 -*-
"""概念合并方案 Step7 前置：汇总执行计划（只读，供用户审批）

汇总各 step 清单 → 每个概念一个动作:
  DELETE       - 删（碎片/垃圾/泛化）
  MERGE_INTO   - 合并到 keeper（变体/展开概念）
  RELOCATE     - 错位归位（改 chapter）
  KEEP         - 保留
  BORDER       - 模糊带（用户逐条审）

输出: D:/workspace/_report_execution_plan.json/.md
"""
import os, sys, io, re, json, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

CONCEPTS = "D:/workspace/sociology-kaoyan-app/web/data/concepts.json"
W = "D:/workspace"
OUT_JSON = f"{W}/_report_execution_plan.json"
OUT_MD = f"{W}/_report_execution_plan.md"

def load(p):
    return json.load(open(p, encoding='utf-8'))

def main():
    cs = load(CONCEPTS)
    cmap = {c['id']: c for c in cs}
    termmap = {c['term']: c for c in cs}

    plan = {}  # id -> {action, target, reason}

    # Step2 碎片 DELETE
    for r in load(f"{W}/_report_delete_fragments.json"):
        plan[r['id']] = {"action": "DELETE", "target": None, "reason": r['reason']}

    # Step3 错位修复（delete → DELETE, 其他 → RELOCATE）
    for r in load(f"{W}/_report_misplaced_fix.json"):
        if r['type'] == 'delete':
            plan[r['id']] = {"action": "DELETE", "target": None, "reason": f"泛化标签·{r['reason']}"}
        else:
            plan[r['id']] = {"action": "RELOCATE", "target": r['new_chapter'], "reason": f"错位归位·{r['reason']}"}

    # Step4 待审区 DELETE（碎片）
    rv = load(f"{W}/_report_review_1024.json")
    for r in rv.get('DELETE', []):
        if r['id'] not in plan:
            plan[r['id']] = {"action": "DELETE", "target": None, "reason": f"待审碎片·{r['mark']}"}

    # Step5 变体合并
    sm = load(f"{W}/_report_synonym_merge.json")
    border = []
    merged_ids = set()
    for g in sm['groups']:
        kid = g['keeper']['id']
        for m in g['merged']:
            if m['id'] in plan:
                continue  # 已被删/归位，不合并
            plan[m['id']] = {"action": "MERGE_INTO", "target": kid, "reason": f"变体合并·{g['type']}"}
            merged_ids.add(m['id'])
    # 展开概念 → 并入主条（去"的XX/产生的"后缀匹配；无主条 → 留 BORDER 用户审）
    for t in sm['expanded']:
        c = termmap.get(t)
        if not c or c['id'] in plan:
            continue
        base = re.sub(r'(产生|形成|影响|的|及其)*的(原因|根源|因素|影响|作用|关系|类型|程度|强度|过程|构成|形成|条件|后果|分类|特点|功能|意义|性质|本质|来源|变迁|发展|产生|方式|结构|层次|问题|结果|前提|基础|机制|内容|逻辑|方法|区分)$', '', t)
        base = re.sub(r'^(影响|决定|制约|促进)', '', base)
        if base in termmap and termmap[base]['id'] != c['id'] and termmap[base]['id'] not in plan:
            plan[c['id']] = {"action": "MERGE_INTO", "target": termmap[base]['id'], "reason": f"展开概念并入「{base}」"}
        else:
            border.append({"id": c['id'], "term": t, "chapter": c.get('chapter',''),
                           "source_text": c.get('source_text',''), "exam_frequency": c.get('exam_frequency',''),
                           "definition": (c.get('definition') or '')[:120], "def_len": len(c.get('definition') or ''),
                           "mark": "展开概念无主条·用户审"})

    # BORDER 待审（合并：step4 模糊带 + 展开概念无主条）
    border += [r for r in rv.get('BORDER', []) if r['id'] not in plan]

    # 最终分类
    stats = collections.Counter(p['action'] for p in plan.values())
    keep_count = len(cs) - len(plan) - len(border)
    final = len(cs) - len(plan)  # 合并/删后（border 暂保留）

    json.dump({"plan": plan, "border": border}, open(OUT_JSON, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    L = [f"# 概念合并汇总执行计划", f"\n总概念: {len(cs)}", ""]
    L.append(f"- **DELETE**: {stats.get('DELETE', 0)}")
    L.append(f"- **MERGE_INTO**: {stats.get('MERGE_INTO', 0)}")
    L.append(f"- **RELOCATE**: {stats.get('RELOCATE', 0)}")
    L.append(f"- **BORDER待审**: {len(border)}")
    L.append(f"- **KEEP**: {keep_count}")
    L.append(f"\n执行后预计: {final} 条（BORDER 待审未计入）")
    L.append(f"\n## DELETE ({stats.get('DELETE',0)})")
    for pid, p in plan.items():
        if p['action'] == 'DELETE':
            L.append(f"- {cmap[pid]['term']} | {p['reason']}")
    L.append(f"\n## MERGE_INTO ({stats.get('MERGE_INTO',0)})")
    for pid, p in plan.items():
        if p['action'] == 'MERGE_INTO':
            L.append(f"- {cmap[pid]['term']} → 并入 {cmap[p['target']]['term']} | {p['reason']}")
    L.append(f"\n## RELOCATE ({stats.get('RELOCATE',0)})")
    for pid, p in plan.items():
        if p['action'] == 'RELOCATE':
            L.append(f"- {cmap[pid]['term']} → {p['target']} | {p['reason']}")
    L.append(f"\n## BORDER 待审 ({len(border)})")
    for b in border:
        L.append(f"- {b['term']} | def={b['def_len']}字 | src={b['source_text'][:16] or '空'}")
    with open(OUT_MD, 'w', encoding='utf-8') as f:
        f.write('\n'.join(L))

    print(f"DELETE: {stats.get('DELETE',0)}, MERGE_INTO: {stats.get('MERGE_INTO',0)}, RELOCATE: {stats.get('RELOCATE',0)}")
    print(f"BORDER 待审: {len(border)}, KEEP: {keep_count}")
    print(f"执行后预计: {final} 条")
    print(f"→ {OUT_JSON}\n→ {OUT_MD}")

if __name__ == '__main__':
    main()
