# -*- coding: utf-8 -*-
"""方向2：分类体系全面重组（chapter 字段归一）

规则：
  1. 顶层归一：社会学研究方法/→方法/、当代→理论
  2. 理论二级：古典/现代/当代→古典时期/现代时期/当代时期；学者直挂→时期/学派展开
  3. 概论编号章节：第X章→主题；编号+主题混合（第十一章社会分层）→剥编号
  4. 空chapter/未分类：proponent命中学者→展开；否则留空

用法:
  python pipeline/normalize_chapters.py --check   # 统计
  python pipeline/normalize_chapters.py --plan    # 出清单（不写）
  python pipeline/normalize_chapters.py --apply   # 写回
"""
import os, sys, io, re, json, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from pipeline.utils.concept_utils import SCHOLAR_NAMES

CONCEPTS = "D:/workspace/sociology-kaoyan-app/web/data/concepts.json"
MAPPINGS = os.path.join(os.path.dirname(__file__), "config", "chapter_mappings.json")
PLAN_OUT = "D:/workspace/_report_chapter_normalize_plan.json"
MD_OUT = "D:/workspace/_report_chapter_normalize_plan.md"

MAP = json.load(open(MAPPINGS, encoding="utf-8"))
TOP_RENAME = MAP["top_level_rename"]
ERA_RENAME = MAP["era_rename"]
SCHOLAR_MAP = MAP["scholar_to_era_school"]
CHAPTER_TO_TOPIC = MAP["chapter_to_topic"]
TOPIC_RENAME = MAP.get("topic_rename", {})

# 时期→学派默认（学者不在映射表时兜底到时期）
ERA_DEFAULT_SCHOOL = {
    "古典时期": "其他古典学者",
    "现代时期": "其他现代学者",
    "当代时期": "其他当代学者",
}

def normalize_chapter(ch, concept=None):
    """归一单个 chapter，返回新 chapter（保留尾斜杠）

    concept: 可选 dict，用于二级空（概论/理论/方法）时的关键词推断
    """
    parts = [p for p in (ch or "").split("/") if p.strip()]
    if not parts:
        return ""
    top = parts[0]
    top = TOP_RENAME.get(top, top)
    parts[0] = top  # 写回顶层

    if top == "理论" and len(parts) >= 2:
        p2 = parts[1].strip()
        if p2 in ERA_RENAME:
            parts[1] = ERA_RENAME[p2]
        elif p2 in SCHOLAR_MAP:
            era, school, scholar = SCHOLAR_MAP[p2]
            parts = [top, era, school, scholar] + parts[2:]
    elif top == "概论" and len(parts) >= 2:
        p2 = parts[1].strip()
        # 第十一章社会分层与社会流动 → 剥编号留主题
        stripped = re.sub(r'^第[一二三四五六七八九十百\d]+章', '', p2)
        if stripped and stripped != p2:
            parts[1] = stripped
        elif re.match(r'^第[一二三四五六七八九十百\d]+章$', p2):
            topic = CHAPTER_TO_TOPIC.get(f"概论/{p2}/")
            parts[1] = topic.rstrip('/').split('/')[-1] if topic else "待分类"
    elif top == "方法":
        # 方法域已是目标顶层，二级路径保留
        pass

    # 主题收敛（概论/方法 二级词 → 目标主题，含三级路径前缀匹配）
    joined = "/".join(parts).strip("/") + "/"
    if joined in TOPIC_RENAME:
        return TOPIC_RENAME[joined]
    for old, new in sorted(TOPIC_RENAME.items(), key=lambda kv: -len(kv[0])):
        if joined.startswith(old):
            return new + joined[len(old):]

    # 二级空（概论/、理论/、方法/）→ 关键词推断
    if concept is not None and len(parts) == 1:
        inferred = infer_chapter_for_empty(concept)
        if inferred:
            return inferred

    return joined

# 关键词 → 目标 chapter（空chapter/未分类 推断）
KEYWORD_CHAPTERS = [
    # (关键词列表, 目标chapter)
    (["真理宣称","正当宣称","真诚宣称","商谈","商谈原则","理想语言情境","理想言说情境","沟通行动","交往行动","普遍语用学","批判的解释学"], "理论/当代时期/沟通行动理论/哈贝马斯/"),
    (["血缘","氏族","宗族","家族","亲属","文化相对主义","文化震惊","种族","民族","文化模式","文化特质","文化","规范","价值"], "概论/文化与社会/"),
    (["社会化","内化","角色","自我","人格","镜中我","初级群体","首属群体","自我概念","角色扮演"], "概论/个人与社会/"),
    (["科层","组织","单位制","官僚","职业","管理","分层","流动","阶级","阶层","地位","声望"], "概论/社会分层与流动/"),
    (["社区","城市","乡村","城市化","集镇","村落","空间","区域"], "概论/社区与城市化/"),
    (["社会变迁","现代化","全球化","进化","发展","转型","变迁","风险","工业化","后工业"], "概论/社会变迁/"),
    (["社会问题","越轨","犯罪","贫困","失业","环境","人口","老龄化","失调"], "概论/社会问题/"),
    (["控制","规范","秩序","制裁","整合","越轨","惩罚"], "概论/社会控制/"),
    (["制度","家庭","教育","经济","政治","宗教","法律"], "概论/社会制度/"),
    (["信任","交换","网络","社会资本","博弈","理性","合作"], "理论/现代时期/社会交换理论/"),
    (["韦伯","理性化","科层制","权威","新教伦理","卡里斯马","铁笼","理解"], "理论/古典时期/理解社会学/韦伯/"),
    (["涂尔干","迪尔凯姆","社会事实","团结","失范","自杀","宗教","集体","分工"], "理论/古典时期/社会学主义/涂尔干/"),
    (["马克思","阶级","异化","资本","商品","剩余价值","生产力","生产关系","意识形态","剥削"], "理论/古典时期/历史唯物主义/马克思/"),
    (["福柯","权力","话语","规训","知识","谱系","性经验","监狱","主体"], "理论/当代时期/后结构主义与谱系学/福柯/"),
    (["吉登斯","结构化","现代性","时空","脱域","反思","本体安全"], "理论/当代时期/结构化理论/吉登斯/"),
    (["布迪厄","场域","惯习","资本","区隔","实践","再生产","符号"], "理论/当代时期/实践理论/布迪厄/"),
    (["哈贝马斯","公共领域","沟通","生活世界","交往理性","商谈"], "理论/当代时期/沟通行动理论/哈贝马斯/"),
    (["舒茨","现象学","生活世界","类型化","自然态度","主体间"], "理论/现代时期/现象学社会学与常人方法学/舒茨/"),
    (["帕森斯","AGIL","结构功能","模式变量","行动系统","社会系统"], "理论/现代时期/结构功能主义/帕森斯/"),
    (["默顿","中层","功能","失范","参照群体","越轨"], "理论/现代时期/结构功能主义/默顿/"),
    (["齐美尔","形式","时尚","货币","都市","陌生人","社会交往"], "理论/古典时期/形式社会学/齐美尔/"),
    (["方法论","假设","变量","操作化","信度","效度","抽样","问卷","访谈","测量","研究设计","资料分析","统计","回归","相关"], "方法/方法论基础/"),
]

# 方法词典来源标记
METHOD_SOURCE_MARK = ("南大_方法", "风笑天", "巴比", "方法名词解释", "方法真题", "社会学方法",
                       "研究设计", "资料分析", "抽样", "问卷调查", "测量", "社会研究方法")

def infer_chapter_for_empty(c):
    """空/未分类 chapter → 推断（proponent 学者 → 关键词主题 → 方法源兜底）"""
    prop = (c.get("proponent") or "") or ""
    src = (c.get("source_text") or "") or ""
    for name, (era, school, scholar) in SCHOLAR_MAP.items():
        if name in prop:
            return f"理论/{era}/{school}/{scholar}/"
    # 关键词推断（term + 定义 + 学者）
    text = f"{c.get('term','')} {c.get('definition','') or ''} {prop}"
    for kws, target in KEYWORD_CHAPTERS:
        if any(kw in text for kw in kws):
            return target
    # 方法词典来源兜底
    if any(m in src for m in METHOD_SOURCE_MARK):
        return "方法/方法论基础/"
    return None

def plan_concepts(concepts):
    """计算归一计划：返回 (new_chapter_by_id, report)"""
    changes = []
    for c in concepts:
        cid = c["id"]
        term = c.get("term", "")
        ch = c.get("chapter", "") or ""
        new_ch = normalize_chapter(ch, concept=c)
        if ch != new_ch:
            changes.append({
                "id": cid, "term": term,
                "old_chapter": ch, "new_chapter": new_ch,
                "type": "normalize",
            })

    # 空/未分类 chapter 推断
    inferred = []
    unresolved = []
    for c in concepts:
        ch = (c.get("chapter", "") or "").strip()
        parts = [p for p in ch.split("/") if p]
        if not parts or parts[0] in ("未分类",):
            new_ch = infer_chapter_for_empty(c)
            if new_ch:
                inferred.append({"id": c["id"], "term": c.get("term",""),
                                 "old_chapter": ch, "new_chapter": new_ch, "type": "infer"})
            else:
                unresolved.append({"id": c["id"], "term": c.get("term",""),
                                   "old_chapter": ch, "reason": "无学者/来源信号"})

    return changes, inferred, unresolved

def main():
    mode = "--check" if "--check" in sys.argv else "--plan" if "--plan" in sys.argv else "apply"
    concepts = json.load(open(CONCEPTS, encoding="utf-8"))

    changes, inferred, unresolved = plan_concepts(concepts)

    if mode == "--check":
        # 统计归一后顶层分布
        after = collections.Counter()
        touched = 0
        for c in concepts:
            ch = c.get("chapter", "") or ""
            new_ch = normalize_chapter(ch, concept=c)
            if ch != new_ch:
                touched += 1
            top = new_ch.split("/")[0] if new_ch else "(空)"
            after[top] += 1
        print(f"归一将改动: {touched} 条")
        print(f"归一后顶层: {dict(after.most_common(8))}")
        print(f"空chapter推断: {len(inferred)}, 未解决: {len(unresolved)}")
        return

    # plan 输出
    report = {
        "schema_version": 1,
        "total": len(concepts),
        "touched": len(changes),
        "normalize_changes": changes,
        "inferred": inferred,
        "unresolved": unresolved,
        "summary": {
            "top_after": None,
            "inferred_count": len(inferred),
            "unresolved_count": len(unresolved),
        }
    }
    # 统计归一后顶层
    after = collections.Counter()
    for c in concepts:
        ch = c.get("chapter", "") or ""
        new_ch = normalize_chapter(ch, concept=c)
        top = new_ch.split("/")[0] if new_ch else "(空)"
        after[top] += 1
    report["summary"]["top_after"] = dict(after.most_common(8))

    if mode == "--plan":
        with open(PLAN_OUT, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=1)
        print(f"计划已写入 {PLAN_OUT}")
        print(f"归一改动: {len(changes)} 条")
        print(f"空chapter推断: {len(inferred)} (未解决 {len(unresolved)})")
        # MD
        lines = ["# 方向2 分类归一审批清单", ""]
        lines.append(f"## 统计\n- 归一改动: {len(changes)} 条")
        lines.append(f"- 空chapter推断: {len(inferred)} (未解决 {len(unresolved)})")
        lines.append(f"- 归一后顶层: {report['summary']['top_after']}\n")
        # 顶层归一
        top_changes = [x for x in changes if x["old_chapter"].startswith(("社会学研究方法","当代"))]
        if top_changes:
            lines.append(f"## 顶层归一（{len(top_changes)} 条）")
            for x in top_changes[:10]:
                lines.append(f"- {x['old_chapter']} → {x['new_chapter']}")
        # 学者展开
        sch = [x for x in changes if x["old_chapter"].startswith("理论/") and len(x["old_chapter"].split('/'))<=3 and x["old_chapter"].split('/')[1] in SCHOLAR_MAP]
        if sch:
            lines.append(f"\n## 学者直挂展开（{len(sch)} 条）")
            for x in sch[:10]:
                lines.append(f"- {x['old_chapter']} → {x['new_chapter']}")
        # 编号章节
        num = [x for x in changes if '第' in x["old_chapter"]]
        if num:
            lines.append(f"\n## 编号章节映射（{len(num)} 条）")
            for x in num[:10]:
                lines.append(f"- {x['old_chapter']} → {x['new_chapter']}")
        # 空推断
        if inferred:
            lines.append(f"\n## 空chapter推断（{len(inferred)} 条）")
            for x in inferred[:10]:
                lines.append(f"- {x['term']} [{x['old_chapter']}] → {x['new_chapter']}")
        if unresolved:
            lines.append(f"\n## 未解决（{len(unresolved)} 条，留空）")
            lines.append("  " + ", ".join(x["term"] for x in unresolved[:20]))
        open(MD_OUT, "w", encoding="utf-8").write("\n".join(lines))
        print(f"→ {MD_OUT}")
        return

    # apply
    new_by_id = {x["id"]: x["new_chapter"] for x in changes}
    inf_by_id = {x["id"]: x["new_chapter"] for x in inferred}
    applied = 0
    for c in concepts:
        if c["id"] in new_by_id:
            c["chapter"] = new_by_id[c["id"]]
            applied += 1
        elif c["id"] in inf_by_id:
            c["chapter"] = inf_by_id[c["id"]]
            applied += 1
    with open(CONCEPTS, "w", encoding="utf-8") as f:
        json.dump(concepts, f, ensure_ascii=False, indent=1)
    print(f"归一+推断: {applied} 条 → {CONCEPTS}")

if __name__ == "__main__":
    main()
