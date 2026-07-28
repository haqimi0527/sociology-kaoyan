# 后端数据全面建设 - 进度追踪

> 最后更新: 2026-07-29
> 计划: `C:\Users\Lenovo\.claude\plans\dapper-shimmying-pascal.md`

## 总体进度: ██████████ 85%

---

## 数据变更历史

| 日期 | 文件 | 改前 | 改后 | 方法 | 增量 |
|------|------|------|------|------|:--:|
| 07-28 | concepts.json | 1,253 | 1,295 | 贾春增DeepSeek +42 | +42 |
| 07-28 | concepts.json | 1,295 | 1,337 | 概论名词正则 +42 | +42 |
| 07-28 | concepts.json | 1,337 | 1,398 | 贾春增笔记DeepSeek +61 | +61 |
| 07-28 | methods-questions.json | 178 | 337 | 风笑天题库正则 | +159 |
| 07-28 | methods-questions.json | 337 | 472 | 风笑天笔记正则 | +135 |
| 07-28 | comparative-theory.json | 无 | 22 | 比较社会理论DeepSeek | 新建 |
| 07-28 | essay-answers.json | 无 | 5 | momo答案手动转录 | 新建 |
| 07-28 | concept-taxonomy.json | 空壳 | 1,384/1,398 | build_taxonomy.py重建 | - |
| **07-29** | **concepts.json** | **1,398** | **1,419** | **方法补充+定量正则** | **+21** |
| **07-29** | **methods-questions.json** | **472** | **898** | **袁方笔记+题库正则** | **+426** |
| **07-29** | **questions-theory.json** | **0** | **438** | **侯钧生笔记+题库正则** | **+438** |

---

## 当前数据状态

| 文件 | 数量 | 状态 |
|------|------|:--:|
| concepts.json | **1,419** | 0 ERROR |
| exams.json | 5,651 | 16校 |
| politics.json | 1,140 | 4模块 |
| english-vocab.json | 5,169 | - |
| methods-questions.json | **898** | 0 ERROR |
| questions-theory.json | **438** | 0 ERROR (新建) |
| comparative-theory.json | 22 专题 | - |
| essay-answers.json | 5 篇 | - |
| concept-taxonomy.json | 1,384/1,419 分类 | 35 unclassified |
| theory-topics.json | 208 (全有definitions) | - |

---

## 尚有问题

1. 35 unclassified 概念 (14旧+21新方法概念，需手动分配 taxonomy)
2. theory-topics 156 条 definitions 不完整 (需DOCX源文件重建)
3. 贾春增教材 133/151 块未提取 (还能出 100-200 概念)
4. 杨善华/刘少杰/卢淑华 OCR 未启动
5. 31 条短定义残留
6. comparative-theory.json 未与 concepts 互链
7. 数据目录有大量中间产物未清理 (concepts_clean.json, concepts_before_*.json 等)

---

## 已处理的笔记 (OCR → 提取)

| 文件 | 大小 | 状态 | 产出 |
|------|------|:--:|------|
| 风笑天_笔记和课后习题详解 | 649KB | ✅ | methods +135 |
| 人大_概论名词解释 | 111KB | ✅ | concepts +41 |
| 人大_贾春增笔记 | 250KB | ✅ | concepts +62 |
| 社会研究方法_补充 | 588KB | ✅ | concepts +21 |
| 定量社会研究方法 | 204KB | ✅ | 含在上条 |
| 人大_袁方笔记 | 884KB | ✅ | methods +148 |
| 人大_袁方题库 | 800KB | ✅ | methods +278 |
| 人大_侯钧生笔记 | 1.1MB | ✅ | theory Q&A +184 |
| 人大_侯钧生题库 | 1.0MB | ✅ | theory Q&A +254 |
| 人大_郑杭生概论笔记 | 648KB | ⏭️ 跳过 | 概论全量覆盖 |
| 人大_郑杭生概论题库 | 712KB | ⏭️ 跳过 | 概论全量覆盖 |
| 人大_概论精编重点 | 133KB | ⏭️ 跳过 | 概论全量覆盖 |

---

## 下一步

1. 🔴 贾春增剩余133块 DeepSeek提取 (+100-200 理论概念)
2. 🔴 杨善华OCR+提取 (西方社会学理论上下卷)
3. 🟡 35 unclassified 手动分配 taxonomy
4. 🟡 theory-topics definitions 重建 (需DOCX源文件)
5. 🟢 刘少杰/卢淑华 OCR
6. 🟢 数据目录清理
7. 🟢 Worker API 扩容

---

## 踩坑汇总 (不要重复犯)

1. **先读格式再写代码** — 章节标题当问题、字段名不一致、编码问题
2. **正则 > API** — 结构化内容(定义/Q&A)用正则，只有叙事文本才调 DeepSeek
3. **去重先查存量** — 袁方教材去重率100%，概论笔记去重率~100%
4. **PowerShell吃中文** — 中文脚本写成.py文件
5. **定义相似度去重** — 除了term匹配，还要check definition前60字
6. **数据字段不一致** — methods-questions有title和question两种字段名，先标准化
7. **hash碰撞** — 8位hex ID不够用，"简化论"和"还原论"碰撞
