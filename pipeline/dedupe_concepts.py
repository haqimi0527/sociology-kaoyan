# -*- coding: utf-8 -*-
"""方向1：合并同名重复 + 碎片扫描

三通道算法：
  A. 同名重复合并：norm_for_dedup(term) 分组 → 按 (def_len, source_rank, base_bonus) 排序
     保留主条，其余合并删除
  B. 定义前60字(去空白)重复：归一后同组→并入A；不同 term→MANUAL_REVIEW 人工清单
  C. 碎片全量扫描 → DELETE 候选（classify_fragment + 新增残句规则）

用法:
  python pipeline/dedupe_concepts.py --report    # 纯统计（供 verify.sh）
  python pipeline/dedupe_concepts.py --plan      # 出审批清单，不写 concepts
  python pipeline/dedupe_concepts.py --apply <plan.json>  # 执行
"""
import os, sys, io, re, json, collections, hashlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from pipeline.utils.concept_utils import norm_for_dedup, def_prefix_key, classify_fragment, clean_term

def group_key(term):
    """分组键：clean_term 去 OCR 残渣 + norm_for_dedup 归一"""
    return norm_for_dedup(clean_term(term))

CONCEPTS = "D:/workspace/sociology-kaoyan-app/web/data/concepts.json"
PLAN_OUT = "D:/workspace/_report_dedupe_plan.json"
MD_OUT = "D:/workspace/_report_dedupe_plan.md"

# 来源权威排序
def source_rank(src):
    src = (src or "").strip()
    if "lcwiki" in src:
        return 3
    if not src:
        return 2
    return 1  # 杨善华笔记/下卷/其他

def rank_entry(c):
    """主条排序：无后缀 base id 最优先（taxonomy 索引目标），其次定义最长 + 来源权威

    为什么 base 优先：taxonomy 引用的是无后缀 id，删 base 保留 _N 会悬空引用。
    且 base 通常是 lcwiki 或原始主条（来源权威）。
    """
    def_len = len(c.get("definition", "") or "")
    src = (c.get("source_text", "") or "").strip()
    is_base = 0 if re.search(r'_\d+$', c.get("id", "")) else 1  # base 优先
    return (is_base, def_len, source_rank(src))

def load_concepts():
    return json.load(open(CONCEPTS, encoding="utf-8"))

# ---------- 通道A：同名重复合并 ----------
def find_same_name_groups(concepts):
    """按 norm_for_dedup(term) 分组，返回 [{key, members:[...]}]"""
    groups = collections.defaultdict(list)
    for c in concepts:
        key = group_key(c.get("term", ""))
        if key:
            groups[key].append(c)
    return [{"key": k, "members": v} for k, v in groups.items() if len(v) > 1]

# ---------- 通道B：定义前60字重复 ----------
def find_def_prefix_groups(concepts):
    """定义前60字(去空白)重复组：{key: [concepts]}"""
    groups = collections.defaultdict(list)
    for c in concepts:
        d = c.get("definition", "") or ""
        if len(d) < 20:
            continue
        key = def_prefix_key(d, 60)
        if key:
            groups[key].append(c)
    return {k: v for k, v in groups.items() if len(v) > 1}

# ---------- 通道C：碎片扫描 ----------
def _has_strong_def(c):
    """定义强信号：≥30字（真概念特征，非残句）"""
    d = (c.get("definition", "") or "").strip()
    return len(d) >= 30

def find_fragments(concepts):
    """碎片 DELETE 候选：只删确定垃圾，误伤保护

    保护规则（不删）：
      - id 以 lc_ 开头（lcwiki 权威来源）
      - 含括号且括号内是英文/学者名（`区隔(Distinction)` `个人主义(托克维尔)`）
      - 有强定义信号（≥30字句号结尾）—— 可能是真概念
    """
    # 泛化词（方法词典小节标题，确定垃圾）
    GENERIC = {"过程与步骤","作用与重要性","要求与问题","定义","含义","特点","作用","意义",
               "步骤","注意事项","适用","适用条件","具体做法","优缺点","优点","缺点","局限性",
               "研究的工具不同","研究的程序不同","研究的策略不同","论文补充","答案参考","示例1",
               "示例2","示例3","例1","例2","例3","排版与流程问题","看过的继续回答","怎么做",
               "提问方式","数字和符号","解决措施","解决","逻辑","设计","构成","测量结果",
               "抽样设计的目标","变量取值","研究问题明确化","三者的关系","三种结果","两者",
               "二者","不同之处","不同之处在于","不同之处如下","不同之处有如下四点",
               "二者的不同之处如下两点","相同之处","相同之处在于","相同之处如下",
               "相同之处有如下两点","一是话语对象","二是述说模态","三是概念","拓展","定性",
               "核心","核心特征","理论局限","理论贡献","起源","基础","符号","特性","联系"}
    frags = []
    for c in concepts:
        term = (c.get("term", "") or "").strip()
        cid = c.get("id", "")
        # 保护1：lcwiki 来源不删
        if str(cid).startswith("lc_"):
            continue
        # 保护2：含括号但括号内是英文/学者名
        if re.search(r'[（(][A-Za-z\s/-]+[）)]', term) or re.search(r'[（(][一-鿿]{1,5}[）)]$', term):
            continue
        # 保护3：强定义信号不删
        if _has_strong_def(c):
            continue
        rule = classify_fragment(term)
        if not rule:
            if term in GENERIC:
                rule = "泛化词/小节标题"
        # 碎片扫描只接受"确定垃圾"规则：泛化词 + 含标点（问句/题目标题）
        # 不接受"概念名>10字/含括号/开头残句/含笔记符号"——这些可能是有完整定义的真概念
        if rule in ("泛化词", "泛化词/小节标题", "含标点", "编号前缀"):
            frags.append({
                "id": cid, "term": term,
                "chapter": c.get("chapter", ""),
                "matched_rule": rule,
                "def_snippet": (c.get("definition", "") or "")[:50],
                "source": c.get("source_text", ""),
            })
    return frags

# ---------- 主流程 ----------
def build_plan(concepts):
    plan = {"schema_version": 1, "same_name_merges": [], "def_prefix_manual": [],
            "fragment_deletes": [], "stats": {}}
    by_id = {c["id"]: c for c in concepts}

    # 通道A
    merge_count = 0
    for g in find_same_name_groups(concepts):
        members = sorted(g["members"], key=rank_entry, reverse=True)
        keeper = members[0]
        deleted = members[1:]
        if not deleted:
            continue
        entry = {
            "group_key": g["key"],
            "terms_seen": sorted({m.get("term", "") for m in members}),
            "keeper": {
                "id": keeper["id"], "term": keeper.get("term", ""),
                "def_len": len(keeper.get("definition", "") or ""),
                "source": keeper.get("source_text", ""),
                "chapter": keeper.get("chapter", ""),
                "def_snippet": (keeper.get("definition", "") or "")[:60],
            },
            "deleted_ids": [m["id"] for m in deleted],
            "deleted_details": [{
                "id": m["id"], "term": m.get("term", ""),
                "def_len": len(m.get("definition", "") or ""),
                "source": m.get("source_text", ""),
                "def_snippet": (m.get("definition", "") or "")[:60],
            } for m in deleted],
            "action": "MERGE",
            "rationale": "同名重复；主条定义最长且来源权威；副本精华并入主条",
        }
        plan["same_name_merges"].append(entry)
        merge_count += 1

    # 通道B：定义前60字重复 → 归一后同组并入A（已含），不同 term 进人工
    manual = []
    for key, members in find_def_prefix_groups(concepts).items():
        if len(members) < 2:
            continue
        # 所有成员 term 归一后是否同组（即已由通道A处理）
        norm_terms = {norm_for_dedup(m.get("term", "")) for m in members}
        if len(norm_terms) > 1:
            manual.append({
                "terms": [m.get("term", "") for m in members],
                "ids": [m["id"] for m in members],
                "def_prefix60": key[:60],
                "recommendation": "REVIEW",
                "detail": "概念名不同、定义开头相同，疑似共用引导语但概念不同，需人工判断",
            })
    plan["def_prefix_manual"] = manual

    # 通道C
    frags = find_fragments(concepts)
    plan["fragment_deletes"] = frags

    # 统计
    total_merge_entries = sum(len(e["deleted_ids"]) for e in plan["same_name_merges"])
    plan["stats"] = {
        "same_name_groups": len(plan["same_name_merges"]),
        "same_name_entries": total_merge_entries + len(plan["same_name_merges"]),
        "merge_deleted": total_merge_entries,
        "def_prefix_groups": len(find_def_prefix_groups(concepts)),
        "def_prefix_manual": len(plan["def_prefix_manual"]),
        "fragment_delete_candidates": len(plan["fragment_deletes"]),
        "net_concepts_after_apply": len(concepts) - total_merge_entries - len(plan["fragment_deletes"]),
    }
    return plan

def write_md(plan):
    lines = ["# 方向1 去重审批清单", ""]
    lines.append(f"## 统计\n- 同名重复组: {plan['stats']['same_name_groups']} 组 / {plan['stats']['same_name_entries']} 条")
    lines.append(f"- 定义前60字重复组: {plan['stats']['def_prefix_groups']}（人工核查 {plan['stats']['def_prefix_manual']} 组）")
    lines.append(f"- 碎片 DELETE 候选: {plan['stats']['fragment_delete_candidates']} 条")
    lines.append(f"- 净变化: 2483 → {plan['stats']['net_concepts_after_apply']}\n")
    lines.append(f"## 需人工核查（{len(plan['def_prefix_manual'])} 组）")
    lines.append("| terms | def前60字 | 建议 |")
    lines.append("|---|---|---|")
    for m in plan["def_prefix_manual"]:
        lines.append(f"| {' / '.join(m['terms'])} | {m['def_prefix60'][:30]} | {m['recommendation']} |")
    lines.append(f"\n## 将合并（{len(plan['same_name_merges'])} 组，删 {plan['stats']['merge_deleted']} 条）")
    lines.append("| term | keeper_id | keeper字数 | 删除id | 删除字数 | 删除来源 |")
    lines.append("|---|---|---|---|---|---|")
    for e in plan["same_name_merges"]:
        for d in e["deleted_details"]:
            lines.append(f"| {e['group_key']} | {e['keeper']['id']} | {e['keeper']['def_len']} | {d['id']} | {d['def_len']} | {d['source'][:20]} |")
    lines.append(f"\n## 碎片 DELETE 候选（{len(plan['fragment_deletes'])} 条）")
    lines.append("| id | term | 规则 | chapter |")
    lines.append("|---|---|---|---|")
    for f in plan["fragment_deletes"]:
        lines.append(f"| {f['id']} | {f['term']} | {f['matched_rule']} | {f['chapter'][:40]} |")
    open(MD_OUT, "w", encoding="utf-8").write("\n".join(lines))
    print(f"→ {MD_OUT}")

def apply_plan(plan, concepts):
    """执行合并/删除"""
    drop_ids = set()
    by_id = {c["id"]: c for c in concepts}
    merged = 0
    for e in plan["same_name_merges"]:
        keeper = by_id.get(e["keeper"]["id"])
        if not keeper:
            continue
        for did in e["deleted_ids"]:
            dup = by_id.get(did)
            if not dup:
                continue
            # 聚合字段（元素可能是 dict，用 JSON 串去重）
            for f in ("core_points", "related", "tags"):
                kv = list(keeper.get(f) or [])
                dv = list(dup.get(f) or [])
                merged_list = []
                seen = set()
                for item in kv + dv:
                    key = json.dumps(item, ensure_ascii=False) if isinstance(item, dict) else str(item)
                    if key not in seen:
                        seen.add(key)
                        merged_list.append(item)
                keeper[f] = merged_list
            # 副本定义更长则替换
            if len(dup.get("definition", "") or "") > len(keeper.get("definition", "") or ""):
                keeper["definition"] = dup["definition"]
            # exam_freq 取较高
            if dup.get("exam_frequency") == "high":
                keeper["exam_frequency"] = "high"
            elif keeper.get("exam_frequency") in (None, "") and dup.get("exam_frequency"):
                keeper["exam_frequency"] = dup["exam_frequency"]
            # source_text 空则填
            if not keeper.get("source_text") and dup.get("source_text"):
                keeper["source_text"] = dup["source_text"]
            drop_ids.add(did)
            merged += 1
    for f in plan["fragment_deletes"]:
        drop_ids.add(f["id"])
    kept = [c for c in concepts if c["id"] not in drop_ids]
    return kept, merged

def main():
    mode = "--report" if "--report" in sys.argv else "--plan" if "--plan" in sys.argv else "apply"
    concepts = load_concepts()

    if mode == "--report":
        plan = build_plan(concepts)
        s = plan["stats"]
        print(f"同名重复组: {s['same_name_groups']} / {s['same_name_entries']}条")
        print(f"定义前60字重复组: {s['def_prefix_groups']} (人工 {s['def_prefix_manual']})")
        print(f"碎片DELETE候选: {s['fragment_delete_candidates']}")
        print(f"净变化: {len(concepts)} → {s['net_concepts_after_apply']}")
        return

    if mode == "--plan":
        plan = build_plan(concepts)
        with open(PLAN_OUT, "w", encoding="utf-8") as f:
            json.dump(plan, f, ensure_ascii=False, indent=1)
        print(f"计划已写入 {PLAN_OUT}")
        print(f"同名重复: {plan['stats']['same_name_groups']}组 删{plan['stats']['merge_deleted']}条")
        print(f"人工核查: {len(plan['def_prefix_manual'])}组")
        print(f"碎片DELETE: {len(plan['fragment_deletes'])}条")
        write_md(plan)
        return

    # apply
    plan_path = sys.argv[sys.argv.index("--apply") + 1]
    plan = json.load(open(plan_path, encoding="utf-8"))
    kept, merged = apply_plan(plan, concepts)
    print(f"合并删除: {merged + len(plan['fragment_deletes'])} 条 (合并{merged} + 碎片{len(plan['fragment_deletes'])})")
    print(f"条数: {len(concepts)} → {len(kept)}")
    with open(CONCEPTS, "w", encoding="utf-8") as f:
        json.dump(kept, f, ensure_ascii=False, indent=1)
    print(f"→ {CONCEPTS}")

if __name__ == "__main__":
    main()
