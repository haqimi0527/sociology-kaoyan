# -*- coding: utf-8 -*-
"""正典概念清单提取 v1（规整源正则提取，散文源后续 DeepSeek 补充）

输入: 四套体系规整源（马工程大纲 / 人大名词解释 / 华中师 txt / 南大全考点 DOCX）
输出: D:/workspace/_canonical_names.json
  [{"term": "社会形态论", "sources": ["马工程考试大纲"], "priority": "S0"}]
  同名概念合并 sources。

用法: python pipeline/extract_canonical_names.py [--dry-run]
"""
import os, sys, io, re, json, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

OUT = "D:/workspace/_canonical_names.json"

# 问句/主题过滤词（概念名不应包含）
QUESTION_WORDS = r"试述|论述|简述|比较|分析|如何|何为|为什么|谈谈|评价|区别|异同|关系如何|意义|地位|作用|特征|特点|立场|影响|条件|方法|原则|类型|结构|过程|途径|功能|形式|内容|要求|维度|层面|表现"

# 常见垃圾词（非概念）
GARBAGE_TERMS = {"定义","原因","作用","特点","含义","类型","意义","背景","过程","方法","比较","补充","概念",
                 "属性","功能","特征","原则","内容","结构","性质","来源","分类","目的","阶段","步骤","条件",
                 "研究","个人","群体","社会","问题","规律","理论","观点","范围","角度","区别","关系","要求",
                 "意义","作用","结论","要点","条目","题解","答","答案","真题","真题汇总","真题解析","真题分析",
                 "参考答案","答案输出","考点","复习笔记","目录","章节","思考题","练习题","小结","本章重点"}

def clean_term(t):
    """清洗概念名：去 OCR 残渣、去首尾符号、压空格"""
    t = t.strip()
    t = re.sub(r'[　 ]+', '', t)          # 去全角/半角空格
    t = t.lstrip('*#△^←→√※.·、—-—|\t')
    t = t.rstrip('*#△^←→√※.·、—-—:：|\t')
    t = re.sub(r'^(第[一二三四五六七八九十百\d]+[章节篇]?)', '', t)  # 去章节头
    return t.strip()

def is_question(t):
    """判断是否为问句/主题（非概念名）"""
    if re.match(r'^(简述|论述|试述|试论述|简单论述|比较|分析|何谓|何为|如何|为什么|谈谈|详述|评价|结合|举例|区别|辨析|阐释|说明|概括|总结|指出)', t):
        return True
    if re.search(r'(的论述|的研究|的历史地位|和作用|的意义|的特征|及评价|的基本观点|的内容与特征|有关.{0,8}的|的主要观点|之间的关系|异同|的叙述|的阐述|的讨论)', t):
        return True
    # "X的<概念后缀词>" 主题（帕森斯的行动理论/默顿对结构功能主义的发展和超越）
    if re.search(r'[一-鿿]{2,8}的(理论|命题|研究|思想|观点|意义|作用|地位|分析|框架|变迁|发展|批判|结构|特点|特征|内容|类型|概念|定义|影响|问题|论述|立场|体系|视角|维度|方面|比较|演化|异同|建设|超越|批判|建构|视角|性质|区分|层次|功能|形式|阶段|过程|途径|来源|分类|模式|方法|因素|层面|环节|命题)', t):
        return True
    # "X的<抽象后缀>" 强排除（韦伯理论体系的缺陷/总加量表的前提/价值中立的对立面）
    if re.search(r'[一-鿿]{2,8}的(缺陷|主题|兴趣|标准|前提|对立面|规定|局限|局限性|问题|范围|程度|方向|部分|来源|特征|特点|作用|意义|原则|要求|条件|因素|影响|结果|原因|方法|途径|手段|形式|过程|内容|功能|性质|地位|角度|层面|之中|之间|之下|框架|类型|分类|概念|定义|假说|假设|规律|趋势|现状|不足|优点|缺点|贡献|价值|合理性|学术兴趣|对立面|初步规定)', t):
        return True
    if re.match(r'^(补充知识点|扩展|专题|思考|练习|本章|本节|小结|拓展)[\-知识点-]', t):
        return True
    if re.match(r'^[一二三四五六七八九十\d]+[、.)．]', t):  # 编号残留
        return True
    return False

def is_concept_term(t):
    """判断是否为合格概念名（过滤问句/主题/噪声）"""
    if len(t) < 2 or len(t) > 12:
        return False
    if t in GARBAGE_TERMS:
        return False
    if re.search(r'[？?。，,！!；;]', t):        # 含句末标点
        return False
    if is_question(t):
        return False
    if re.search(r'^\d', t):                     # 数字开头
        return False
    if re.match(r'^[①②③④⑤⑥⑦⑧⑨⑩⑪⑫]', t):   # 带圈数字开头
        return False
    if re.search(r'^[A-Za-z]', t):               # 英文字母开头（B预测效度）
        return False
    # 描述性短语：以下/方面/来看/表现在/真正/各种/从...的
    if re.search(r'(以下|方面|来看|表现在|的真正|各种|若干|具体|相应|相关|主要|基本|重要|包括|分为|具有|进行|通过|的总体|的各个|各种不同|三个|四个|五种|两种|步骤|环节|要点|作用在于|体现在|取决于|层面|其中|之一|那些|这些|某些)', t):
        return False
    # 重复前缀：戈夫曼-戈夫曼的拟剧分析框架
    if re.match(r'^(.{2,6})[-\-]\1的', t):
        return False
    return True

def norm_for_dedup(t):
    """归一化（用于去重）：全半角、去括号内容、去末尾'理论/思想/概念'"""
    t = t.replace('（', '(').replace('）', ')')
    t = re.sub(r'\(.*?\)', '', t)             # 去括号（含英文/年份）
    t = re.sub(r'[　 ]+', '', t)
    return t

# ---------- 各源 extractor ----------

def extract_gangling(path):
    """马工程考试大纲：识记：X定义；Y定义"""
    text = open(path, encoding='utf-8').read()
    terms = []
    for m in re.finditer(r'识记[:：]\s*([^\n]+)', text):
        seg = m.group(1)
        for item in re.split(r'[；;、]', seg):
            item = re.sub(r'定义$', '', item.strip())
            item = clean_term(item)
            if is_concept_term(item):
                terms.append(item)
    return terms

def extract_noun_mingci(path):
    """人大名词解释/华中师结构图：N．概念名：定义 / N.概念名：定义"""
    text = open(path, encoding='utf-8').read()
    text = re.sub(r'=== [^=]+ ===\n?', '', text)
    terms = []
    # 模式：编号+分隔符 → 概念名 → 冒号
    pat = re.compile(r'(?:^|\n)\s*(\d{1,3})[．.、]+\s*(?:[^：:\n]{0,6}?)\s*([^：:\n]{2,30}?)[：:]')
    for m in pat.finditer(text):
        t = clean_term(m.group(2))
        if is_concept_term(t):
            terms.append(t)
    # 补充：无冒号的编号行（概念名独占一行）
    pat2 = re.compile(r'(?:^|\n)\s*(\d{1,3})[．.、]+\s*(?:[^：:\n]{0,6}?)\s*([^：:\n]{2,20})\s*$')
    for m in pat2.finditer(text):
        t = clean_term(m.group(2))
        if is_concept_term(t):
            terms.append(t)
    # 贾春增模式：N．概念名（提出者）——无冒号，概念名后跟（人名）
    pat3 = re.compile(r'(?:^|\n)\s*(\d{1,3})[．.、]+\s*([^（(：:\n]{2,20})[（(][^）)]{1,10}[）)]')
    for m in pat3.finditer(text):
        t = clean_term(m.group(2))
        if is_concept_term(t):
            terms.append(t)
    return terms

def extract_huazhong_method(path):
    """华中师风笑天方法笔记：N、概念名（social research）：定义"""
    text = open(path, encoding='utf-8').read()
    terms = []
    pat = re.compile(r'(?:^|\n)\s*(\d{1,3})[、.．]\s*([^：:（(\n]{1,30})')
    for m in pat.finditer(text):
        t = clean_term(m.group(2))
        if is_concept_term(t):
            terms.append(t)
    return terms

def extract_quankaodian(path):
    """南大全考点 DOCX：四种格式叠加
    1) 概念名【年份、年份-题型】 / 概念名【补充】
    2) 概念名2009（韦伯格式，年份直连）
    3) 概念名（补充）
    4) 概念名：定义（科塞/其他人物格式）
    """
    text = open(path, encoding='utf-8').read()
    terms = []
    seen = set()
    def add(t):
        t = clean_term(t)
        if is_concept_term(t) and t not in seen:
            seen.add(t)
            terms.append(t)
    # 1) 【】格式：概念名（可能带年份尾）
    pat1 = re.compile(r'(?:^|\n)\s*([^【\n：:]{2,30}?)【([^】\n]+)】')
    for m in pat1.finditer(text):
        add(re.sub(r'20\d{2}\s*$', '', m.group(1)))
    # 2) 年份直连（韦伯）
    pat2 = re.compile(r'(?:^|\n)\s*([一-鿿（）()·\-]{2,25}?)(20[0-9]{2}(?:[-\s、]20[0-9]{2})*)\s*(?:（|$|\n)')
    for m in pat2.finditer(text):
        add(m.group(1))
    # 3) （补充）
    pat3 = re.compile(r'(?:^|\n)\s*([^（\n：:]{2,25}?)（补充）')
    for m in pat3.finditer(text):
        add(m.group(1))
    # 4) 概念名：定义（冒号后 ≥8 字）
    pat4 = re.compile(r'(?:^|\n)\s*([^：:\n【】（）(]{2,15})[:：]\s*[^：:\n]{8,}')
    for m in pat4.finditer(text):
        add(m.group(1))
    return terms

def extract_method_dict(path):
    """南大方法词典：概念名：定义 或 概念名/别名/别名：定义"""
    text = open(path, encoding='utf-8').read()
    terms = []
    pat = re.compile(r'(?:^|\n)\s*([^：:\n]{2,30}?)[：:]\s*[^\n]{8,}')
    for m in pat.finditer(text):
        raw = m.group(1)
        # 斜杠分隔的同义词取第一个
        t = raw.split('/')[0].strip()
        t = clean_term(t)
        if is_concept_term(t) and not re.search(QUESTION_WORDS, t):
            terms.append(t)
    return terms

# 理论家人名黑名单（非概念）
SCHOLAR_NAMES = {"孔德","斯宾塞","马克思","涂尔干","迪尔凯姆","杜尔凯姆","韦伯","齐美尔","帕累托","滕尼斯",
    "托克维尔","帕森斯","默顿","达伦多夫","科塞","米尔斯","阿多诺","马尔库塞","霍曼斯","布劳","米德","布鲁默",
    "戈夫曼","舒茨","加芬克尔","布迪厄","吉登斯","福柯","埃利亚斯","哈贝马斯","鲍德里亚","布希亚","利奥塔",
    "卢曼","贝克","贝尔","科尔曼","鲍曼","费孝通","王思斌","袁方","风笑天","郑杭生","贾春增","侯钧生","杨善华",
    "刘少杰","卢淑华","宋林飞","文军","周晓虹","狄尔泰","李凯尔特","库利","托马斯","佩奇","格奥尔格","埃米尔",
    "安东尼","米歇尔","尤尔根","皮埃尔","塔尔科特","詹姆斯","乌尔里希","诺伯特","奥古斯特","罗伯特","让",
    "杰弗里","米哈伊尔","弗洛伊德","凯恩斯"}

def extract_xmind(path):
    """XMind 节点标题提取概念名（人名/描述性标题已过滤）"""
    terms = []
    for line in open(path, encoding='utf-8'):
        t = line.strip()
        if not t:
            continue
        t = clean_term(t)
        if t in SCHOLAR_NAMES or t.rstrip("（( ").strip() in SCHOLAR_NAMES:
            continue
        # 去掉人名尾注：涂尔干（1858-1917）
        base = re.sub(r'[（(].*?[）)]$', '', t)
        if base in SCHOLAR_NAMES:
            continue
        if is_concept_term(t):
            terms.append(t)
    return terms

# ---------- 主流程 ----------

SOURCES = [
    # (源标识, 优先级, extractor, 路径)
    ("马工程考试大纲", "S0", extract_gangling,
     "D:/workspace/sociology-kaoyan/__extracted__/笔记/马工程《社会学概论》（第2版）考试大纲.txt"),
    ("人大_概论名词解释", "A", extract_noun_mingci,
     "D:/workspace/sociology-kaoyan/__extracted__/方法/人大_概论名词解释.txt"),
    ("人大_巴比方法名词解释", "A", extract_noun_mingci,
     "D:/workspace/sociology-kaoyan/__extracted__/方法/人大_巴比名词解释.txt"),
    ("人大_贾春增名词解释", "A", extract_noun_mingci,
     "D:/workspace/sociology-kaoyan/__extracted__/方法/人大_贾春增名词解释.txt"),
    ("华中师_风笑天方法笔记", "A", extract_huazhong_method,
     "D:/workspace/_exam_texts/华中师_风笑天社会学方法笔记.txt"),
    ("华中师_西方理论简约版结构图", "A", extract_noun_mingci,
     "D:/workspace/_exam_texts/华中师_西方社会学理论简约版结构图.txt"),
    ("南大_方法真题考点", "A", extract_method_dict,
     "D:/workspace/_nanda_docx/社会研究方法_方法-真题考点.txt"),
    ("南大_方法名词解释综合", "A", extract_method_dict,
     "D:/workspace/_nanda_docx/方法_社会研究方法--名词解释综合.txt"),
    # 散文源（整体背诵/理论me/华中师复习笔记等）→ DeepSeek 阶段处理，本轮正则跳过
]

# 全考点 DOCX（动态收集）
QUANKAODIAN_DIR = "D:/workspace/_nanda_docx"
for f in sorted(os.listdir(QUANKAODIAN_DIR)):
    if f.startswith("03.西方社会学理论-全考点") and f.endswith(".txt"):
        SOURCES.append((f"南大全考点_{f}", "A", extract_quankaodian,
                        os.path.join(QUANKAODIAN_DIR, f)))

# XMind 笔记（动态收集）
XMIND_DIR = "D:/workspace/_nanda_xmind"
for f in sorted(os.listdir(XMIND_DIR)):
    if f.endswith(".txt"):
        SOURCES.append((f"南大XMind_{f}", "B", extract_xmind,
                        os.path.join(XMIND_DIR, f)))

def main():
    dry_run = "--dry-run" in sys.argv
    canon = collections.defaultdict(lambda: {"sources": set(), "priority": None})
    priority_order = {"S0": 0, "A": 1, "B": 2, "C": 3}

    for name, prio, fn, path in SOURCES:
        if not os.path.exists(path):
            print(f"[SKIP] {name}: 文件不存在 {path}")
            continue
        try:
            terms = fn(path)
        except Exception as e:
            print(f"[FAIL] {name}: {e}")
            continue
        # 去重 + 登记
        seen_in_source = set()
        new_cnt = 0
        for t in terms:
            key = norm_for_dedup(t)
            if key in seen_in_source:
                continue
            seen_in_source.add(key)
            rec = canon[t]  # 精确 term 合并（同字面）
            rec["sources"].add(name)
            if rec["priority"] is None or priority_order.get(prio, 9) < priority_order.get(rec["priority"], 9):
                rec["priority"] = prio
            new_cnt += 1
        print(f"[OK] {name}: {len(terms)} 原始, {new_cnt} 新")

        # 抽检：每源打印前 5 个
        sample = [t for t in terms[:5]]
        print(f"    抽检: {sample}")

    # 输出
    result = []
    for term, rec in canon.items():
        result.append({
            "term": term,
            "sources": sorted(rec["sources"]),
            "priority": rec["priority"],
        })
    result.sort(key=lambda r: (priority_order.get(r["priority"], 9), r["term"]))

    if dry_run:
        print(f"\n[dry-run] 正典概念名 {len(result)} 个，不写文件")
        from collections import Counter
        pc = Counter(r["priority"] for r in result)
        print("优先级分布:", dict(pc))
        return

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    print(f"\n正典概念名 {len(result)} 个 → {OUT}")
    from collections import Counter
    pc = Counter(r["priority"] for r in result)
    print("优先级分布:", dict(pc))

if __name__ == "__main__":
    main()
