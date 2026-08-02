---
name: concept-dict-quality
description: Use when working on the 考研 concept dictionary's data quality — audit, validation, repair, restructure of web/data/concepts.json and concept-taxonomy.json. Interpreting verify.sh / audit_runner.py exit codes (PASS/FAIL/REVIEW), reading _audit_report.md, fixing concept misplacement (概念错位), proponent mismatch, unclassified taxonomy, fragment/noise terms, merge/dedupe of variants, or adding concepts from notes/textbooks. Touches translation_aliases.json, audit_rules.json, chapter_mappings.json.
---

# 概念词典数据质量纪律

## 概述

概念词典（`web/data/concepts.json`，~1972 条）的修复有固定纪律：**先审计 → 分类 → 修复 → 验证**。
本 skill 只编排现有脚本（`pipeline/` + `scripts/`），不复制代码，把 07-28~08-02 六次数据大修的踩坑固化成可执行检查。

核心原则：
- **名校笔记定义"哪些概念存在"**，教材只补定义，绝不从教材裸文本提取新概念名
- **弱信号只标注不改判**，强信号才自动改判，多弱信号叠加才人工审核
- **改数据前必备份**
- **verify 退出码 0 才算绿**（0 ERROR / 0 blocker WARN）

## 何时使用

- 任何涉及概念词典的"数据质量 / 审计 / 校验 / 修数据 / 概念错位 / 概念合并 / 新增概念"任务
- 需要解读 `verify.sh` / `audit_runner.py` 退出码或 `D:/workspace/_audit_report.md`
- 改动 `web/data/concepts.json`、`concept-taxonomy.json`、`translation_aliases.json`、`audit_rules.json`、`chapter_mappings.json`
- **不适用**：纯前端展示逻辑、与数据字段无关的文档写作

## Entry Points（按场景选工作流）

### Mode 1 — 全量审计（新数据集 / 大修前基线）
1. `bash scripts/verify.sh`（必须 Git Bash，PowerShell 中文乱码）拿基线
2. 读 `D:/workspace/_audit_report.md` 的"需处理清单"
3. 按 ERROR → blocker WARN → 普通 WARN 优先级处理
4. 修复后复跑直到 exit 0

### Mode 2 — 定向修复（具体概念错位 / proponent mismatch / 短定义）
1. 只处理目标概念，不碰无关数据
2. proponent 错位：清单 → DeepSeek 判定归属 → **人工核对** → 修复
3. 改任何数据前 `add_backup`

### Mode 3 — 新增概念入库（从笔记/教材提取）
1. 查 `D:/workspace/_canonical_names.json`（正典清单）确认概念该存在
2. **只从名校笔记取新概念名**，教材只补 definition
3. 每批次抽检：前读 50 行确认格式 → 中抽 3 条 → 后抽 5 条，不合格整批 NG
4. 新概念必须带 `source_text`，用 hex hash 做 ID

## 核心工作流

```
开工 → 1.审计(verify.sh基线) → 2.分类(读报告+规则注册表) → 3.修复(守纪律) → 4.验证(exit 0) → 收工
```

**退出码语义**（audit_runner 唯一来源）：
| 码 | 含义 | 是否算绿 |
|---|---|---|
| 0 | 真PASS（0 ERROR / 0 blocker WARN） | ✅ |
| 1 | FAIL（有 ERROR，数据真错位/结构破坏） | ❌ 必须修 |
| 2 | REVIEW（0 ERROR 但有 blocker WARN） | ⚠️ **不是全绿**，blocker 须人审 |

**DQS 质量评分**（报告顶部必报）：
- 🟢 85-100 生产就绪 / 🟡 65-84 可用但有缺陷 / 🔴 <65 必须先修
- 维度权重：完整性 30%（缺 source/字段）、一致性 25%（chapter 结构）、有效性 20%（proponent 归属）、唯一性 15%（重复）、及时性 10%

## 主动预警信号（看到就提示，不等用户问）

- **概念总数 > 2000** → 该砍了（笔记正典违规信号）
- **名校笔记来源占比 < 50%** → 方向错了（查 `_note_weight_report.json`）
- **blocker WARN 未人审** → 退出码 2 ≠ 收工
- **proponent-mismatch 突然增多** → 可能引入新提取源，检查译名归一是否漏了

## 纪律检查（12 条踩坑 → 可操作检查）

| # | 规则 | 操作检查 |
|---|------|---------|
| 1 | 笔记正典原则 | 新增概念前查 `_canonical_names.json`。只从名校笔记取新概念名，教材只补定义。违规信号：总数>2000 或名校笔记来源占比<50% |
| 2 | 保守审计 | 弱信号（INFO/普通WARN）只标注不改判；只有 ERROR/blocker WARN 才处理。`no_source_text` 是 INFO 技术债，禁止批量推 REVIEW（v1 教训：1543 条没法审） |
| 3 | 每批次抽检 | 任何批量提取：前读 50 行确认格式 → 中抽 3 条 → 后抽 5 条，不合格整批 NG 重来 |
| 4 | 先看数据再写逻辑 | 写脚本前 `python -c "import json;d=json.load(open('web/data/concepts.json',encoding='utf-8'));print(len(d),d[0])"` 确认字段，别假设 |
| 5 | 统计拆分布 | 某规则命中多（如 577 缺 proponent），先按 chapter 顶层拆分布再定性；方法论概念本无提出者属正常 |
| 6 | 映射方向核对 | 建 era/学者映射先拿已知对 dry-run（如 `古典时期 (1830s-1920s)` → `古典时期`）；`era_short_to_full` 曾写反 → 误报 591 条 |
| 7 | 改结构必同步校验 | 改 taxonomy/chapter 结构，必须同步改 `audit_runner` 的 Layer D、`tests/validate_data.py`、`tests/audit_taxonomy.py` |
| 8 | 社会学判断不凭印象 | proponent/归属拿不准（文化悲剧=齐美尔非韦伯；选择性亲和关系在教材里是鲍曼）→ 查原文或 DeepSeek 判定，绝不凭记忆改 |
| 9 | WARN 洪水=假全绿 | verify 只看退出码；有 blocker WARN 即使 0 ERROR 也是 REVIEW，必须人审清单后才算完成 |
| 10 | 修复流程 | proponent 错位：mismatch 清单 → DeepSeek 判定归属（模板见"实现"）→ 人工核对 → 修复 |
| 11 | 新脚本先小跑 | 新脚本先 `--dry-run` / 小样本跑一次，无意外再全量 |
| 12 | 改前必备份 | 每次写 `web/data/*.json` 前备份，命名 `concepts_backup_<tag>_<ts>.json` |
| 13 | **变体普查** | 重复定义检测**全量扫，绝不抽查**（用户铁律）。看 `_audit_report.md` 的 variant_* 规则（def_similar/edit_distance/exact_norm/alias_ref/shared_word）。"term 不同但同一概念"（如 资本主义的文化悲剧~文化悲剧）现有 term 查重抓不到，必须靠 E 层变体检测。合并前**人审**，keeper 保留定义最长+来源最权威 |

## 置信度分级（修复建议标注）

- 🟢 **已确认** — 数据检查或源文本证实
- 🟡 **可能** — 强信号但未完全确认
- 🔴 **需人审** — 推断/拿不准，**绝不自动修复**，必须人工确认（尤其社会学归属判断）

## 快速参考

| 动作 | 命令 |
|------|------|
| 一键验证链 | `bash scripts/verify.sh`（Git Bash） |
| 全量审计 | `python pipeline/audit_runner.py --all` |
| 严格模式（全 WARN 当 blocker） | `bash scripts/verify.sh --strict` |
| 结构单跑 | `python pipeline/audit_runner.py --check-structure` |
| 学者映射生成 | `python scripts/build_scholar_map.py --dry-run` / `--apply` |
| 报告文件 | `D:/workspace/_audit_report.json` / `_audit_report.md` |

## 实现（编排现有资产，不复制代码）

- `pipeline/audit_runner.py` — 统一审计出口（A数据 / B语义 / C结构 / D taxonomy），退出码语义唯一来源
- `pipeline/config/audit_rules.json` — severity/blocker 注册表，修数据前先查它
- `pipeline/config/translation_aliases.json` — 译名归一表；canonical 键必须与 `build_taxonomy.py` 学者键一致
- `pipeline/utils/concept_utils.py` — `find_definition` / `is_fragment_term` / `classify_fragment` / `add_backup`
- `scripts/verify.sh` — 一键验证链
- `D:/workspace/_canonical_names.json` — 正典概念清单（新增概念唯一依据；注意在项目外）

**DeepSeek 归属判定 prompt（内联模板，复用 `ai_semantic_merge_check.py` 的调用壳）**：
```
判定以下 proponent 错位概念的正确提出者与 chapter 归属。
[{term, chapter, proponent_cur}, ...] 只输出 JSON 数组：[{id, canonical_scholar, proponent_correct, chapter_suggestion, reason}]
```
输出写 `D:/workspace/_ai_attribution_results.json`，结果必须人工核对后才能修。

## 红线 — 停下来重新开始

- 不备份就写 `web/data/*.json`
- 从教材裸文本直接提新概念名
- 把 `no_source_text` 推成 REVIEW
- 退出码 2 当全绿收工
- 凭记忆改 proponent / 学者归属
- 新脚本不 dry-run 直接全量
- 开工不先跑 verify.sh
- "量太大 / 没时间 / 这次特殊"跳过抽检或备份

## 常见错误

| 错误 | 修复 |
|------|------|
| 把 `no_source_text` 当阻塞 | INFO 技术债，只监控不回填 |
| 从教材裸提新概念名 | 只在名校笔记找新概念，教材只补定义 |
| 不备份直接改数据 | 先 `add_backup` 再写 |
| 凭记忆改 proponent | 查原文或 DeepSeek 判定 |
| 有 blocker WARN 仍收工 | 退出码 2 须人审，审完才算完成 |
| 改 taxonomy 忘同步校验 | 结构改动同步改 validate/audit 规则 |
| 新脚本直接全量跑 | 先 dry-run / 小样本 |
| 教材短定义自动删 | 真概念用 `is_fragment_term` 分流 KEEP，绝不自动删 |

## When NOT to use

- 纯前端展示逻辑（改 index.html 渲染）
- 与数据字段无关的文档写作
- 数据库 schema 设计 / ETL 构建（那是另一个问题域）
