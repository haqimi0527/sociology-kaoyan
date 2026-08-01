# -*- coding: utf-8 -*-
"""概念合并方案 Step3：错位概念修复清单（Explore 报告编码）

错位 = 概念挂在错误学者下。修复动作：改 concepts.json 的 chapter 字段归位。
原则（Explore 报告）：判定以 definition 内容为准，proponent 字段不可信。

输出:
  _report_misplaced_fix.json/.md  全部错位候选 {term, 现挂chapter, 应归, 理由, 归属类型}
"""
import os, sys, io, re, json, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

CONCEPTS = "D:/workspace/sociology-kaoyan-app/web/data/concepts.json"
OUT_JSON = "D:/workspace/_report_misplaced_fix.json"
OUT_MD = "D:/workspace/_report_misplaced_fix.md"

# taxonomy 已有学者节点（可直接归位）
# 应归学者→时期（不在 taxonomy 45 学者时兜底到"其他XX学者"）
OTHER_ERA = {
    "诺尔-诺依曼": "现代", "默顿/斯托福": "现代", "怀特": "现代", "伯林": "当代",
    "戴维·哈维": "当代", "凡勃伦": "古典", "埃尔德": "当代", "霍布斯/洛克/卢梭": "古典",
    "孟德斯鸠": "古典", "普雷维什": "当代", "笛卡尔": "古典", "笛卡儿": "古典", "康德": "古典",
    "哈耶克": "当代", "贝尔": "当代", "柯林斯": "现代", "库恩": "现代", "贝克尔/勒默特": "现代",
    "艾森斯塔德": "现代", "亚彻": "当代", "葛兰西": "现代", "卢卡奇": "现代", "胡塞尔/舒茨": "现代",
    "安德森": "当代", "莫斯": "现代", "拉什": "当代", "伯杰和鲁克曼": "现代",
    "斯梅尔塞": "现代", "钱帕基": "当代", "传统分化理论": "现代", "艾森斯塔德系": "现代",
    "卢曼/帕森斯": "现代", "芒奇系": "现代", "芒奇": "现代", "鲍姆和莱切尼尔": "现代",
    "苏里": "现代", "罗西": "现代", "费孝通": "当代",
}
OTHER_FALLBACK = {"古典": "理论/古典时期/其他古典学者/", "现代": "理论/现代时期/其他现代学者/",
                  "当代": "理论/当代时期/其他当代学者/"}

TAXONOMY_SCHOLAR = {
    "哈贝马斯": "理论/当代时期/沟通行动理论/哈贝马斯/", "韦伯": "理论/古典时期/理解社会学/韦伯/",
    "鲍德里亚": "理论/当代时期/后现代理论/鲍德里亚/", "戈夫曼": "理论/现代时期/符号互动论/戈夫曼/",
    "滕尼斯": "理论/古典时期/社群与社会/滕尼斯/", "马尔库塞": "理论/现代时期/批判理论（法兰克福学派）/马尔库塞/",
    "阿多诺": "理论/现代时期/批判理论（法兰克福学派）/阿多诺/", "霍克海默": "理论/现代时期/批判理论（法兰克福学派）/霍克海默/",
    "默顿": "理论/现代时期/结构功能主义/默顿/", "斯宾塞": "理论/古典时期/实证主义/斯宾塞/",
    "布迪厄": "理论/当代时期/实践理论/布迪厄/", "米德": "理论/古典时期/其他古典学者/米德/",
    "齐美尔": "理论/古典时期/形式社会学/齐美尔/", "涂尔干": "理论/古典时期/社会学主义/涂尔干/",
    "马克思": "理论/古典时期/历史唯物主义/马克思/", "卢曼": "理论/现代时期/系统理论/卢曼/",
    "贝克": "理论/当代时期/风险社会理论/贝克/", "科尔曼": "理论/当代时期/理性选择理论/科尔曼/",
    "舒茨": "理论/现代时期/现象学社会学与常人方法学/舒茨/", "帕森斯": "理论/现代时期/结构功能主义/帕森斯/",
    "福柯": "理论/当代时期/后结构主义与谱系学/福柯/", "布劳": "理论/现代时期/社会交换理论/布劳/",
    "霍曼斯": "理论/现代时期/社会交换理论/霍曼斯/", "鲍曼": "理论/当代时期/后现代理论/鲍曼/",
    "吉登斯": "理论/当代时期/结构化理论/吉登斯/", "埃利亚斯": "理论/当代时期/型构/过程社会学/埃利亚斯/",
    "亚历山大": "理论/当代时期/其他当代学者/亚历山大/", "卡斯特": "理论/当代时期/网络/信息社会理论/卡斯特/",
    "拉图尔": "理论/当代时期/行动者网络理论/拉图尔/", "列斐伏尔": "理论/当代时期/其他当代学者/列斐伏尔/",
}

# {term: (应归, 理由, 归属类型)}
# 归属类型: scholar(归taxonomy学者) / other(归非taxonomy学者→其他节点) / method(归方法) / delete(建议删)
MISPLACED = {
    # 韦伯名下
    "沟通行为": ("哈贝马斯", "definition明言哈氏,韦伯错挂", "scholar"),
    "拟象秩序": ("鲍德里亚", "定义即四种拟象秩序,符号学拟象理论", "scholar"),
    "沉默的大多数": ("诺尔-诺依曼", "当代传媒化大众概念,非古典韦伯", "other"),
    "相对剥夺": ("默顿/斯托福", "社会比较经典命题,非韦伯", "other"),
    "绝对剥夺": ("默顿/斯托福", "与相对剥夺配套", "other"),
    "组织人": ("怀特", "《组织人》同名著作核心概念", "other"),
    "积极自由": ("伯林", "proponent=伯林", "other"),
    "谋划": ("亚历山大", "proponent=亚历山大", "scholar"),
    # 涂尔干名下
    "斯宾塞的自由竞争论": ("斯宾塞", "概念即斯宾塞的竞争论", "scholar"),
    "共同体": ("滕尼斯", "定义主干是滕尼斯共同体vs社会", "scholar"),
    "有效宣称": ("哈贝马斯", "与真理/正当/真诚宣称同家族", "scholar"),
    # 马克思名下
    "时空压缩": ("戴维·哈维", "通信运输技术使时空缩短", "other"),
    "灵活积累": ("戴维·哈维", "哈维提出灵活积累", "other"),
    "必要的压抑": ("马尔库塞", "必要vs额外压抑出自爱欲与文明", "scholar"),
    "炫耀性消费": ("凡勃伦", "proponent=凡勃伦", "other"),
    "本质意志": ("滕尼斯", "Wesenwille,滕尼斯核心", "scholar"),
    "选择意志": ("滕尼斯", "Kürwille", "scholar"),
    "实践理论": ("布迪厄", "proponent=布迪厄", "scholar"),
    "理性": ("科尔曼", "定义即理性行动理论", "scholar"),
    "自由社会制度": ("埃尔德", "proponent=埃尔德,功能主义整合论", "other"),
    # 托克维尔名下
    "社会契约理论": ("霍布斯/洛克/卢梭", "proponent明示", "other"),
    "政体分类原则": ("孟德斯鸠", "proponent=孟德斯鸠", "other"),
    "依附理论": ("普雷维什", "拉美依附理论,proponent明示", "other"),
    "身心二元论": ("笛卡尔", "proponent=笛卡尔", "other"),
    "笛卡儿典范": ("笛卡儿", "proponent=笛卡儿", "other"),
    "先验范畴": ("康德", "proponent=康德", "other"),
    "致命的自负": ("哈耶克", "proponent=哈耶克", "other"),
    "消极自由": ("伯林", "proponent=伯林", "other"),
    "公众家庭": ("贝尔", "proponent=贝尔", "other"),
    "法律的认受性": ("哈贝马斯", "proponent=哈贝马斯", "scholar"),
    "女权主义": ("概论/泛化", "泛化运动标签,非托克维尔概念", "delete"),
    # 米德名下
    "互动仪式链": ("柯林斯", "柯林斯提出", "other"),
    "前台": ("戈夫曼", "表演区域前台与后台", "scholar"),
    "角色距离": ("戈夫曼", "拟剧论个人与角色差距", "scholar"),
    "剧情": ("戈夫曼", "预先建立的行动模式/剧组", "scholar"),
    # 布鲁默名下
    "补救表演": ("戈夫曼", "拟剧论表演类型", "scholar"),
    "理想化表演": ("戈夫曼", "拟剧论表演类型", "scholar"),
    "表演框架": ("戈夫曼", "拟剧论框架", "scholar"),
    "神秘化表演": ("戈夫曼", "拟剧论表演类型", "scholar"),
    "误解表演": ("戈夫曼", "拟剧论表演类型", "scholar"),
    "衣阿华学派": ("库恩", "衣阿华学派为库恩所创", "other"),
    "心智": ("米德", "Mind,Self and Society", "scholar"),
    # 戈夫曼名下
    "标签理论": ("贝克尔/勒默特", "越轨研究标签理论", "other"),
    "情感能量": ("柯林斯", "柯林斯提出", "other"),
    # 帕森斯名下
    "中轴原理": ("贝尔", "贝尔的理论", "other"),
    "启蒙辩证法": ("阿多诺/霍克海默", "法兰克福工具理性批判", "scholar"),
    "利益群体": ("艾森斯塔德", "proponent=艾森斯塔德", "other"),
    "利益关系结构": ("艾森斯塔德", "定义明言艾森斯塔德提出", "other"),
    "情感筛选事实": ("当代传媒", "非帕森斯,传媒信息筛选概念", "delete"),
    # 达伦多夫名下
    "利益群体结构": ("艾森斯塔德", "proponent明示", "other"),
    # 霍克海默名下
    "形态衍生": ("亚彻", "morphogenesis,proponent明示", "other"),
    "新自由知识分子": ("葛兰西", "proponent=葛兰西", "other"),
    "物化": ("卢卡奇", "卢卡奇历史与阶级意识核心", "other"),
    # 鲍德里亚名下
    "价值中立社会研究": ("韦伯", "定义即价值中立", "scholar"),
    "互为主观性": ("胡塞尔/舒茨", "主体间性是现象学概念", "other"),
    # 鲍曼名下
    "选择性亲和关系": ("韦伯", "elective affinity韦伯经典概念", "scholar"),
    "想象的共同体": ("安德森", "同名专著核心概念", "other"),
    # 布迪厄名下
    "型构社会学": ("埃利亚斯", "埃利亚斯核心方法论", "scholar"),
    "内局群体与外局群体": ("埃利亚斯", "埃利亚斯权力观", "scholar"),
    "礼物交换理论": ("莫斯", "莫斯《礼物》混融", "other"),
    "模仿世界": ("鲍德里亚", "proponent=布希亚/鲍德里亚", "scholar"),
    "社会测量": ("方法", "方法论泛化术语", "method"),
    # 吉登斯名下
    "风险社会": ("贝克", "贝克世界风险社会", "scholar"),
    "风险文化": ("拉什", "proponent=拉什", "other"),
    # 贝克名下
    "国际合作": ("泛化", "proponent=科尔曼,泛化政策术语", "delete"),
    # 科尔曼名下
    "囚徒困境": ("博弈论", "博弈论通用模型", "other"),
    # 福柯名下
    "三权分立": ("孟德斯鸠", "proponent明示", "other"),
    "社会建构主义": ("伯杰和鲁克曼", "proponent明示", "other"),
    "科学主义": ("泛化标签", "proponent=哈贝马斯(批判对象)", "delete"),
    # 列斐伏尔名下（系统性污染）
    "受挫的分化": ("斯梅尔塞", "proponent明示", "other"),
    "不平等的分化": ("钱帕基", "proponent明示", "other"),
    "压力-分化模式": ("传统分化理论", "非列斐伏尔", "other"),
    "问题-解决模式": ("传统分化理论", "非列斐伏尔", "other"),
    "利益冲突模式": ("艾森斯塔德系", "权力/分化理论", "other"),
    "权威合法化模式": ("卢曼/帕森斯", "权力符号化合法化", "other"),
    "行动领域": ("芒奇系", "对照帕森斯AGIL", "other"),
    "微观互动": ("芒奇", "proponent明示", "other"),
    "社会过程": ("艾森斯塔德", "proponent明示", "other"),
    "逆分化": ("鲍姆和莱切尼尔", "proponent明示", "other"),
    "社团结构": ("苏里", "proponent明示", "other"),
    "符号的复杂性": ("芒奇", "proponent明示", "other"),
    "文化决定论": ("罗西", "proponent明示", "other"),
    "文化自觉": ("费孝通", "费孝通提出", "other"),
    "整体方法论": ("泛化", "跨国际比较宏观分析", "delete"),
}

def main():
    cs = json.load(open(CONCEPTS, encoding='utf-8'))
    by_term = {c['term']: c for c in cs}

    rows = []
    found, missing = 0, []
    for term, (target, reason, typ) in MISPLACED.items():
        c = by_term.get(term)
        if not c:
            missing.append(term)
            continue
        if typ == "scholar":
            new_ch = TAXONOMY_SCHOLAR.get(target, "理论/当代时期/其他当代学者/")
        elif typ == "method":
            new_ch = "方法/方法论基础/"
        elif typ == "delete":
            new_ch = "(删除候选)"
        else:
            era = OTHER_ERA.get(target, "当代")
            new_ch = OTHER_FALLBACK[era]
        rows.append({"term": term, "id": c['id'], "now_chapter": c.get('chapter',''),
                     "target": target, "new_chapter": new_ch, "type": typ,
                     "reason": reason, "definition": (c.get('definition') or '')[:40]})
        found += 1

    json.dump(rows, open(OUT_JSON, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    grp = collections.Counter(r['type'] for r in rows)
    L = [f"# Step3 错位概念修复清单", f"\n共 {len(rows)} 条（含归位/删除）", f"未匹配: {missing}", ""]
    for typ in ("scholar", "method", "other", "delete"):
        sub = [r for r in rows if r['type'] == typ]
        if not sub:
            continue
        L.append(f"\n## {typ} ({len(sub)})")
        for r in sub:
            mark = "→删除" if typ == "delete" else f"→{r['new_chapter']}"
            L.append(f"- **{r['term']}** [{r['now_chapter']}] {mark} | {r['reason']}")
    with open(OUT_MD, 'w', encoding='utf-8') as f:
        f.write('\n'.join(L))

    print(f"错位候选: {len(rows)} (未匹配 {len(missing)})")
    print(f"  归taxonomy学者: {grp['scholar']}")
    print(f"  归方法: {grp['method']}")
    print(f"  归其他(需决策): {grp['other']}")
    print(f"  删除候选: {grp['delete']}")
    print(f"→ {OUT_JSON}\n→ {OUT_MD}")

if __name__ == '__main__':
    main()
