# -*- coding: utf-8 -*-
"""方向0：南大材料真概念补入库（白名单优先）

背景：南大材料（全考点/方法词典）的概念名已进正典清单（3828），但定义入库仅 91 条。
上一轮 extract_missing_concepts 的 is_noise 误删真概念（主体间性/情感能量等），
find_definition 未适配全考点【年份】/年份直连/`-2019` 格式。

本脚本白名单优先：
1. 取 _canonical_names.json 中 S0/A 级 且 sources 含南大源 的概念
2. 减去当前 concepts.json 已有（term 精确/归一）
3. find_definition 从南大源定位定义（复用 concept_utils 修复版）
4. 定义 ≥25 字 → 入库候选；方法源 15≤len<25 且完整句 → short_def_review 人工清单

输出: D:/workspace/_extracted_nanda.json
      [{term, priority, sources, definition, source_text, def_len}]
用法: python pipeline/extract_nanda_concepts.py [--dry-run] [--min-def-len 25]
"""
import os, sys, io, re, json, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from pipeline.utils.concept_utils import (find_definition, is_fragment_term, is_question,
                                          norm_for_dedup, SCHOLAR_NAMES)

CANON = "D:/workspace/_canonical_names.json"
CONCEPTS = "D:/workspace/sociology-kaoyan-app/web/data/concepts.json"
OUT = "D:/workspace/_extracted_nanda.json"

QUANKAODIAN_DIR = "D:/workspace/_nanda_docx"
XMIND_DIR = "D:/workspace/_nanda_xmind"

# 南大源标识 → 文件路径（正典清单 sources 里的标识）
SOURCE_FILES = {
    "南大_方法真题考点": os.path.join(QUANKAODIAN_DIR, "社会研究方法_方法-真题考点.txt"),
    "南大_方法名词解释综合": os.path.join(QUANKAODIAN_DIR, "方法_社会研究方法--名词解释综合.txt"),
}

# 白名单额外排除（明确噪声，即使正典清单标记了 A 也剔除）
EXTRA_NOISE = {
    "定义、步骤、注意事项","定义、步骤、过程、作用","定义、作用","框架图","真题汇总","真题解析",
    "概念的操作化","抽样框/抽样范围","分析单位","作用与重要性","要求与问题","过程与步骤",
    "与其他抽样方法的区别","定义、步骤","适用条件","适用","具体做法","答题要点","参考答案",
    "答案要点","论述要点","简答要点","名词解释要点","本章小结","知识拓展","思考与练习",
    "示例1","示例2","例1","例2","例3","记忆口诀","步骤","注意事项","定义","含义","作用","特点",
    "不同","优点","缺点","实质","产生原因","后果","修改","原因","结果","影响","目的","目标",
    "做法","方式","方法","基本内容","主要内容","简单评价","历史地位","评价","总结","概述",
    "参考答案（约650字）","典型问题示例","另外注意","严格匿名与保密承诺",
    "多段抽样的优缺点","对敏感问题采用建构性策略","对文化差异的系统性忽视",
    "对同一概念的文化解读错位","允许“拒绝回答”选项","专家评审与认知访谈",
    "场景介入互动","学术效度危机","利益集团的隐性在场","定性研究的策略","定量研究的工具",
    "定性研究的工具","封面信缺陷","研究设计","研究实施","研究结论","研究局限",
    "不同之处","不同之处在于","不同之处如下","不同之处有如下四点","二者的不同之处如下两点",
    "一是话语对象","二是述说模态","三是概念","三种结果","三者的关系","两者","三者","二者",
    "例3（经典研究）","保持现象的整体性","先给出定义","全球化最突出的变化","关于福柯的套路",
    "其他问题","伦理观念","互补关系","亚文化话语的滥用","消除危机的处方",
    "到实地、到现场","重情景、重关联","修正","历史","发展","后台","作用与重要性",
    # 方法真题考点/名词解释综合里的章节小节标题（非概念）
    "分层的比例问题","初稿设计与操作化","抽样框的形成","抽样逻辑","排版与流程问题",
    "提问方式","政策与实践误导","数字和符号","委婉化与去标签化","承担起“转译者”的责任",
    "知识生产的殖民性","研究者的任务","研究问题明确化","示例3","社会产物与社会事实",
    "答案参考","结论的效度边界","职业声望测量的例子","行文要则","选择测量尺度须注意",
    "避免否定与复杂句式","错误问法","概念与测量工具的简单移植","有框但质量差",
    "访问员⇆受访者","访问员的专业培训","读者的任务","看过的继续回答","利益集团",
    "法国学者布迪厄在《区隔","消费转向的社会学意义","涂尔干有关社会分工观点",
    "拓展","定性","核心","核心特征","理论局限","理论贡献",
    "相同","相同之处在于","相同之处如下","相同之处有如下两点","联系","解决",
    "解决措施","设计","起源","逻辑","缺陷","基础","特性","概念与测量工具的简单移植",
    # 南大全考点里的小节标题/学者名（非独立概念）
    "曼海姆-知识社会学","滕尼斯","破坏性实验的例示","社会学主义特征",
    "社区结构","语言性质","符号","宗教的含义与本质",
}

# 真概念 KEEP 白名单（人工核定的真题概念，即使正典清单标记也保留）
# 本清单 = 用户点名的 20 目标 + 南大全考点真题中确认为独立概念者
# 边界项（小节标题/主题短语/学者名）明确不在内：《社会/消费转向的社会学意义/滕尼斯/
# 破坏性实验的例示/社会学主义特征/宗教的含义与本质/社区结构/语言性质/起源/特性/符号/
# 曼海姆-知识社会学
KEEP_CONCEPTS = {
    # —— 理论类（南大全考点真题概念）——
    "主体间性","客观文化","文化资本","象征资本","情感能量","失范性自杀","实质理性",
    "文化工业","时尚","社会学想象力","权力精英理论","自然态度的悬置","因果多元论",
    "两级构想","显在利益和潜在利益","显群体与准群体","归纳法","常规姿态",
    "穷人","文化悲剧","文化自觉","测不准效应","研究问题明确化",
    # —— 方法类（南大方法词典真题概念）——
    "沟通的有效性","预设的有效性","随机化回答技术","卡片选择法","主体论","过滤性问题",
}

# 正典清单中 明确是"真题题型/章节"而非概念的 A 级项（人工维护白名单）
TITLE_ONLY = {
    "一、名词解释","二、简答题","三、论述题","真题汇总","真题解析","框架图","名词解释",
    "简答题","论述题","计算题","设计题","真题","参考答案","答案输出","考点",
}

def load_canon():
    return json.load(open(CANON, encoding='utf-8'))

def load_concepts():
    return json.load(open(CONCEPTS, encoding='utf-8'))

def is_title_phrase(term):
    """书名著/主题短语（非概念）：
    - 《社会》、《规训与惩罚》 等书名
    - 帕森斯的行动理论 / 宗教的含义与本质 等 "X的Y" 主题短语
    - 怎么做 / 在多元建构视角下 等描述短语
    """
    t = term.strip()
    if re.match(r'^《', t):  # 《社会 / 《规训与惩罚》 书名（残缺书名也是）
        return True
    if re.match(r'^怎么|^如何|^为何|^为什么|^为什么有', t):
        return True
    if re.match(r'^在.{2,8}视角下|^从.{2,8}角度|^就.{2,10}而言', t):
        return True
    # 学者名 + 的 + 主题：帕森斯的行动理论 / 布迪厄的权力场域（主题短语，非概念）
    if re.match(rf'^({"|".join(re.escape(s) for s in sorted(SCHOLAR_NAMES, key=len, reverse=True))})的', t):
        return True
    if re.search(r'[一-鿿]{1,8}的(意义|含义|本质|理论|思想|观点|概念|定义|作用|功能|结构|过程|内容|特点|特征|方法|问题|研究|分析|批评|批判|发展|变迁|演变|影响|局限|不足|优点|缺点|地位|来源|分类|类型|形式|阶段|条件|目的|原因|结果|途径|视角|框架|模式|命题|假说|立场|体系|维度|方面|层面|环节|关系|区别|比较|对比|异同)', t):
        return True
    if re.match(r'^(本质|含义|定义|特点|特征|作用|意义|目的|内容|结构|方法|来源|分类|条件|背景|过程|步骤|方式|适用范围|优点|缺点|局限|不足|优势|特点)', t):
        return True
    # 2 字纯泛化词（不杀"时尚/语言/基础/定理"等真概念——宁可保留进人工审）
    if len(t) <= 2 and t in EXTRA_NOISE:
        return True
    return False

def is_true_concept(term):
    """白名单筛选：过问句 + 额外排除，保留真概念

    注意：绝不使用 is_noise() 的"化/性"结尾规则——它会把"主体间性/客观文化/
    实质理性"等以"性/化"结尾的真概念误杀（[[notes-canon-principle]] 踩坑教训）。
    正典清单已过 extract_canonical_names 的 is_concept_term，此处只做定向排除。
    """
    t = term.strip().strip('"“”')
    if not t:
        return False
    # 人工核定真概念白名单 → 直接通过
    if t in KEEP_CONCEPTS:
        return True
    if t in EXTRA_NOISE or t in TITLE_ONLY:
        return False
    if is_title_phrase(t):
        return False
    if is_fragment_term(t):
        return False
    if is_question(t):
        return False
    return True

def resolve_source_path(src):
    """正典清单 sources 标识 → 文件路径

    extract_canonical_names 里 SOURCES 用 f"南大全考点_{f}"，f 本身带 .txt，
    所以 sources 可能已带 .txt 后缀，不能重复拼接。
    """
    if src in SOURCE_FILES:
        return SOURCE_FILES[src]
    if src.startswith("南大全考点_"):
        name = src[len("南大全考点_"):]
        if not name.endswith(".txt"):
            name += ".txt"
        return os.path.join(QUANKAODIAN_DIR, name)
    if src.startswith("南大XMind_"):
        name = src[len("南大XMind_"):]
        if not name.endswith(".txt"):
            name += ".txt"
        return os.path.join(XMIND_DIR, name)
    return None

def main():
    dry_run = "--dry-run" in sys.argv
    min_def_len = 25
    for a in sys.argv:
        if a.startswith("--min-def-len="):
            min_def_len = int(a.split("=")[1])

    canon = load_canon()
    concepts = load_concepts()

    # 已有 term（精确 + 归一）
    existing_terms = {c.get("term", "").strip() for c in concepts}
    existing_norm = {norm_for_dedup(c.get("term", "")) for c in concepts}

    # 白名单：S0/A 级 + sources 含南大 + 当前库缺失
    candidates = []
    for r in canon:
        if r["priority"] not in ("S0", "A"):
            continue
        if not any("南大" in s for s in r["sources"]):
            continue
        term = r["term"].strip().strip('"“”')
        if not term or term in existing_terms or norm_for_dedup(term) in existing_norm:
            continue
        if not is_true_concept(term):
            continue
        candidates.append(r)
    print(f"白名单候选（S0/A + 南大源 + 缺失 + 过噪声）: {len(candidates)}")

    # 定义定位
    _cache = {}
    def get_text(path):
        if path not in _cache:
            _cache[path] = open(path, encoding="utf-8").read() if path and os.path.exists(path) else ""
        return _cache[path]

    found, not_found, short_review = [], [], []
    for r in candidates:
        term = r["term"].strip().strip('"“”')
        definition = None
        src_used = None
        # 搜索源：优先全考点，其次方法词典
        search_srcs = sorted(r["sources"], key=lambda s: (0 if "全考点" in s else 1 if "XMind" in s else 2))
        for src in search_srcs:
            path = resolve_source_path(src)
            text = get_text(path)
            if not text:
                continue
            d = find_definition(text, term)
            if d:
                definition = d
                src_used = src
                break
        rec = {"term": term, "priority": r["priority"], "sources": r["sources"]}
        if definition:
            rec["definition"] = definition
            rec["source_text"] = src_used
            rec["def_len"] = len(definition)
            if len(definition) >= min_def_len:
                found.append(rec)
            else:
                # 短定义 → short_def_review
                rec["reason"] = f"定义仅{len(definition)}字（<{min_def_len}）"
                short_review.append(rec)
        else:
            rec["reason"] = "源中未定位到定义"
            not_found.append(rec)

    print(f"\n定义达标(≥{min_def_len}字): {len(found)}")
    print(f"定义过短(需人工审): {len(short_review)}")
    print(f"未找到定义: {len(not_found)}")

    if found:
        print(f"\n提取成功（{len(found)} 条）:")
        for r in found:
            print(f"  {r['term']} [{r['source_text'].split('/')[-1][:40]}] {r['def_len']}字 | {r['definition'][:38]}")
    if short_review:
        print(f"\n短定义清单（{len(short_review)} 条，人工判断是否入库）:")
        for r in short_review:
            print(f"  {r['term']} [{r['def_len']}字] | {r['definition'][:40]}")
    if not_found:
        print("\n未找到（可跳过/DeepSeek）:")
        print("  ", [r["term"] for r in not_found[:25]])

    # 目标概念覆盖率检查
    targets = ["主体间性","客观文化","文化资本","象征资本","情感能量","失范性自杀","实质理性","文化工业",
               "时尚","社会学想象力","权力精英理论","自然态度的悬置","因果多元论","国家结构","卡片选择法",
               "随机化回答技术","沟通的有效性","预设的有效性","主体论","过滤性问题"]
    got = {r["term"] for r in found + short_review}
    missing_t = [t for t in targets if t not in got]
    print(f"\n目标概念覆盖: {len(targets)-len(missing_t)}/{len(targets)}")
    if missing_t:
        print("  未覆盖:", missing_t)

    if dry_run:
        print("\n[dry-run] 不写文件")
        return

    out_data = found + short_review  # 短定义也输出，交由 apply 时人工筛选
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out_data, f, ensure_ascii=False, indent=1)
    print(f"\n→ {OUT} ({len(out_data)} 条)")

if __name__ == "__main__":
    main()
