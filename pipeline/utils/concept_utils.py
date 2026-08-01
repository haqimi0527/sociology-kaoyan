# -*- coding: utf-8 -*-
"""概念处理共用规则库（方向3 工具层）

从 extract_canonical_names / extract_missing_concepts / _qa_check 抽取统一：
  - GARBAGE_TERMS / SCHOLAR_NAMES / EXTRA_NOISE 常量
  - clean_term / norm_for_dedup / is_noise / is_question / classify_fragment
  - def_prefix_key / find_definition / add_backup

用法:
  from pipeline.utils.concept_utils import find_definition, is_noise, ...
"""
import os, re, shutil, time, json

# ============ 常量 ============

GARBAGE_TERMS = {
    "定义","原因","作用","特点","含义","类型","意义","背景","过程","方法","比较","补充",
    "概念","属性","功能","特征","原则","内容","结构","性质","来源","分类","目的","阶段",
    "步骤","条件","研究","个人","群体","社会","问题","规律","理论","观点","范围","角度",
    "区别","关系","要求","意义","作用","结论","要点","条目","题解","答","答案","真题",
    "真题汇总","真题解析","真题分析","参考答案","答案输出","考点","复习笔记","目录","章节",
    "思考题","练习题","小结","本章重点","概述","总结","举例","方式","适用","目标","示例",
    "做法","不同之处","相同之处","知识补充","框架图","记忆口诀","具体来说",
}

# 方向0 额外噪声（南大全考点/方法词典里的描述短语标题）
EXTRA_NOISE = {
    "定义、步骤、注意事项","定义、步骤、过程、作用","定义、作用","框架图","真题汇总","真题解析",
    "概念的操作化","抽样框/抽样范围","分析单位","作用与重要性","要求与问题","过程与步骤",
    "与其他抽样方法的区别","定义、步骤","适用条件","适用","具体做法","答题要点","参考答案",
    "答案要点","论述要点","简答要点","名词解释要点","本章小结","知识拓展","思考与练习",
}

# 理论家人名（非概念，XMind/章节里直接出现的）
SCHOLAR_NAMES = {
    "孔德","斯宾塞","马克思","涂尔干","迪尔凯姆","杜尔凯姆","韦伯","齐美尔","帕累托","滕尼斯",
    "托克维尔","帕森斯","默顿","达伦多夫","科塞","米尔斯","阿多诺","马尔库塞","霍曼斯","布劳",
    "米德","布鲁默","戈夫曼","舒茨","加芬克尔","布迪厄","吉登斯","福柯","埃利亚斯","哈贝马斯",
    "鲍德里亚","布希亚","利奥塔","卢曼","贝克","贝尔","科尔曼","鲍曼","费孝通","王思斌","袁方",
    "风笑天","郑杭生","贾春增","侯钧生","杨善华","刘少杰","卢淑华","宋林飞","文军","周晓虹",
    "狄尔泰","李凯尔特","库利","托马斯","佩奇","格奥尔格","埃米尔","安东尼","米歇尔","尤尔根",
    "皮埃尔","塔尔科特","詹姆斯","乌尔里希","诺伯特","奥古斯特","罗伯特","让","杰弗里","米哈伊尔",
    "弗洛伊德","凯恩斯","胡塞尔","萨特","列斐伏尔","拉图尔","亚历山大","卡斯特","波斯特","鲍曼",
    "索罗金","曼海姆","卡西尔","齐美尔","帕克","沃斯","雷德菲尔德","沃勒斯坦","华勒斯坦",
    "奥格本","贝尔纳","默顿","科泽","斯梅尔塞","吉丁斯","沃德","萨姆纳","塔尔德","勒庞",
    "布鲁默","托马斯","兹纳涅茨基","海德格尔","康德","黑格尔","尼采","卢卡奇","葛兰西",
}

# ============ 清洗 ============

def clean_term(t):
    """清洗概念名：去 OCR 残渣、去首尾符号、压空格、去章节头"""
    t = t.strip()
    t = re.sub(r'[　 ]+', '', t)
    t = t.lstrip('*#△^←→√※.·、—-—|　．、|\t')
    t = t.rstrip('*#△^←→√※.·、—-—:：|　|\t')
    t = re.sub(r'^(第[一二三四五六七八九十百\d]+[章节篇]?)', '', t)
    return t.strip()

def norm_for_dedup(t):
    """归一化（用于去重分组）：全半角、去括号内容、去末尾'理论/思想/概念'"""
    t = str(t or '').replace('（', '(').replace('）', ')')
    t = re.sub(r'\(.*?\)', '', t)
    t = re.sub(r'[　 ]+', '', t)
    t = t.strip(' \t\n*#△^←→√※.·、—-—')
    return t

def def_prefix_key(defn, n=60):
    """定义前 n 字（去空白），用于定义查重"""
    return re.sub(r'\s+', '', (defn or ''))[:n]

# ============ 噪声判定 ============

def is_fragment_term(term):
    """碎片/描述短语判定（不含"化/性"结尾规则——避免误杀真概念）

    用于方向0 白名单：只抓"残句/列表项/描述短语"，
    不因结尾"性/化"（主体间性/客观文化）误删真概念。
    """
    t = term.strip().strip('"“”')
    if len(t) < 2:
        return True
    if t in GARBAGE_TERMS:
        return True
    if re.match(r'^(一是|二是|三是|四是|其一|其二|其三|不同之处|三种|两种|具体来说|如下|包括|分为|在于|需要|应该|可以|进行|通过|具有|所谓|检验|测定|分析|比较|阐述|先给出|提供|考虑|高度|重视|强调|注重|突出|结合|针对|围绕|存在|体现|反映|涉及|指出)', t):
        return True
    if re.search(r'(的总体|的各个|的每一个|各种不同|以下几个方面|如下四点|如下三点|如下两个方面|的滥用|的决定|的结果|的条件|的效应|的两者|的三者|的关系|的区别|的异同|之间|之中|之下的)', t):
        return True
    if re.match(r'^例\d+', t) or re.match(r'^[（(]\d+[）)]', t) or re.match(r'^\d+[）)]', t):
        return True
    if re.search(r'[？?。，,！!；;]', t):
        return True
    if re.match(r'^[\d一二三四五六七八九十]+[、.．)]', t):
        return True
    # 编号/序数词短语：三种结果/两者的关系/一是话语对象
    if re.match(r'^(一是|二是|三是|四是|两者|三者|三种|四种|两种|二者的|三者的|几方面的|两个方面的|具体表现在|主要表现|基本特征|基本特点|理论来源|思想来源|现实意义|理论意义|历史意义|积极意义|消极影响|积极影响)', t):
        return True
    return False

def is_noise(term):
    """噪声概念：残句/列表项/描述短语（含"化/性"结尾——用于通用过滤，慎用于白名单）"""
    t = term.strip().strip('"“”')
    if len(t) < 2 or len(t) > 14:
        return True
    if t in GARBAGE_TERMS:
        return True
    if is_fragment_term(t):
        return True
    if t.endswith(("的", "之", "中", "下", "与", "及", "或", "化", "性")):
        return True
    return False

def is_question(t):
    """判断是否为问句/主题（非概念名）"""
    if re.match(r'^(简述|论述|试述|试论述|简单论述|比较|分析|何谓|何为|如何|为什么|谈谈|详述|评价|结合|举例|区别|辨析|阐释|说明|概括|总结|指出)', t):
        return True
    if re.search(r'(的论述|的研究|的历史地位|和作用|的意义|的特征|及评价|的基本观点|的内容与特征|有关.{0,8}的|的主要观点|之间的关系|异同|的叙述|的阐述|的讨论)', t):
        return True
    if re.search(r'[一-鿿]{2,8}的(理论|命题|研究|思想|观点|意义|作用|地位|分析|框架|变迁|发展|批判|结构|特点|特征|内容|类型|概念|定义|影响|问题|论述|立场|体系|视角|维度|方面|比较|演化|异同|建设|超越|批判|建构|视角|性质|区分|层次|功能|形式|阶段|过程|途径|来源|分类|模式|方法|因素|层面|环节|命题)', t):
        return True
    if re.match(r'^(补充知识点|扩展|专题|思考|练习|本章|本节|小结|拓展)[\-知识点-]', t):
        return True
    if re.match(r'^[一二三四五六七八九十\d]+[、.)．]', t):
        return True
    return False

def classify_fragment(term):
    """返回 _qa_check 命中的碎片规则名，无则 None

    覆盖 _qa_check.py 18 条中的概念名/定义碎片类 + 新增泛化词/残句规则。
    """
    t = (term or '').strip()
    d = t  # classify 只针对 term；定义碎片由调用方传定义

    # 泛化词/描述短语（新增，方向1 碎片 DELETE）
    if t in EXTRA_NOISE:
        return "泛化词"
    if re.match(r'^(过程|作用|要求|步骤|定义|特点|含义|类型|意义|背景|条件|原则|方法|内容|结构|性质|来源|分类|目的|阶段)$', t):
        return "泛化词"
    # 纯虚词
    if t in ("解决办法","总的来说","实际上","因素之一","是一种扩张","主要","需一步","派生物","东西便被","可以递减到零"):
        return "纯虚词"
    # 概念名含标点
    if re.search(r'[，。！？：；、]', t):
        return "含标点"
    # 概念名含括号
    if re.search(r'[（）()]', t):
        return "含括号"
    # 概念名含笔记符号
    if re.search(r'[→←↑↓△※\^☆★○●□■]', t):
        return "含笔记符号"
    # 概念名>10字（白名单除外）
    if len(t) > 10 and t not in ('新教伦理与资本主义精神','社会静力学和社会动力学','强制性协作组合','强制性协调组合'):
        return "概念名>10字"
    # 概念名教学前缀
    if re.match(r'^(又称|也叫|亦称|即|换言之|所谓|指的是|定义为|被称|称之为|简言之)', t):
        return "教学前缀"
    # 概念名教学后缀
    if re.search(r'(的概念|的含义|的特点|的特征|的论述|的阐述|的总结|的概述|的归纳|的定义|的区别|的联系|的分类|的类型|的作用|的功能|的意义)$', t):
        return "教学后缀"
    # 概念名句子碎片
    if re.match(r'^(又是|而是|还是|正是|就是|不是|只是|也是|都是)', t) or re.match(r'^(进行|通过|根据|对于|关于|由于|然后|所以|但是|以及|或者|可以|应该|必须|需要)', t) or re.search(r'(及其|以及|它们|这是|那是|这种|那种|某个|某些)', t):
        return "句子碎片"
    # 概念名导航文本
    if re.match(r'^(详见|参见|见下|如下|下述|本章|本节|上一章|下一章|第[一二三四五六七八九十]代$)', t) or re.search(r'(详见|参见|如下|卡片上|小节)', t):
        return "导航文本"
    # 编号前缀
    if re.match(r'^\d+[\.\、\)]\s*', t):
        return "编号前缀"
    # 定义开头残句（只针对 term 本身传进来的情况）
    if re.match(r'^[了着过）\)，,、。！…]', t):
        return "开头残句"
    return None

# ============ find_definition ============

# 定义引导行（真题解析段）：`答案输出：` 等，不算定义内容
DEF_LEADERS = r'^(答案输出|真题解析|名词解释|定义|含义|内容|特点|特征|解释|说明|要点|简答|论述)[:：]?\s*$'

def _collect_definition(text, term, format_name):
    """收集所有匹配的定义候选（含跨行续接），返回 [(def_text, start_pos), ...]

    format_name: colon | year | newline
    """
    t = re.escape(term)
    L = r'(?<![一-鿿])'
    cands = []

    if format_name == "colon":
        # `概念名：定义`（同行） / `概念名：\n定义`（换行）
        pat = re.compile(rf'(?:^|\n)\s*(?:[\d一二三四五六七八九十]{{1,3}}[．.、]\s*)?{L}{t}[:：]\s*([^\n]{{8,}})')
        for m in pat.finditer(text):
            cands.append((m.group(1).strip(), m.end()))
        pat2 = re.compile(rf'(?:^|\n)\s*(?:[\d一二三四五六七八九十]{{1,3}}[．.、]\s*)?{L}{t}[:：]\s*\n\s*([^\n]{{8,}})')
        for m in pat2.finditer(text):
            cands.append((m.group(1).strip(), m.end()))
    elif format_name == "year":
        # `概念名【年份】\n定义` / `概念名2022\n定义` / `概念名-2019\n定义`
        # / `概念名2020（尾注）\n定义` / `概念名【年份】-动乱型自杀\n定义`（尾注/引导行）
        # 捕获任意非空行，引导行/目录行在 _clean_definition 处理
        pat = re.compile(
            rf'(?:^|\n)\s*(?:[\d一二三四五六七八九十]{{1,3}}[．.、]\s*)?{L}{t}'
            rf'(?:【[^】]*】[^\n]*|-20\d{{2}}[^\n]*|20\d{{2}}(?:（[^）]*）)?(?:[-\s、]20\d{{2}})*[^\n]*)?'
            rf'\n\s*([^\n]+)')
        for m in pat.finditer(text):
            cands.append((m.group(1).strip(), m.end()))
    elif format_name == "newline":
        # `概念名\n定义`
        pat = re.compile(rf'(?:^|\n)\s*(?:[\d一二三四五六七八九十]{{1,3}}[．.、]\s*)?{L}{t}[^\S\n]*\n\s*([^\n]+)')
        for m in pat.finditer(text):
            cands.append((m.group(1).strip(), m.end()))
    return cands

def _is_index_line(line):
    """目录行/索引行：含【年份】标记且无句号（`机械团结【2022/2009】` 目录，非定义）"""
    if not re.search(r'【[^】]+】', line):
        return False
    # 含句号 → 是定义内容，不是目录
    if re.search(r'[。.]', line):
        return False
    return True

def _trim_def_tail(defn):
    """裁剪定义尾部混入的下一概念头/字数标注"""
    if not defn:
        return defn
    # 1) `（220字）` 字数标注 → 切到标注前
    m = re.search(r'[（(【\[]\s*\d{1,4}\s*字\s*[）)】\]]', defn)
    if m:
        defn = defn[:m.start()].rstrip('。！？，,；; ')
    # 2) 尾部混入下一概念头 `概念名2020` `概念名【年份】`（中文名+年份/标注直连）
    m = re.search(r'[一-鿿]{2,12}(?:20\d{2}|【[^】]{1,10}】)\s*(?:（[^）]*）)?$', defn)
    if m:
        # 若该段前面是完整句号，切到句号后
        cut = defn[:m.start()]
        last_period = max(cut.rfind('。'), cut.rfind('！'), cut.rfind('？'))
        if last_period >= 0:
            defn = cut[:last_period + 1]
    return defn

def _clean_definition(first_line, text, start):
    """处理首行引导词 + 跨行续接，返回完整定义；目录行返回 None"""
    # 目录行（含【】无句号）→ 丢弃
    if _is_index_line(first_line):
        return None
    # 首行是引导行（答案输出：/真题解析：）→ 取下一行作为定义开头
    if re.match(DEF_LEADERS, first_line.strip()):
        rest = text[start:]
        lines = rest.split('\n', 2)
        if len(lines) >= 2:
            first_line = lines[1].strip()
            start = start + len(lines[0]) + 1
    # 再查一次引导行后的行是否还是目录
    if _is_index_line(first_line):
        return None
    d = _continue_paragraph(text, start, first_line)
    return _trim_def_tail(d)

def _continue_paragraph(text, start, first_line):
    """跨行续接定义：后续行若非新概念头/编号/空行/总结句则并入，最多续 2 行"""
    parts = [first_line]
    rest = text[start:]
    lines = rest.split('\n', 5)[:5]
    added = 0
    for ln in lines[1:]:
        s = ln.strip()
        if not s:
            break
        # 字数标注/标记：`（220字）` `【235字】` `【补充】` `【待补充】`
        # （注意：`(1)xxx` 列表项不算，必须是"数字+字"或【补充】类标记）
        if re.search(r'[（(【\[]\s*\d{1,4}\s*字\s*[）)】\]]|【[^】]*(补充|待|完)[^】]*】', s):
            break
        # 书名号开头（下一概念/著作）
        if re.match(r'^《', s):
            break
        # 新概念头：`概念名：` 或 `概念名：定义`（冒号后紧跟内容）或 编号开头
        if re.match(r'^[\d一二三四五六七八九十]{1,3}[．.、]\s*', s):
            break
        # 总结句/合论句（"这些方法旨在..."），不属于单条定义
        if re.match(r'^(这些|那些|该|上述|它们|它|此|另外|综上|总的来说|总而言之)', s):
            break
        # 新概念头 `生活世界：` `象征资本2020` 等（短冒号行）
        if re.search(r'^[^：:\n]{1,20}[:：]', s) and not re.match(r'^(且|而|并|但|这|那|其|它|因|为|所|在|就|正|又|也|或|即|所谓|因而|因此|所以|然而|不过)', s):
            break
        parts.append(s)
        added += 1
        if added >= 2:
            break
    return ''.join(parts)

def find_definition(text, term, formats=("colon", "year", "newline")):
    """在源文本中定位 term 的定义（修复版）

    词边界 `(?<![一-鿿])` 只加起始——避免"社会"误匹配"社会资本"，且不破坏
    `文化资本2022` 的年份直连（末尾数字合法）。

    策略：收集所有格式的所有匹配 → 去引导行 + 跨行续接 → 返回**最长**候选。
    最长优先解决"目录行 vs 真题解析定义段"（目录行匹配通常较短且含【】）。

    格式:
      colon   `概念名：定义`（定义跨多行，`主体间性：\n定义` 也支持）
      year    `概念名【年份】\n定义` / `概念名2022\n定义` / `概念名-2019\n定义`
      newline `概念名\n定义`
    """
    cands = []
    for fmt in formats:
        if fmt in ("colon", "year", "newline"):
            cands.extend(_collect_definition(text, term, fmt))

    if not cands:
        return None

    best = None
    for raw, pos in cands:
        d = _clean_definition(raw, text, pos)
        if not d:
            continue  # 目录行
        if len(d) >= 25:
            if best is None or len(d) > len(best):
                best = d
    # 无 ≥25 的，退回最长非目录候选（供 short_def_review 判断）
    if best is None:
        for raw, pos in sorted(cands, key=lambda c: len(c[0]), reverse=True):
            d = _clean_definition(raw, text, pos)
            if d:
                best = d
                break
    return best

# ============ 备份 ============

def add_backup(path, tag):
    """备份文件到同目录：<basename>_backup_<tag>_<ts>.json"""
    if not os.path.exists(path):
        return None
    ts = time.strftime('%Y%m%d_%H%M%S')
    base, ext = os.path.splitext(path)
    dest = f"{base}_backup_{tag}_{ts}{ext}"
    shutil.copy2(path, dest)
    print(f"  [备份] {path} → {dest}")
    return dest
