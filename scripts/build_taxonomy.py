"""
Build concept-taxonomy.json from concepts.json + textbook classification.
Theory: era -> school -> scholar -> concept_ids
Methods: phase -> category -> concept_ids
"""
import json, os, sys, io
from collections import defaultdict

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'web', 'data')
OUTPUT = os.path.join(DATA_DIR, 'concept-taxonomy.json')

# ===== Standard Taxonomy (from 侯钧生 + 贾春增 + 风笑天) =====

THEORY_TAXONOMY = {
    "古典时期 (1830s-1920s)": {
        "实证主义": {
            "desc": "社会学初创期的实证科学范式",
            "scholars": {
                "孔德": {"concepts": [], "keywords": ["孔德", "社会静力学", "社会动力学", "三阶段法则", "神学阶段", "形而上学阶段", "实证阶段", "秩序与进步", "实证哲学", "人道教"]},
                "斯宾塞": {"concepts": [], "keywords": ["斯宾塞", "社会进化", "社会有机体", "军事社会", "工业社会"]},
            }
        },
        "社会学主义": {
            "desc": "涂尔干开创的以社会事实为核心的研究范式",
            "scholars": {
                "涂尔干": {"concepts": [], "keywords": ["涂尔干", "迪尔凯姆", "杜尔凯姆", "社会事实", "社会团结", "自杀", "失范", "机械团结", "有机团结", "集体意识", "集体表象", "宗教生活"]},
            }
        },
        "历史唯物主义": {
            "desc": "马克思的社会批判理论",
            "scholars": {
                "马克思": {"concepts": [], "keywords": ["马克思", "阶级", "异化劳动", "劳动异化", "社会形态", "经济基础", "上层建筑", "生产力", "生产关系", "商品拜物教", "意识形态", "历史唯物主义", "阶级斗争", "剩余价值"]},
            }
        },
        "形式社会学": {
            "desc": "齐美尔开创的形式研究与文化分析",
            "scholars": {
                "齐美尔": {"concepts": [], "keywords": ["齐美尔", "形式社会学", "社会交往", "社会圈子", "陌生人", "时尚", "都市", "货币哲学"]},
            }
        },
        "理解社会学": {
            "desc": "韦伯开创的以社会行动和意义理解为核心的传统",
            "scholars": {
                "韦伯": {"concepts": [], "keywords": ["韦伯", "社会行动", "理想类型", "科层制", "新教伦理", "价值中立", "权威类型", "理性化", "铁笼", "阶级阶层", "解释性理解", "理解社会学", "卡里斯马", "传统型权威", "法理型权威"]},
            }
        },
        "精英理论": {
            "desc": "帕累托的精英循环与逻辑/非逻辑行为",
            "scholars": {
                "帕累托": {"concepts": [], "keywords": ["帕累托", "精英循环", "逻辑行为", "剩余物", "派生物", "社会系统均衡"]},
            }
        },
        "社群与社会": {
            "desc": "滕尼斯的共同体与社会类型学",
            "scholars": {
                "滕尼斯": {"concepts": [], "keywords": ["滕尼斯", "本质意志", "选择意志", "礼俗社会", "法理社会", "共同体与社会", "社区与社会"]},
            }
        },
        "其他古典学者": {
            "desc": "古典时期的其他重要理论家",
            "scholars": {
                "托克维尔": {"concepts": [], "keywords": ["托克维尔", "民主", "平等", "自由", "多数暴政"]},
                "库利": {"concepts": [], "keywords": ["库利", "镜中我", "首属群体", "初级群体"]},
                "托马斯": {"concepts": [], "keywords": ["托马斯", "情境定义", "托马斯定理", "愿望四分法"]},
                "米德": {"concepts": [], "keywords": ["米德", "符号互动", "主我", "客我", "角色扮演", "泛化他人"]},
                "萨姆纳": {"concepts": [], "keywords": ["萨姆纳", "民俗", "民德", "内群体", "外群体", "种族中心主义"]},
                "塔尔德": {"concepts": [], "keywords": ["塔尔德", "模仿律", "暗示", "社会逻辑"]},
            }
        },
    },
    "现代时期 (1930s-1970s)": {
        "结构功能主义": {
            "desc": "帕森斯集大成的宏大理论体系",
            "scholars": {
                "帕森斯": {"concepts": [], "keywords": ["帕森斯", "社会行动", "AGIL", "模式变量", "社会系统", "一般行动系统", "结构功能", "社会化", "社会控制", "适应", "目标达成", "整合", "维模"]},
                "默顿": {"concepts": [], "keywords": ["默顿", "中层理论", "功能分析", "显功能", "潜功能", "反功能", "功能替代", "失范", "参照群体", "自我实现预言", "科学社会学", "越轨"]},
                "新功能主义": {"concepts": [], "keywords": ["新功能主义", "亚历山大", "后功能主义"]},
            }
        },
        "冲突理论": {
            "desc": "批判结构功能主义保守性的理论流派",
            "scholars": {
                "科塞": {"concepts": [], "keywords": ["科塞", "冲突功能", "安全阀", "现实冲突", "非现实冲突", "内群体冲突"]},
                "达伦多夫": {"concepts": [], "keywords": ["达伦多夫", "权威结构", "强制协作团体", "利益群体", "准群体", "显群体", "社会压制模式"]},
                "米尔斯": {"concepts": [], "keywords": ["米尔斯", "权力精英", "社会学的想象力", "白领", "公众与大众"]},
            }
        },
        "批判理论（法兰克福学派）": {
            "desc": "以批判实证主义和资本主义为核心的马克思主义后续",
            "scholars": {
                "霍克海默": {"concepts": [], "keywords": ["霍克海默", "传统理论", "社会批判理论", "法兰克福学派", "批判理论", "工具理性", "启蒙辩证法", "跨学科研究"]},
                "阿多诺": {"concepts": [], "keywords": ["阿多诺", "文化工业", "权威人格", "否定辩证法", "否定辩证", "同一性批判", "非同一性", "工具理性批判", "文化批判", "启蒙辩证法", "反体系"]},
                "马尔库塞": {"concepts": [], "keywords": ["马尔库塞", "单向度", "大拒绝", "压抑性宽容", "爱欲与文明"]},
                "弗洛姆": {"concepts": [], "keywords": ["弗洛姆", "逃避自由", "社会性格", "人本主义精神分析"]},
            }
        },
        "符号互动论": {
            "desc": "以微观互动中的意义建构为核心的理论传统",
            "scholars": {
                "布鲁默": {"concepts": [], "keywords": ["布鲁默", "符号互动论", "共同行动", "情境定义", "自我指示"]},
                "戈夫曼": {"concepts": [], "keywords": ["戈夫曼", "拟剧论", "戏剧理论", "印象管理", "前台后台", "污名", "总体性制度", "框架分析", "互动仪式", "角色距离"]},
            }
        },
        "社会交换理论": {
            "desc": "以经济学理性选择解释社会行为的微观理论",
            "scholars": {
                "霍曼斯": {"concepts": [], "keywords": ["霍曼斯", "社会交换", "成功命题", "刺激命题", "价值命题", "剥夺-满足命题", "攻击-赞同命题"]},
                "布劳": {"concepts": [], "keywords": ["布劳", "社会交换", "宏观交换", "结构性交换", "间接交换", "权力不平衡"]},
            }
        },
        "现象学社会学与常人方法学": {
            "desc": "以日常生活世界和意义建构为核心的社会学传统",
            "scholars": {
                "舒茨": {"concepts": [], "keywords": ["舒茨", "现象学", "生活世界", "自然态度", "类型化", "知识库存", "关联性", "多重实在"]},
                "伯格与卢克曼": {"concepts": [], "keywords": ["伯格", "卢克曼", "现实的社会建构", "制度化", "合法化", "次级社会化"]},
                "加芬克尔": {"concepts": [], "keywords": ["加芬克尔", "常人方法学", "索引性", "反思性", "破坏性实验", "背景期望"]},
            }
        },
        "系统理论": {
            "desc": "卢曼的社会系统理论",
            "scholars": {
                "卢曼": {"concepts": [], "keywords": ["卢曼", "社会系统", "自我指涉", "沟通", "复杂性化约", "功能分化", "系统与环境"]},
            }
        },
        "其他现代学者": {
            "desc": "过渡性或难以归入主要流派的现代学者",
            "scholars": {
                "曼海姆": {"concepts": [], "keywords": ["曼海姆", "知识社会学", "意识形态与乌托邦", "知识分子"]},
                "索罗金": {"concepts": [], "keywords": ["索罗金", "社会分层", "社会流动", "文化类型"]},
                "布鲁默": {"concepts": [], "keywords": []},
            }
        },
    },
    "当代时期 (1980s-)": {
        "实践理论": {
            "desc": "布迪厄的生成结构主义",
            "scholars": {
                "布迪厄": {"concepts": [], "keywords": ["布迪厄", "惯习", "场域", "资本", "文化资本", "社会资本", "象征资本", "符号暴力", "区隔", "实践感", "反思社会学", "再生产", "场域理论"]},
            }
        },
        "结构化理论": {
            "desc": "吉登斯的现代性与结构化",
            "scholars": {
                "吉登斯": {"concepts": [], "keywords": ["吉登斯", "结构化", "结构二重性", "反思性", "时空延伸", "脱域", "本体性安全", "现代性", "第三条道路", "生活政治"]},
            }
        },
        "沟通行动理论": {
            "desc": "哈贝马斯的批判转向与沟通理性",
            "scholars": {
                "哈贝马斯": {"concepts": [], "keywords": ["哈贝马斯", "沟通行动", "生活世界殖民化", "公共领域", "交往理性", "系统与生活世界", "普遍语用学", "理想言说情境", "认识兴趣"]},
            }
        },
        "后结构主义与谱系学": {
            "desc": "福柯的权力/知识/主体分析",
            "scholars": {
                "福柯": {"concepts": [], "keywords": ["福柯", "权力", "知识", "话语", "规训", "全景敞视", "治理术", "生命政治", "自我技术", "考古学", "谱系学", "性经验史"]},
            }
        },
        "后现代理论": {
            "desc": "对宏大叙事的解构与消费社会批判",
            "scholars": {
                "鲍德里亚": {"concepts": [], "keywords": ["鲍德里亚", "消费社会", "符号价值", "拟像", "超真实", "内爆", "象征交换", "符号消费"]},
                "鲍曼": {"concepts": [], "keywords": ["鲍曼", "流动的现代性", "液态现代性", "大屠杀与现代性", "废弃的生命", "消费者社会"]},
                "利奥塔": {"concepts": [], "keywords": ["利奥塔", "后现代状况", "宏大叙事", "语言游戏"]},
            }
        },
        "理性选择理论": {
            "desc": "科尔曼的理性行动与社会资本",
            "scholars": {
                "科尔曼": {"concepts": [], "keywords": ["科尔曼", "理性选择", "社会资本", "法人行动者", "权威关系", "信任", "社会规范"]},
            }
        },
        "风险社会理论": {
            "desc": "贝克的风险社会与自反性现代化",
            "scholars": {
                "贝克": {"concepts": [], "keywords": ["贝克", "风险社会", "自反性现代化", "个体化", "世界风险社会", "亚政治"]},
            }
        },
        "型构/过程社会学": {
            "desc": "埃利亚斯的文明化进程与型构",
            "scholars": {
                "埃利亚斯": {"concepts": [], "keywords": ["埃利亚斯", "型构", "文明化进程", "宫廷社会", "局内人与局外人"]},
            }
        },
        "行动者网络理论": {
            "desc": "拉图尔的科学技术社会学",
            "scholars": {
                "拉图尔": {"concepts": [], "keywords": ["拉图尔", "行动者网络", "ANT", "转译", "非人类行动者", "实验室研究", "我们从未现代过"]},
            }
        },
        "网络/信息社会理论": {
            "desc": "卡斯特的网络社会分析",
            "scholars": {
                "卡斯特": {"concepts": [], "keywords": ["卡斯特", "网络社会", "信息时代", "流动空间", "认同的力量", "网络化个人主义"]},
            }
        },
        "其他当代学者": {
            "desc": "其他当代重要理论家",
            "scholars": {
                "列斐伏尔": {"concepts": [], "keywords": ["列斐伏尔", "空间生产", "日常生活批判", "城市的权利", "空间三元辩证法"]},
                "邓肯": {"concepts": [], "keywords": ["邓肯", "生态复合体", "POET"]},
                "亚历山大": {"concepts": [], "keywords": ["亚历山大", "新功能主义", "文化社会学", "文化创伤"]},
            }
        },
    },
    "综合与比较": {
        "理论综合": {
            "desc": "跨流派理论整合与比较",
            "scholars": {
                "理论综合": {"concepts": [], "keywords": ["微观-宏观", "能动-结构", "理论整合", "综合范式", "社会互构论"]},
            }
        },
        "理论对比": {
            "desc": "经典理论家之间的比较",
            "scholars": {
                "理论对比": {"concepts": [], "keywords": ["理论比较", "思想比较", "比较分析", "理论对话", "异同比较", "比较研究", "分歧", "共通性", "比较社会理论"]},
            }
        },
    }
}

METHODS_TAXONOMY = {
    "方法论基础": {
        "desc": "社会研究的基本范式与认识论基础",
        "categories": {
            "研究范式": {"concepts": [], "keywords": ["实证主义", "人文主义", "批判范式", "后实证主义", "建构主义"]},
            "理论与研究关系": {"concepts": [], "keywords": ["理论建构", "假设检验", "假设演绎", "归纳逻辑", "演绎逻辑", "操作化", "概念化", "中层理论", "扎根理论"]},
            "定量与定性": {"concepts": [], "keywords": ["定量", "定性", "混合方法", "定性研究", "定量研究"]},
            "核心概念": {"concepts": [], "keywords": ["变量", "自变量", "因变量", "中介变量", "控制变量", "假设", "操作性定义", "概念化", "通则式", "个性解释", "相关关系", "因果关系", "分析单位", "维度", "属性", "反应性", "关联", "人的特殊性", "研究主题", "组织研究", "调查中的文化障碍"]},
        }
    },
    "研究设计": {
        "desc": "从问题到测量方案的整体规划",
        "categories": {
            "研究类型": {"concepts": [], "keywords": ["探索性", "描述性", "解释性", "横向研究", "纵向研究", "趋势研究", "同期群", "同组研究", "个案研究", "比较研究", "评估研究"]},
            "分析单位": {"concepts": [], "keywords": ["分析单位", "生态谬误", "还原论", "层次谬误"]},
            "测量与操作化": {"concepts": [], "keywords": ["测量", "操作化", "概念化", "量表", "李克特", "鲍格达斯", "语义差异", "信度", "效度", "指标", "指数", "测量层次", "定类", "定序", "定距", "定比"]},
        }
    },
    "抽样设计": {
        "desc": "从总体到样本的选择过程",
        "categories": {
            "概率抽样": {"concepts": [], "keywords": ["概率抽样", "简单随机", "系统抽样", "分层抽样", "整群抽样", "多段抽样", "PPS", "抽样框", "抽样误差", "样本量"]},
            "非概率抽样": {"concepts": [], "keywords": ["非概率抽样", "偶遇抽样", "判断抽样", "配额抽样", "滚雪球", "方便抽样", "立意抽样"]},
        }
    },
    "资料收集": {
        "desc": "获取经验材料的具体方法",
        "categories": {
            "问卷调查": {"concepts": [], "keywords": ["问卷", "自填问卷", "访问问卷", "邮寄问卷", "网络调查", "问卷设计", "封闭式问题", "开放式问题", "答案格式"]},
            "访谈法": {"concepts": [], "keywords": ["访谈", "结构式访谈", "半结构访谈", "无结构访谈", "深度访谈", "焦点小组", "口述史", "访谈员", "访谈提纲"]},
            "观察法": {"concepts": [], "keywords": ["观察", "参与观察", "非参与观察", "结构化观察", "田野调查", "民族志"]},
            "实验法": {"concepts": [], "keywords": ["实验", "真实验", "准实验", "自然实验", "前测", "后测", "控制组", "实验组", "随机化", "所罗门四组"]},
            "文献法与内容分析": {"concepts": [], "keywords": ["文献法", "内容分析", "二次分析", "现存统计资料", "历史比较", "文本分析", "编码", "显性内容", "隐性内容"]},
        }
    },
    "资料分析": {
        "desc": "对收集的数据进行处理和解读",
        "categories": {
            "数据整理": {"concepts": [], "keywords": ["编码", "录入", "清洗", "数据管理", "数据审核", "缺失值"]},
            "描述统计": {"concepts": [], "keywords": ["描述统计", "集中趋势", "均值", "中位数", "众数", "离散趋势", "方差", "标准差", "极差", "四分位差", "频率分布", "正态分布", "偏态", "峰度", "标准化", "Z分数"]},
            "推断统计": {"concepts": [], "keywords": ["推断统计", "参数估计", "点估计", "区间估计", "置信区间", "置信水平", "假设检验", "原假设", "备择假设", "显著性水平", "P值", "p值", "第一类错误", "第二类错误", "统计功效", "t检验", "Z检验", "F检验", "卡方检验", "显著性检验", "统计推断", "抽样分布", "标准误"]},
            "相关与回归": {"concepts": [], "keywords": ["相关分析", "回归分析", "相关系数", "Pearson", "Spearman", "最小二乘法", "决定系数", "列联表", "Lambda", "Gamma", "交互分类", "详析模式", "条件关系", "虚假相关", "阐明分析", "双变量", "二元回归", "简单回归", "等级相关", "相关", "回归", "复相关", "净相关", "偏相关", "伪相关", "零相关", "聚类分析", "Q型", "R型", "多元分析", "多因"]},
            "多变量分析": {"concepts": [], "keywords": ["多元回归", "因子分析", "路径分析", "判别分析", "对数线性模型", "结构方程模型", "多层次分析"]},
            "定性分析": {"concepts": [], "keywords": ["定性分析", "编码", "开放式编码", "主轴编码", "选择性编码", "扎根理论", "叙事分析", "话语分析", "会话分析", "主题分析"]},
            "报告撰写": {"concepts": [], "keywords": ["研究报告", "调查报告", "描述性报告", "解释性报告", "综合性报告", "摘要", "文献综述", "方法论", "结论", "讨论", "撰写"]},
        }
    },
    "报告撰写与伦理": {
        "desc": "研究成果的呈现与研究伦理规范",
        "categories": {
            "研究报告": {"concepts": [], "keywords": ["研究报告", "摘要", "文献综述", "方法论", "结论", "讨论"]},
            "研究伦理": {"concepts": [], "keywords": ["伦理", "知情同意", "匿名", "保密", "自愿参与", "无害原则", "机构审查"]},
        }
    },
}

# 概论分类：按主题而非学者
INTRO_TAXONOMY = {
    "学科基础": {"concepts": [], "keywords": ["社会学", "学科", "实证", "功能", "冲突", "互动", "范式", "理论视角", "社会学想象力", "社会运行"]},
    "个人与社会": {"concepts": [], "keywords": ["个人", "社会", "社会化", "社会角色", "角色", "社会互动", "社会关系", "社会网络", "社会群体", "社会地位"]},
    "社会结构": {"concepts": [], "keywords": ["社会结构", "社会分层", "阶级", "阶层", "社会流动", "社会不平等", "社会分化", "弹性结构", "刚性结构"]},
    "社会制度": {"concepts": [], "keywords": ["制度", "家庭", "教育", "经济", "政治", "宗教", "社会制度"]},
    "社会问题与治理": {"concepts": [], "keywords": ["社会问题", "社会治理", "社会控制", "越轨", "犯罪", "社会政策", "社会保障", "社会工作", "社会援助", "社会疏导", "扶贫", "贫困"]},
    "社会变迁与现代化": {"concepts": [], "keywords": ["社会变迁", "现代化", "全球化", "城市化", "社会运动", "集体行为", "社会发展", "迟发展"]},
    "社区与组织": {"concepts": [], "keywords": ["社区", "组织", "科层", "管理", "单位制", "共同体"]},
    "文化与意识形态": {"concepts": [], "keywords": ["文化", "意识形态", "价值", "规范", "符号", "语言", "宗教"]},
    "研究方法论": {"concepts": [], "keywords": ["方法论", "定量研究", "定性研究", "混合研究方法", "社会研究方法", "研究范式"]},
}

# ===== Classification Logic =====

def classify_concept(c):
    """Determine if a concept belongs to theory or methods, and classify it into taxonomy"""
    term = c.get('term', '')
    definition = c.get('definition', '')
    chapter = c.get('chapter', '')
    tags = c.get('tags', [])
    school = c.get('school', '')
    proponent = c.get('proponent', '')
    all_text = f"{term} {definition} {chapter} {' '.join(tags)} {school} {proponent}".lower()

    # Determine domain
    # NOTE: '方法' alone is too broad — it matches '常人方法学' (ethnomethodology, a THEORY school)
    is_methods = False
    if '研究方法' in chapter or '社会学研究方法' in chapter or chapter.startswith('方法/'):
        is_methods = True
    for t in tags:
        if t in ('定量', '定性', '资料分析', '研究设计', '资料收集', '描述统计',
                 '抽样', '概率抽样', '测量与操作化', '定性分析', '研究基础'):
            is_methods = True

    is_intro = '概论' in chapter

    if is_methods:
        return classify_methods(c, all_text)
    elif is_intro:
        return classify_intro(c)
    else:
        return classify_theory(c, all_text)


def classify_theory(c, all_text):
    """Classify a theory concept into era→school→scholar"""
    term = c['term']
    proponent = (c.get('proponent') or '').lower()
    school = (c.get('school') or '').lower()
    chapter = (c.get('chapter') or '').lower()
    tags = [t.lower() for t in (c.get('tags') or [])]

    best_score = 0
    best_path = None

    for era_name, era_data in THEORY_TAXONOMY.items():
        for school_name, school_data in era_data.items():
            scholars = school_data.get('scholars', {})
            for scholar_name, scholar_data in scholars.items():
                score = 0
                keywords = scholar_data.get('keywords', [])

                # Keyword match in full text
                for kw in keywords:
                    if kw.lower() in all_text:
                        score += 1

                # Bonus for chapter path match
                if scholar_name and chapter and scholar_name in chapter:
                    score += 5
                if school_name and chapter:
                    # Check full name first, then short name (before parentheses)
                    if school_name in chapter:
                        bonus = 5 if ('对比' in school_name or '综合' in school_name) else 3
                        score += bonus
                    elif '（' in school_name:
                        short = school_name.split('（')[0]
                        if short and short in chapter:
                            bonus = 5 if ('对比' in school_name or '综合' in school_name) else 3
                            score += bonus

                # Bonus for proponent/school field match (guard against empty string)
                if proponent and scholar_name and (scholar_name in proponent or proponent in scholar_name):
                    score += 5
                if school and scholar_name and (scholar_name in school or school in scholar_name):
                    score += 3

                # Bonus for tag match
                for t in tags:
                    if t and scholar_name and (scholar_name in t or t in scholar_name):
                        score += 2
                    if t and school_name and school_name in t:
                        score += 1

                if score > best_score:
                    best_score = score
                    best_path = (era_name, school_name, scholar_name)

    return best_path, best_score


def classify_methods(c, all_text):
    """Classify a methods concept into phase→category

    优先用 chapter 路径直接定位（`方法/X/Y/` → phase=X, category=Y），
    避免 keywords 兜底误分。chapter 无法匹配时退回 keywords 打分。
    """
    term = c['term']
    chapter = c.get('chapter', '')

    # 直接路径定位：`方法/阶段/类目/`
    parts = [p for p in chapter.split('/') if p]
    if len(parts) >= 3 and parts[0] == '方法':
        phase_name, cat_name = parts[1], parts[2]
        if phase_name in METHODS_TAXONOMY and cat_name in METHODS_TAXONOMY[phase_name]['categories']:
            return (phase_name, cat_name), 100

    best_score = 0
    best_path = None

    for phase_name, phase_data in METHODS_TAXONOMY.items():
        for cat_name, cat_data in phase_data['categories'].items():
            score = 0
            for kw in cat_data['keywords']:
                if kw.lower() in all_text:
                    score += 1
            # Chapter path match bonus
            if cat_name in chapter:
                score += 3
            if phase_name in chapter:
                score += 2

            if score > best_score:
                best_score = score
                best_path = (phase_name, cat_name)

    return best_path, best_score


def classify_intro(c):
    """Classify a 概论 concept into topic area based on keywords

    优先用 chapter 路径直接定位（`概论/主题/` → topic），避免 keywords 兜底误分。
    """
    term = c.get('term', '')
    definition = c.get('definition', '')
    chapter = c.get('chapter', '')
    all_text = f"{term} {definition} {chapter}".lower()

    # 直接路径定位：`概论/主题/`
    parts = [p for p in chapter.split('/') if p]
    if len(parts) >= 2 and parts[0] == '概论':
        topic_name = parts[1]
        if topic_name in INTRO_TAXONOMY:
            return ('intro', topic_name), 100

    best_score = 0
    best_path = None

    for topic, tdata in INTRO_TAXONOMY.items():
        score = 0
        for kw in tdata['keywords']:
            if kw.lower() in all_text:
                score += 1
        if topic in chapter:
            score += 3
        if score > best_score:
            best_score = score
            best_path = topic

    # Return with a sentinel to distinguish from theory/methods
    return ('intro', best_path), best_score


def build():
    with open(os.path.join(DATA_DIR, 'concepts.json'), 'r', encoding='utf-8') as f:
        concepts = json.load(f)

    # Reset concept lists in taxonomy
    for era in THEORY_TAXONOMY.values():
        for school_data in era.values():
            for scholar_data in school_data.get('scholars', {}).values():
                scholar_data['concepts'] = []
    for phase in METHODS_TAXONOMY.values():
        for cdata in phase['categories'].values():
            cdata['concepts'] = []
    for tdata in INTRO_TAXONOMY.values():
        tdata['concepts'] = []

    unclassified = []
    conflicts = []
    classified_count = 0

    for c in concepts:
        result = classify_concept(c)
        term = c['term']
        cid = c.get('id', '?')

        if result is None or result[1] == 0:
            unclassified.append(c)
            continue

        path, score = result

        if path[0] == 'intro':
            INTRO_TAXONOMY[path[1]]['concepts'].append(cid)
        elif len(path) == 3:
            THEORY_TAXONOMY[path[0]][path[1]]['scholars'][path[2]]['concepts'].append(cid)
        else:
            METHODS_TAXONOMY[path[0]]['categories'][path[1]]['concepts'].append(cid)
        classified_count += 1

    # Count totals
    theory_total = sum(
        len(scholar_data['concepts'])
        for era in THEORY_TAXONOMY.values()
        for school_data in era.values()
        for scholar_data in school_data.get('scholars', {}).values()
    )
    methods_total = sum(
        len(cdata['concepts'])
        for phase in METHODS_TAXONOMY.values()
        for cdata in phase['categories'].values()
    )
    intro_total = sum(
        len(tdata['concepts'])
        for tdata in INTRO_TAXONOMY.values()
    )

    # Strip empty nodes: remove scholars/categories/topics with 0 concepts
    clean_theory = {}
    for era_n, era in THEORY_TAXONOMY.items():
        clean_era = {}
        for sch_n, sch in era.items():
            clean_scholars = {}
            for sname, sdata in sch.get('scholars', {}).items():
                if sdata['concepts']:
                    clean_scholars[sname] = {'concepts': sdata['concepts']}
            if clean_scholars:
                clean_era[sch_n] = {'desc': sch.get('desc', ''), 'scholars': clean_scholars}
        if clean_era:
            clean_theory[era_n] = clean_era

    clean_methods = {}
    for ph_n, ph in METHODS_TAXONOMY.items():
        clean_cats = {cn: {'concepts': cd['concepts']} for cn, cd in ph['categories'].items() if cd['concepts']}
        if clean_cats:
            clean_methods[ph_n] = {'desc': ph.get('desc', ''), 'categories': clean_cats}

    clean_intro = {tn: {'concepts': td['concepts']} for tn, td in INTRO_TAXONOMY.items() if td['concepts']}

    output = {
        "theory": clean_theory,
        "methods": clean_methods,
        "intro": clean_intro,
        "_meta": {
            "total_concepts": len(concepts),
            "classified": classified_count,
            "unclassified": len(unclassified),
            "theory_count": theory_total,
            "methods_count": methods_total,
            "intro_count": intro_total,
            "unclassified_terms": [{"id": c.get('id'), "term": c['term'], "chapter": c.get('chapter','')}
                                  for c in unclassified[:30]]
        }
    }

    # Re-count after cleanup
    theory_total = sum(len(sd['concepts']) for era in clean_theory.values() for sch in era.values() for sd in sch.get('scholars',{}).values())
    methods_total = sum(len(cd['concepts']) for ph in clean_methods.values() for cd in ph['categories'].values())
    intro_total = sum(len(td['concepts']) for td in clean_intro.values())

    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Taxonomy written to {OUTPUT}")
    print(f"Classified: {classified_count}/{len(concepts)}")
    print(f"  Theory: {theory_total}")
    print(f"  Methods: {methods_total}")
    print(f"  Intro: {intro_total}")
    print(f"  Unclassified: {len(unclassified)}")
    if unclassified:
        print(f"\nFirst 15 unclassified:")
        for c in unclassified[:15]:
            print(f"  [{c.get('chapter','?')}] {c['term']}")


if __name__ == '__main__':
    build()
