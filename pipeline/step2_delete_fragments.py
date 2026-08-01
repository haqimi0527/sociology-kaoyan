# -*- coding: utf-8 -*-
"""概念合并方案 Step2：碎片 DELETE 清单（只收确定垃圾）

来源:
  1. Explore 报告确认的垃圾/提取碎片（纯学者名/来源注释/OCR残渣/序号/提取残片）
  2. classify_fragment 高置信规则命中 + 真概念保护（定义完整→转 REVIEW 不删）

输出:
  _report_delete_fragments.json/.md   DELETE 候选（确定垃圾，待用户审批）
  _report_repair_move.json/.md        错位归位候选（方法概念挂在学者下，留给 Step3）
"""
import os, sys, io, re, json, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from pipeline.utils.concept_utils import classify_fragment

CONCEPTS = "D:/workspace/sociology-kaoyan-app/web/data/concepts.json"
OUT_JSON = "D:/workspace/_report_delete_fragments.json"
OUT_MD = "D:/workspace/_report_delete_fragments.md"
OUT_RJ = "D:/workspace/_report_repair_move.json"
OUT_RM = "D:/workspace/_report_repair_move.md"

# 确定垃圾（Explore 报告 3.4）：纯学者名/来源注释/OCR残渣/序号/提取残片
EXPLORE_DELETE = {
    "马林诺夫斯基": "纯学者名(人类学家)",
    "赖特": "纯学者名(新马克思主义者)",
    "斯金纳": "纯学者名(行为主义心理学家)",
    "托马斯": "纯学者名(与库利并列的笔记错误)",
    "清华大学李强论精英": "来源注释非概念",
    "solidarity）": "OCR残渣",
    "sanctions）": "OCR残渣",
    "authority）": "OCR残渣",
    "group）": "OCR残渣",
    "第六": "提取残渣(序号)",
    "第七": "提取残渣(序号)",
    "第八": "提取残渣(序号)",
    "A．系统层次观点": "提取残渣",
    "否定性条件": "提取残渣",
    "利己已型自杀的原因": "描述短语非概念",
    "三条基本定律": "提取残渣",
    "学的任务": "提取残渣",
    "评价": "提取残渣(泛化词)",
    "例如": "提取残渣(泛化词)",
    "贡献": "提取残渣(泛化词)",
    "不足": "提取残渣(泛化词)",
    "自标": "提取残渣",
    "职业分布": "提取残渣",
    "未来的方向": "描述短语",
    "一一手段": "提取残渣(单位行动手段残片)",
    "定义": "提取残渣(泛化词)",
    "代表人物": "提取残渣(泛化词)",
    "现代社会学理论": "提取残渣(学科标题非概念)",
    "基本假设": "提取残渣(泛化词)",
    "核心观点": "提取残渣(泛化词)",
    "自我分为四类": "提取残渣",
    "性报酬的社会交换": "提取残渣(断行误切,应为内在性报酬)",
    "解决的办法": "描述短语",
    "分类": "提取残渣(泛化词)",
    "要求与问题": "描述短语",
}

# 方法概念错挂学者下 → 归位（留给 Step3，不删）
EXPLORE_REPAIR = {
    "命题": "方法概念(命题是方法论核心),错挂齐美尔→归方法",
    "第二手文献": "方法概念(二次文献),错挂齐美尔→归方法",
    "结构观察": "方法概念(观察法),错挂齐美尔→归方法",
    "理论建构与理论检验": "方法概念(理论建构),错挂齐美尔→归方法",
    "研究逻辑错位": "方法概念(真题考点),错挂齐美尔→归方法",
    "调查者误差": "方法概念(调查误差),错挂齐美尔→归方法",
    "归纳法": "方法概念,错挂米德→归方法",
}

# 规则命中后的真概念保护（定义完整→REVIEW 不删）
RULE_SAFE = {
    "分析单位", "结构", "过程社会学", "过程理论", "派生物",
    "过渡性贫困", "过度政治化", "过度私人化", "过程理论的多维标准",
}

ACCEPT_RULES = {"泛化词", "纯虚词", "含标点", "含笔记符号", "教学前缀", "教学后缀",
                "句子碎片", "导航文本", "编号前缀", "开头残句"}

def main():
    cs = json.load(open(CONCEPTS, encoding='utf-8'))
    by_term = {}
    for c in cs:
        by_term.setdefault(c['term'], c)

    deletes, repairs = [], []
    seen_d, seen_r = set(), set()

    for term, reason in EXPLORE_DELETE.items():
        c = by_term.get(term)
        if c and c['id'] not in seen_d:
            deletes.append({"id": c['id'], "term": term, "chapter": c.get('chapter',''),
                            "source_text": c.get('source_text',''),
                            "definition": (c.get('definition') or '')[:50],
                            "reason": reason})
            seen_d.add(c['id'])
    for term, reason in EXPLORE_REPAIR.items():
        c = by_term.get(term)
        if c and c['id'] not in seen_r:
            repairs.append({"id": c['id'], "term": term, "chapter": c.get('chapter',''),
                            "source_text": c.get('source_text',''),
                            "definition": (c.get('definition') or '')[:50],
                            "reason": reason})
            seen_r.add(c['id'])

    # 规则命中 + 真概念保护
    for c in cs:
        if c['id'] in seen_d or c['id'] in seen_r:
            continue
        r = classify_fragment(c['term'])
        if r not in ACCEPT_RULES:
            continue
        defn = c.get('definition') or ''
        # 真概念保护：定义完整(≥30字且判断句式) → REVIEW
        if c['term'] in RULE_SAFE or (len(defn) >= 30 and re.match(r'^(是|指|是指|指的是|指.*的|所谓)', defn.strip())):
            repairs.append({"id": c['id'], "term": c['term'], "chapter": c.get('chapter',''),
                            "source_text": c.get('source_text',''),
                            "definition": defn[:50],
                            "reason": f"规则{ r }但定义完整→真概念保护(REVIEW)"})
            seen_r.add(c['id'])
            continue
        deletes.append({"id": c['id'], "term": c['term'], "chapter": c.get('chapter',''),
                        "source_text": c.get('source_text',''),
                        "definition": defn[:50],
                        "reason": f"规则·{r}"})
        seen_d.add(c['id'])

    json.dump(deletes, open(OUT_JSON, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    json.dump(repairs, open(OUT_RJ, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    L = [f"# Step2 碎片 DELETE 清单", f"\n共 {len(deletes)} 条（确定垃圾）", ""]
    for r in deletes:
        L.append(f"- **{r['term']}** | {r['reason']} | src={r['source_text'][:16] or '空'}")
    with open(OUT_MD, 'w', encoding='utf-8') as f:
        f.write('\n'.join(L))
    L2 = [f"# Step2b 错位归位候选（留给 Step3，不删）", f"\n共 {len(repairs)} 条", ""]
    for r in repairs:
        L2.append(f"- **{r['term']}** | {r['reason']} | chapter={r['chapter']}")
    with open(OUT_RM, 'w', encoding='utf-8') as f:
        f.write('\n'.join(L2))

    print(f"DELETE(确定垃圾): {len(deletes)}")
    print(f"归位候选(Step3): {len(repairs)}")
    print(f"→ {OUT_JSON}\n→ {OUT_MD}\n→ {OUT_RJ}")

if __name__ == '__main__':
    main()
