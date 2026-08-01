# -*- coding: utf-8 -*-
"""REVIEW 审核判定：杨善华下卷碎片（人工逐条审出）+ 垃圾特征检测

输入: D:/workspace/_restructure_classification.json
输出: D:/workspace/_restructure_final.json (classification 更新为 KEEP/DELETE)
"""
import json, sys, io, re, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

CLASS = "D:/workspace/_restructure_classification.json"
OUT = "D:/workspace/_restructure_final.json"

# 杨善华下卷碎片（2026-08-01 人工逐条审核 291 条，标记 DELETE 的 87 条）
# 判定标准：教材分析维度/理论内部变量/描述性短语，非独立可考名词解释
YANSHANHUA_FRAGMENTS = {
    # 科尔曼交换论变量（第一批 14-17）
    "控制分布","资源价值","行动者的实力","事件的结果",
    # 帕森斯/行动理论分析维度（第一批 32-49）
    "辩证张力","行动的偶然性","基本现象","相应真理论","更佳论据的力量",
    "单向理解","单向理解模式","商品价值观","策略性行动分析",
    "控制的辩证关系","结构性特征","矛盾",
    # 吉登斯碎片（第一批 28、第二批 83-87）
    "谋划","单线压缩","对应压缩","规范错觉","调适概念","时间歪曲",
    # 贝克风险碎片（第一批 92-94）
    "风险的定义关系","控制逻辑",
    # 贝克/全球化碎片（第二批 101-118）
    "标准化的充分就业体系","灵活多元的、不充分就业体系","国际化","为自己工作的人",
    "无知","公民工作","生活美学家","角落市场","虚拟纳税人","社会企业家",
    # 布迪厄碎片（第二批 121-145）
    "社会正义论","唯理论主义","极端经验主义","经院观点","哲学升华",
    "符号支配的资本和工具","中央集权资本","预存","筹划","再生产",
    # 埃利亚斯碎片（第二批 150-187）
    "投入与超脱","过程性社会学模式","行为手册","内部稳定过程","王室机制","闲言碎语",
    "贬损化","理想化","投入","超脱","现实适当性","异治性","它-功能","我们-功能",
    "基本控制的三重体系","取向方式","自我驯化","孤立主义的二元论","还原主义的一元论",
    "过程还原","我群卡理斯玛","内在性",
    # 福柯碎片（第三批 202-233）
    "主体的条件","客体的条件","生产性的实践","人体的解剖政治","指出危险的批判",
    "全能型的知识分子","从事专门研究的知识分子","不可容忍","可见性政治","接力",
    "精神品质","精神锻炼","没有先验主体的康德主义","逾越","姿态",
    # 布希亚碎片（第三批 242-278）
    "父权制室内设计","现代室内设计","室内环境的结构","功能性概念","古物收藏",
    "收藏式占有","收藏的自恋","机器人","增长","现代意义的死亡","缓慢的死亡",
    "价值之分裂的阶段","超性状态","定局性对策","客体的胜利","大众的抵抗","主体",
    "传媒的范围","散点监视",
    # 鲍曼碎片
    "病因学神话","副产品",
}

def garbage_features(term, definition=""):
    """明确垃圾特征"""
    if re.match(r'^[①②③④⑤⑥⑦⑧⑨⑩\d]', term):
        return True
    if re.search(r'\n', term):
        return True
    if re.search(r'[？?。，,！!；;]', term) and len(term) > 10:
        return True
    # 残句：term 以"的"结尾（定义拆分残句）
    if term.endswith("的"):
        return True
    return False

def main():
    data = json.load(open(CLASS, encoding='utf-8'))
    changes = collections.Counter()
    for d in data:
        if d["classification"] != "REVIEW":
            continue
        term = d["term"]
        source = d.get("source_text", "") or ""
        is_ysh = "杨善华_下卷" in source
        if is_ysh and term in YANSHANHUA_FRAGMENTS:
            d["classification"] = "DELETE"
            d["reason"] = "杨善华下卷背景碎片(人工审核)"
            changes["碎片"] += 1
        elif garbage_features(term):
            d["classification"] = "DELETE"
            d["reason"] = "垃圾特征"
            changes["垃圾"] += 1
        else:
            d["classification"] = "KEEP"
            d["reason"] = "REVIEW通过(人工/规则)"
            changes["保留"] += 1

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

    print("REVIEW 审核结果:")
    for k, v in changes.items():
        print(f"  {k}: {v}")
    print()
    print("最终分类分布:")
    final = collections.Counter(d["classification"] for d in data)
    for k in ("CANON", "SYNONYM", "KEEP", "DELETE"):
        print(f"  {k}: {final.get(k, 0)}")
    print(f"总保留: {final.get('CANON',0)+final.get('SYNONYM',0)+final.get('KEEP',0)} / {len(data)}")
    print(f"→ {OUT}")

if __name__ == "__main__":
    main()
