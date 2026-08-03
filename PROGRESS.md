# 概念词典数据质量 — 进度追踪

> 最后更新: 2026-08-03（全库质量清理完成）
> 本次计划: `C:\Users\Lenovo\.claude\plans\eager-wondering-bee.md`

## 总体状态: ✅ verify exit 0 | 1900 概念 | taxonomy 1900/1900 | Playwright 10/10

---

## 2026-08-03 全库质量清理（孔德式问题系统性修复）

### 问题发现（全量扫描，非抽查）
| 问题 | 数量 | 处理 |
|------|:--:|------|
| 合并式变体（A和B各自独立） | 23 | 删合并条目+回填定义 |
| 括号同义变体（X（Y）） | 6 | 删括号变体+并入主条目 |
| 教材 OCR 裸碎片候选 | 375 | DeepSeek 判定 + 人工核对 |
| 伪概念（基本主张/达伦多夫的理论目标等） | 32 | 删除 |
| proponent 错标（进化→斯宾塞等） | 15 | 修正 |
| 学派直挂缺学者（school_direct） | 214 | DeepSeek 归属 + 人工核对 |
| 缺概念（孔德三阶段缺2） | 2 | 补神学阶段/形而上学阶段 |
| taxonomy 错配 | 75→0 | 重建+学派名映射+学者段修正 |
| related 悬空引用 | 655 | 清理1102死链+重定向311 |
| def OCR 残句 | 99 | 97补句号+2删伪概念 |
| chapter 6段重复 | 40 | 去重 |
| chapter 2段缺学派 | 5 | 归位 |
| 短 def（<40字） | 36 | DeepSeek 补全 |
| 理论域 proponent 空 | 41 | 27填学者+11方法概念移域 |
| 真 proponent 错标（深扫发现） | 10 | 修正 |

### 数据规模变化
1968 → 1900（删 80，补 4：神学/形而上学/软控制等）

### 改动文件
- `web/data/concepts.json` / `data/concepts.json`
- `web/data/concept-taxonomy.json` / `data/concept-taxonomy.json`（重建）
- `pipeline/audit_runner.py`（EXCLUDE_VARIANT_TERMS + SCHOOL_DIRECT_EXEMPT + 杂项桶豁免）
- `scripts/build_taxonomy.py`（学派/学者增强匹配 + 新学者节点）
- `tests/specs/01-smoke.spec.ts`（`.hero-bar`→`.hero-banner` 选择器更新）
- `web/index.html`（上次会话未提交的 RPG 深色层，未动）

### 踩坑
1. **正典原则**：教材 OCR 裸提取的"伪概念"（基本主张/达伦多夫的理论目标）大量混入，must 用 classify_fragment + DeepSeek 分流
2. **audit 漏检**：碎片检测只看 term，抓不到"term 正常但 def 是教材裸提取"——需加 def 质量扫描
3. **AI 归属的 chapter 学派名与 taxonomy 键不一致**（现象学社会学 vs 现象学社会学与常人方法学）→ 学派名映射
4. **学者全名 vs taxonomy 短名**（乔治·米德 vs 米德）→ build_taxonomy 姓提取匹配
5. **verify 曾从 exit 0 退到 REVIEW**：改 chapter 后 school_direct 复发 → 杂项桶豁免
6. **补概念脚本误覆盖**（虚惊）：deep_scan 显示 bug 用错变量，非数据污染

---

## 历史数据变更（2026-07-28~29）
| 日期 | 文件 | 改前 | 改后 | 方法 |
|------|------|------|------|------|
| 07-29 | concepts.json | 1,398 | 1,419 | 方法补充+定量正则 |
| 07-29 | methods-questions.json | 472 | 898 | 袁方笔记+题库正则 |
| 07-29 | questions-theory.json | 0 | 438 | 侯钧生笔记+题库正则 |
| 07-28 | concepts.json | 1,253 | 1,398 | 贾春增/概论/笔记 |

---

## 当前数据状态
| 文件 | 数量 | 状态 |
|------|:--:|------|
| concepts.json | **1,900** | ✅ 0 ERROR / 0 blocker |
| concept-taxonomy.json | 1900/1900 | ✅ 0 unclassified / 0 错配 |
| exams.json | 5,651 | ✅ 16校 |
| politics.json | 1,140 | ✅ 4模块 |
| english-vocab.json | 5,169 | ✅ |
| methods-questions.json | 898 | ✅ |
| questions-theory.json | 438 | ✅ |

## 待办
- ⬜ **部署上线**（数据清理完成，待确认推送 cykaoyan.top）
- ⬜ RPG ④四科属性成长(雷达图) → ③BOSS试炼
- ⬜ 云端同步（需后端）
- ⬜ 通论·民大617 入口
