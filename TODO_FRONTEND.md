# 社会学考研 App — 前端待办清单

> 主文件：`D:\workspace\sociology-kaoyan-app\web\index.html`（1907 行，单文件 HTML+CSS+JS）
> 数据文件：`D:\workspace\sociology-kaoyan-app\web\data/concepts.json`（2,418 条概念）
> 测试方式：`cd D:\workspace\sociology-kaoyan-app\web && python -m http.server 8765` → `http://localhost:8765`

---

## 一、方法面板（panel-methods，行 1055-1126）

当前 5 个子 Tab：概念卡片 ✅、公式手册 ❌、统计练习 ❌、研究设计 ❌、资料库 ✅

### 1.1 公式手册 UI（sub-met-formula，行 1087-1093）

**现状：** 占位符。一句话描述。

**要做：**
- 左侧章节导航（单变量描述 → 概率 → 假设检验 → 回归…），右侧公式卡片列表
- 公式卡片：名称 + 公式（等宽字体 `<code>`）+ 使用条件 + 计算示例
- 数据源优先级：lcwiki 28 个方法概念 md > concepts.json 统计学章节 > 手写补充
- 样式复用 `.card`、`.method-card-grid`

**参考样式：** 行 598-621 `.method-card` 已有展开卡片样式，公式卡片类似

### 1.2 统计练习 UI（sub-met-stat，行 1095-1101）

**现状：** 占位符。

**要做：**
- 题目列表，每题：题干 + "显示答案"按钮 + 完整解答
- 按章节筛选（假设检验 / 回归 / 方差分析 / 非参数）
- 难度标签（简单/中等/困难）
- 初期硬编码 10-15 道经典计算题

### 1.3 研究设计 UI（sub-met-design，行 1103-1109）

**现状：** 占位符。

**要做：**
- 场景卡片：研究问题描述 + 展开看完整方案
- 每个场景包含：概念操作化、抽样方案、数据收集方法、分析策略
- 初期硬编码 5-8 道经典设计题（从 `方法设计.docx` OCR 文本提取）
- 卡片样式类似 `.method-card`，点击展开

---

## 二、理论面板（panel-theory，行 910-1053）

当前 4 个子 Tab：概念学习 ✅、刷题/闪卡 ✅、模拟考 ❌、资料库 ✅

### 2.1 概念关系图 Canvas（#graphShell，行 972-981）

**现状：** 空 `<div>`，占位文字。

**要做：**
- 力导向图：节点=概念，连线=关联关系，颜色=学派
- 数据源：`concepts.json` 的 `related` 字段（`{id, relation}` 格式）
- 交互：拖拽节点、滚轮缩放、点击节点跳转概念详情
- 可选方案：D3.js force layout（CDN 引入，不增加依赖文件）或纯 Canvas 手写

### 2.2 模拟考 UI（sub-thr-exam，行 1030-1036）

**现状：** 占位符。

**要做：**
- 出卷配置：概念数量、题型（名词解释/简答/论述）、限时
- 作答区：文本框，倒计时
- 交卷后：逐题批改（需 DeepSeek API）+ 分数 + 维度雷达图
- 先做 UI 框架，API 接入后面再说

### 2.3 概念搜索搜索框实时搜索（已有框架，需打磨）

**现状：** 搜索可用但结果展示偏简陋。

**优化：**
- 搜索结果高亮匹配文字
- 支持拼音搜索
- 快捷键：`/` 聚焦搜索框

---

## 三、政治面板（panel-politics，行 765-836）

当前 5 个子 Tab：选择题刷题 ❌、错题本 ❌、分析题背诵 ❌、时政速览 ❌、资料库 ✅

**全部是占位符。** 缺政治题库数据文件，但可先做 UI 框架：

### 3.1 选择题刷题 UI（sub-pol-quiz）

- 题目卡片：题干 + 4 选项 + 提交按钮 + 即时判对错
- 模块筛选：马原/毛中特/史纲/思修
- 进度条：已做/总数
- 错题自动入错题本

### 3.2 错题本 UI（sub-pol-wrong）

- 错题列表，按模块分组
- 每道错题可重做
- 重做正确后移除

### 3.3 分析题背诵 UI（sub-pol-essay）

- 卡片式：正面 = 题目，反面 = 答题框架 + 关键词
- SM-2 间隔复习（复用理论闪卡的 `sm2Schedule()`）

### 3.4 时政速览 UI（sub-pol-news）

- 热点卡片：标题 + 关联出题角度 + 素材要点
- 按国内/国际分类

---

## 四、英语面板（panel-english，行 838-908）

当前 5 个子 Tab：单词本 ❌、阅读理解 ❌、作文 ❌、翻译 ❌、资料库 ✅

### 4.1 单词本 UI（sub-eng-vocab）

- 复用 SM-2 闪卡引擎（`sm2Schedule()` 行 1508）
- 正面英文 → 反面中文 + 例句
- 待复习 / 新词 / 已掌握 三栏统计
- 数据源：需英语词库 JSON，暂无

### 4.2 作文 UI（sub-eng-write）

- data/ 下已有 4 个作文模板 txt（大/小作文 背诵+模板），但未渲染
- 模板列表 + 展开看全文
- AI 批改框：粘贴作文 → DeepSeek 批改（API 接入后）

### 4.3 阅读/翻译 UI

- 阅读理解：真题文章 + 题目 + 逐段翻译对照
- 翻译：长难句拆解，手动输入译文对比
- 都需要真题数据文件

---

## 五、Dashboard（行 678-763）

基本可用，小修：

### 5.1 方法卡片统计修正（行 1834-1843）

方法卡片显示 `metReviewed/metConcepts`，逻辑已写但用的是 `isMethodsConcept()` 过滤，数据依赖 concepts.json 加载。确认功能正常即可。

### 5.2 侧边栏 Badge 修正（行 649，行 1231-1233）

方法 Badge 写死 `0`。已有 `updateDashStats()` 里的更新逻辑（行 1232-1233），加载 concepts.json 后自动更新到 559。检查是否生效。

---

## 六、Settings 面板（行 1128-1166）

### 6.1 API Key 持久化

- 输入框 `apiKeyShell`、`apiModelShell` 无 JS 读写
- localStorage key: `socio_apikey_v1`
- oninput 自动保存，页面加载恢复

### 6.2 清除数据按钮

- 行 1153 的按钮 `alert('数据清除功能将在正式版开放')` → 替换为真实清除 localStorage

---

## 七、全局

### 7.1 DeepSeek API 客户端

- 无任何外部 API 调用代码
- 需要：`callDeepSeek(systemPrompt, userPrompt)` → 返回文本
- API 格式：`POST https://api.deepseek.com/chat/completions`，Bearer 认证，model: deepseek-chat
- 接入后激活：模拟考批改、英语作文批改、AI 出题

### 7.2 Toast 提示组件

- 页面右上角滑入提示，3 秒消失
- 用于 API 错误、操作反馈

### 7.3 删除中间产物

`D:\workspace\` 下临时脚本：`_extract_docx.py`, `_pdf_classify.py`, `_ocr_batch.py`, `_ocr_g1.py`, `_ocr_g2.py`, `_dpi_test.py`, `_ocr_worker.py`, `_ocr_parallel.py`，OCR 全完成后删。

---

## 优先级建议

| 优先级 | 项目 | 理由 |
|--------|------|------|
| 🔴 P0 | 方法公式手册 UI | 方法面板最核心，有数据源可直接用 |
| 🔴 P0 | 方法统计练习 UI | 同上，数据结构简单 |
| 🟡 P1 | 概念关系图 Canvas | 视觉效果最好，数据现成 |
| 🟡 P1 | API Key 持久化 | 15 行 JS，不堵路 |
| 🟡 P1 | DeepSeek API 客户端 | 所有 AI 功能的基建 |
| 🟢 P2 | 理论模拟考 UI | 依赖 API，先做壳 |
| 🟢 P2 | 方法研究设计 UI | 依赖 DOCX OCR 文本 |
| ⚪ P3 | 政治面板 | 缺题库数据文件 |
| ⚪ P3 | 英语面板 | 缺词库+真题数据 |
