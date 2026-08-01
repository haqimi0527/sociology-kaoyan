# 社会学考研 App — 前端交接文档（给 Trae）

> 📅 2026-07-29 | 作者：Claude Code | 线上：https://cykaoyan.top
>
> **怎么用这份文档**：先通读第 1-4 节理解项目全貌，然后跳到第 7 节挑一个任务开干。每个任务卡片里写了改哪个函数、怎么验证——照着做就行，别自由发挥。

---

## 1. 项目概况

**社会学考研 AI 导师** — 单文件 Web App，HTML+CSS+原生 JS，零框架零构建。

| 项 | 值 |
|---|-----|
| 技术栈 | 单文件 HTML (~5000行) + 原生 CSS + 原生 JS |
| 数据 | 静态 JSON，浏览器 fetch 加载 |
| 部署 | GitHub Pages (`haqimi0527/sociology-kaoyan`) |
| 域名 | cykaoyan.top（CNAME 指向上游仓库） |
| AI | DeepSeek API（模拟考批改、AI 出题） |
| 测试 | Playwright 冒烟测试 (6 cases) + Python 数据校验 |

---

## 2. index.html 物理结构（改代码前先看这里）

一份 5000 行的单文件，没人想从头读到尾。记住这个布局：

```
行 1-7       HTML doctype + <head>（charset/viewport/title/fonts）
行 8-997     <style>  — 全部 CSS，~990 行
行 998-1000   </style> → <body>
行 1001-1044  <aside>  — 左侧导航栏
行 1046-1049  <main>   — 主内容区开始
行 1051-1059  顶部 Top Bar（面包屑 + 搜索框）
行 1060-1761  7 个 panel div，每个是一个页面
  ├─ 1063: panel-dashboard   — 总览仪表盘
  ├─ 1119: panel-politics    — 政治（4 子 Tab）
  ├─ 1218: panel-english     — 英语（5 子 Tab）
  ├─ 1317: panel-theory      — 理论（4 子 Tab）
  ├─ 1476: panel-methods     — 方法（6 子 Tab）
  ├─ 1586: panel-mock-exam   — 模拟测试（独立面板）
  └─ 1719: panel-settings    — 设置
行 1762-1763  </main>
行 1764-5026  <script> — 全部 JavaScript，~3260 行
```

### Panel 和子 Tab 对照表

| 主面板 | 子 Tab ID | 内容 | 渲染函数 |
|--------|-----------|------|----------|
| panel-politics | sub-pol-quiz | 选择题刷题 | `renderPolQuiz(mod)` |
| | sub-pol-wrong | 错题本 | `renderPolWrong(mod)` |
| | sub-pol-essay | 分析题背诵 | `renderPolEssay(mod)` |
| | sub-pol-news | 时政速览 | 静态 HTML |
| panel-english | sub-eng-vocab | 单词闪卡 | `startVocabSession()` |
| | sub-eng-read | 阅读理解 | 静态 HTML |
| | sub-eng-write | 作文 | 静态 HTML（批改未接线） |
| | sub-eng-trans | 翻译 | 静态 HTML |
| panel-theory | sub-thr-concept | 概念分类浏览 | `renderCategoryBrowser()` |
| | sub-thr-quiz | 闪卡刷题 | `startThrFlash()` |
| | sub-thr-exam | 模拟考 | `startMockExam()` |
| panel-methods | sub-met-concept | 方法概念卡片 | `renderMetCards()` |
| | sub-met-formula | 公式手册 | `renderFormulaCards(phase)` |
| | sub-met-stat | 统计练习 | `renderStatExercises(phase)` |
| | sub-met-design | 研究设计 | `renderDesignCards()` |
| | sub-met-questions | 方法真题 | `renderMetQuestions()` |
| panel-mock-exam | — | 模拟测试 | 独立面板，无子 Tab |

### Panel 的 HTML 怎么写

每个 panel 遵循这个模板（在 `index.html` 里搜一个现成的抄）：

```html
<div class="panel" id="panel-xxx">
  <!-- 子 Tab 导航 -->
  <nav class="sub-tabs">
    <button class="sub-tab active" data-sub="xxx-tab1">标签1</button>
    <button class="sub-tab" data-sub="xxx-tab2">标签2</button>
  </nav>
  <!-- 子面板内容 -->
  <div class="sub-panel active" id="sub-xxx-tab1">...</div>
  <div class="sub-panel" id="sub-xxx-tab2">...</div>
</div>
```

子 Tab 切换逻辑是自动的（`<script>` 开头的委托事件，行 1790-1813），只要 `data-sub` 和 `id="sub-xxx"` 对上就行。**但如果你加了新 panel，要去 `switchPanel()` 函数（行 1768）和第 1790 行的子 Tab 委托里加对应的初始化逻辑。**

---

## 3. 数据接口（后端已就绪，前端只需读 JSON）

所有数据在 `data/` 目录，fetch 时带 `?v=N` 做缓存刷新。**改数据后必须升版本号，否则浏览器用旧缓存。**

| 文件 | 条目 | 大小 | 用途 |
|------|:--:|:--:|------|
| `concepts.json` | 2399 | ~2.3MB | 概念词典（term/definition/proponent/chapter/tags） |
| `concept-taxonomy.json` | 2243 分类 | ~150KB | 概念分类树，面包屑导航 |
| `exams.json` | 5651 | ~1.1MB | 16 校历年真题 |
| `methods-questions.json` | 898 | ~1.8MB | 方法专题题库 |
| `questions-theory.json` | 438 | ~1.1MB | 理论专题题库 |
| `theory-topics.json` | 208 | ~30KB | 理论考点摘要 |
| `method-exam-freq.json` | — | ~60KB | 方法概念考频 |
| `politics.json` | 1140 | ~756KB | 政治选择题 |
| `politics-essay.json` | 27 | ~116KB | 政治材料分析题 |
| `english-vocab.json` | 5169 | ~910KB | 考研英语词汇 |
| `schools.json` | 16 | ~10KB | 院校列表 |
| `exam-prompts.json` | 17 | ~30KB | 各校 AI 出题风格 prompt |
| `resources.json` | — | ~1.3MB | 资料库索引 |

### concepts.json 结构（样本）

```json
{
  "id": "c_5add096e",
  "term": "社会形态论",
  "definition": "社会形态论是马克思社会变迁理论的必要前提...",
  "proponent": "卡尔·马克思",
  "school": "",
  "chapter": "理论/古典/马克思/",
  "exam_frequency": "high",
  "core_points": ["生产力决定生产关系", "..."],
  "related": [{"id": "c_f6f5f5cd", "relation": "related", "term": "社会变迁理论"}],
  "source_text": "lcwiki compile",
  "textbook_ref": "侯钧生《西方社会学理论教程》 第61页",
  "tags": ["古典时期", "马克思"]
}
```

### 数据加载时序（重要！）

`concepts.json` 有 2.3MB，fetch 需要 1-3 秒。不要在它加载完之前渲染依赖概念的 UI。加载顺序：

1. `switchPanel()` → 如果 concepts 还没加载，显示 loading spinner
2. `loadConcepts()` → 并行 fetch concepts.json + concept-taxonomy.json
3. 加载完成后设置 `window.concepts`、`window.conceptIndex`、`window.taxonomy`
4. 触发当前 panel 的渲染

**改数据后**：找到 `index.html` 里对应的 fetch URL，手动升版本号。比如改了 `exams.json`，搜 `exams.json?v=` 把数字 +1。

---

## 4. 代码架构

### localStorage Key 全表

| 常量/Key | 用途 | 读写位置 | 数据格式 |
|----------|------|----------|----------|
| `LS_DASH` = `socio_dash_v2` | Dashboard 打卡+学习记录 | 行 3001-3004 | `{streak, lastActive, daily{date:views,exams}}` |
| `LS_FLASH` = `socio_flash_v1` | 闪卡 SM-2 状态 | 行 3031-3037 | `{conceptId: {due, interval, lastReview, reps}}` |
| `LS_APIKEY` = `socio_apikey_v1` | DeepSeek API Key | 行 3531-3564 | `{key: "sk-..."}` |
| `LS_POL_WRONG` = `socio_pol_wrong_v1` | 政治错题本 | 行 4149-4317 | `{qId: {_done, correct, chosen}}` |
| `LS_POL_ESSAY` = `socio_pol_essay_v1` | 政治分析题复习进度 | 行 4150-4518 | `{essayId: {reviewed, score}}` |
| `LS_ENG_VOCAB` = `socio_eng_vocab_v1` | 英语单词 SM-2 状态 | 行 4636-4711 | `{wordId: {due, interval, ...}}` |
| `socio_exam_log_v1` | 模拟考记录 | 行 3454 | `[{date, school, subject, score, ...}]` |
| `socio_concept_views_v1` | 概念浏览记录 | 行 3468 | `{"2026-07-29": ["c_xxx", "c_yyy"], ...}` — 日期为 key，值是当天浏览的概念 ID 数组 |
| ~~`socio_tasks_v2`~~ | 已废弃，不再使用 | 行 3571（仅清除） | — |

**加新 key 规则**：前缀 `socio_` + 描述 + `_v` + 版本号。在 script 顶部声明常量，别到处硬编码字符串。

### 全局变量

```js
// 导航状态
currentPanel          // 当前面板 ID

// 概念数据（核心）
concepts[]            // 全部概念 (from concepts.json)
conceptIndex{}        // id → concept 快速索引
taxonomy              // 概念分类树 (from concept-taxonomy.json)

// 分类浏览状态
_catState{subject}    // {period, thinkers[], tags[], viewMode}

// 闪卡 (SM-2)
flashState{}          // {conceptId: {due, interval, lastReview, lastQ, reps}}
thrFlashSession       // 当前闪卡会话 {queue, idx}

// 政治刷题
polQuestions[]        // 1140 题
polWrongState{}       // 错题状态
polEssayState{}       // 分析题复习状态

// 模拟考
examState{}           // 当前考试状态
examsData[]           // 5651 真题
examPrompts[]         // 17 校风格 prompt

// 英语
engVocabWords[]       // 5169 词
engVocabState{}       // SM-2 状态

// API
DEFAULT_API_KEY       // 内置 DeepSeek Key
```

### 关键函数映射

| 函数 | 作用 | 行号(约) |
|------|------|---------|
| `switchPanel(id)` | 切换主面板 | ~1768 |
| `loadConcepts()` | 加载 concepts.json + taxonomy | ~1833 |
| `renderCategoryBrowser()` | 渲染分类浏览（理论/方法共用） | ~2140 |
| `searchConceptsShell()` | 概念搜索入口 | ~2420 |
| `renderFormulaCards()` | 公式手册渲染 | ~3220 |
| `renderMetCards()` | 方法概念卡片 | ~3390 |
| `renderMetQuestions()` | 方法真题列表 | ~4100 |
| `startMockExam()` | 理论模拟考 | ~3740 |
| `submitExam()` | 提交模拟考 + AI 批改 | ~3850 |
| `renderPolQuiz(mod)` | 政治刷题 | ~4380 |
| `renderPolWrong(mod)` | 政治错题本 | ~4500 |
| `renderPolEssay(mod)` | 政治分析题 | ~4580 |
| `updateTodaySummary()` | Dashboard 摘要更新 | ~3443 |
| `updateDashboardPolStats()` | 政治卡片+徽章 | ~4617 |
| `callDeepSeek(sys, user)` | DeepSeek API 调用 | ~3560 |
| `getApiKey()` | API Key 获取（兜底默认Key） | ~3540 |

### 事件机制
- 分类浏览 click：`document.addEventListener('click', ...)` 统一处理，靠 `data-action` 属性分发
- 搜索：`conceptSearchShell` oninput → `searchConceptsDebounced()` (150ms 防抖)
- 方法搜索：`metCardSearch` addEventListener → debounced `renderMetCards()`
- 子Tab 切换：`.sub-tabs` 内 `click` 委托
- **注意**：没有用事件代理的地方，innerHTML 替换后事件会丢。用 `insertAdjacentHTML` 或者渲染完重新绑事件。

### CSS 变量体系
```css
--ink / --lead / --faint    文字层级
--surface / --surface2       背景层级
--border / --border-light    边框
--thr / --thr-bg / --thr-light  理论主题色
--met / --met-bg             方法
--pol / --pol-bg             政治
--eng / --eng-bg             英语
--good / --bad / --warn      语义色
--r-xs / --r-sm / --r-md     圆角
--fast / --ease              动画
```

**用 `var(--xxx)` 取色，别写死 hex 值。** 暗色模式通过切换 CSS 变量实现，写死颜色会在暗色下炸。

---

## 5. 文件结构

```
D:/workspace/sociology-kaoyan-app/
├── index.html          ← GitHub Pages 服务的就是这个（deploy.sh 从 web/ 拷过来）
├── data/               ← Pages 实际服务的数据文件（deploy.sh 同步）
│   ├── concepts.json       2399 条概念，~2.3MB（核心数据）
│   ├── exams.json          5651 道真题，16 校，~1.1MB
│   ├── politics.json       1140 道政治选择，~756KB
│   ├── politics-essay.json 27 道政治材料分析题
│   ├── english-vocab.json  5169 个考研英语词汇
│   ├── concept-taxonomy.json  概念分类体系
│   ├── methods-questions.json 898 道方法真题
│   ├── questions-theory.json  438 道理论真题
│   ├── theory-topics.json  208 条理论考点
│   ├── method-exam-freq.json  方法概念考频
│   ├── exam-prompts.json   17 校 AI 出题风格 prompt
│   ├── schools.json        16 校信息
│   ├── resources.json      资料库索引
│   └── rubric.md           评分标准
├── web/                   ← 工作副本（开发在这个目录改！）
│   ├── index.html         主文件，~5000 行
│   ├── data/              开发用的数据副本
│   └── js/
│       └── exam-engine.js  模拟考引擎（独立 JS）
├── tests/
│   ├── validate_data.py        Layer 0-A: 格式校验
│   ├── validate_data_semantic.py Layer 0-B: 语义校验
│   ├── audit_taxonomy.py       概念分类审计
│   └── specs/01-smoke.spec.ts  Playwright 冒烟测试
├── scripts/
│   └── build_taxonomy.py   概念分类树构建
├── deploy.sh              部署脚本
└── package.json           仅 Playwright 测试用
```

### ⚠️ 双副本结构

根目录 `data/` 和 `web/data/` 是两套，`deploy.sh` 负责同步。**你永远在 `web/index.html` 里改代码**，别碰根目录那个。改数据文件在 `web/data/`，部署时 `deploy.sh` 会拷到根目录。

---

## 6. 面板功能状态（改之前先确认没人在用）

### Dashboard（总览）
- ✅ 四个学科入口卡片（政治/英语/理论/方法），含进度条
- ✅ 今日学习摘要（刷题数/正确率/浏览概念/闪卡复习）—— `updateTodaySummary()`
- ✅ 刷题建议（根据错题和待复习量自动提示）—— `studySuggestion`
- ❌ 每日任务系统已删除（2026-07-29）
- ❌ 薄弱维度已删除（数据源单一）

### 政治 (panel-politics) — 4 子 Tab
- ✅ 选择题刷题 — 模块筛选 + 即时判对错 + 错题自动入库
- ✅ 错题本 — 按模块分组，可重做
- ✅ 分析题背诵 — 卡片式正反面
- ✅ 时政速览 — 热点卡片
- ⚠️ `politics.json` 有 6 题 answer 索引越界（OCR 选项合并问题，非前端 bug，见任务 #1）

### 英语 (panel-english) — 5 子 Tab
- ✅ 单词本 — SM-2 闪卡引擎，5169 词，含音标例句
- ✅ 阅读理解 — 硬编码 5 篇范例
- ✅ 作文 — 模板浏览 + AI 批改输入框
- ✅ 翻译 — 长难句拆解
- ⚠️ 作文批改按钮没接线（见任务 #5）

### 理论 (panel-theory) — 4 子 Tab
- ✅ 概念学习 — 分类浏览双视图：时代树 / 学者 A-Z
- ✅ 闪卡 — SM-2 间隔复习，deck 筛选
- ✅ 模拟考 — 出卷配置 + 计时 + DeepSeek AI 批改
- ⚠️ 模拟考 AI 批改 prompt 偏简单，分数虚高

### 方法 (panel-methods) — 6 子 Tab
- ✅ 概念卡片 — 分类浏览，搜索，高频筛选
- ✅ 公式手册 — 8 章公式卡片
- ✅ 统计练习 — 12 道硬编码经典计算题
- ✅ 研究设计 — 5 道硬编码场景设计题
- ✅ 真题题库 — 898 题，HTML 表格渲染

### 模拟测试 (panel-mock-exam) — 独立面板
- ✅ 学校/年份/科目选择器
- ✅ AI 出题模式（17 校个性化 prompt）
- ✅ 真题模式（5651 题按条件筛选）
- ✅ 计时 + 作答 + AI 批改

### 设置 (panel-settings)
- ✅ API Key 管理（localStorage 持久化，内置默认 Key）
- ✅ 数据清除
- ✅ 关于信息

---

## 7. 任务清单（开工！）

格式：每项 = 目标 + 涉及代码 + 怎么做 + 验收标准。从上往下做，别跳。

---

### 任务 #1：政治 6 题 answer 索引越界

- **难度**：⭐ | **类型**：修数据 | 估计 20 分钟
- **问题**：`politics.json` 里 `pol_10/29/46/49/77/363` 的 answer 指向了不存在的 option（OCR 把选项合并了，比如 "A.xxxB.yyy" 被当成一个选项）
- **涉及文件**：`web/data/politics.json`（和根目录 `data/politics.json` 同步修）
- **怎么做**：
  1. 搜这 6 个 ID，对照 question 文本里的选项字母和 options 数组长度
  2. 如果 options 数组比正确选项少（合并了），手动拆开
  3. 修完 answer 指向正确的选项索引
- **验收**：`python tests/validate_data.py` 不再报这 6 个越界

---

### 任务 #2：概念浏览记录写入

- **难度**：⭐⭐ | **类型**：功能修复 | 估计 30 分钟
- **问题**：`updateTodaySummary()` 读 `socio_concept_views_v1` 显示浏览数，但 `showConceptDetail()` 从来没写这个 key，永远是 "—"
- **涉及函数**：`showConceptDetail()`（搜索这个函数名找到它）、`updateTodaySummary()`（行 ~3443）
- **怎么做**：
  1. 在 `showConceptDetail()` 里，拿到概念 ID 后
  2. 读 `socio_concept_views_v1`：`JSON.parse(localStorage.getItem('socio_concept_views_v1') || '{}')`
  3. **注意数据格式**：`{"2026-07-29": ["c_xxx", "c_yyy"]}` — 日期做 key，值是当天浏览的概念 ID 数组（不是 `{conceptId: timestamp}`！）
  4. 写入逻辑：
     ```js
     var today = new Date().toISOString().slice(0, 10);
     if (!views[today]) views[today] = [];
     if (!views[today].includes(id)) views[today].push(id);
     ```
  5. 存回：`localStorage.setItem('socio_concept_views_v1', JSON.stringify(views))`
- **验收**：打开一个概念详情 → 切回 Dashboard → "浏览概念"数字变成 1

---

### 任务 #3：搜索快捷键 `/` 和 `Esc`

- **难度**：⭐ | **类型**：体验增强 | 估计 15 分钟
- **涉及代码**：在 `<script>` 顶部（`switchPanel` 附近，行 ~1765）加 `keydown` 监听
- **怎么做**：
  ```js
  document.addEventListener('keydown', e => {
    // 不在 input/textarea 里才触发
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
    if (e.key === '/') {
      e.preventDefault();
      const searchBox = document.getElementById('conceptSearchShell') || document.getElementById('metCardSearch');
      if (searchBox) searchBox.focus();
    }
    if (e.key === 'Escape') {
      // 关闭概念详情弹窗（调已有函数，别自己写 DOM 操作）
      if (typeof closeConceptDetail === 'function') closeConceptDetail();
    }
  });
  ```
- **注意**：`conceptSearchShell` 是理论面板的搜索框，`metCardSearch` 是方法面板的。两个都要覆盖。
- **验收**：在 Dashboard 按 `/` → 跳转到理论面板并聚焦搜索框；按 `Esc` → 关闭概念详情

---

### 任务 #4：搜索结果高亮

- **难度**：⭐⭐ | **类型**：体验增强 | 估计 30 分钟
- **问题**：搜索概念时匹配的文字没有高亮，不知道哪个字匹配了
- **涉及函数**：`searchConceptsShell()` 和概念列表渲染部分（行 ~2420 附近）
- **怎么做**：
  1. 找到渲染搜索结果列表的循环
  2. 对每个结果的 `term` 和 `definition` 片段，用 `<mark>` 或 `<span class="hl">` 包裹匹配文字
  3. CSS 里加 `.hl { background: var(--thr-light); border-radius: var(--r-xs); }`
- **验收**：搜索"社会" → 结果列表里"社会"俩字有高亮背景

---

### 任务 #5：英语作文批改按钮接线

- **难度**：⭐⭐ | **类型**：功能补全 | 估计 30 分钟
- **问题**：`sub-eng-write` 里有 AI 批改按钮（textarea + 按钮），但 `onclick` 没接
- **涉及代码**：panel-english 的 sub-eng-write 区域（行 ~1218-1316 之间），`callDeepSeek()`（行 ~3560）
- **怎么做**：
  1. 找到作文批改的 textarea 和按钮
  2. 按钮 `onclick` 调用一个新函数 `gradeEnglishEssay()`
  3. `gradeEnglishEssay()` 获取 textarea 内容 → 拼 system/user prompt → 调 `callDeepSeek()` → 渲染结果到下面的 div
  4. system prompt 参考：考研英语一大作文评分标准（内容/结构/语言/字数）
  5. 调用期间按钮 disabled + 文字变"批改中..."
- **验收**：写一段英语作文 → 点批改 → 看到 AI 返回的分数和评语

---

### 任务 #6：统计练习从 methods-questions.json 动态加载

- **难度**：⭐⭐⭐ | **类型**：数据接入 | 估计 45 分钟
- **问题**：`renderStatExercises()` 目前 12 道硬编码题，`methods-questions.json` 里还有大量计算题没接入
- **涉及函数**：`renderStatExercises(phase)`（搜索这个函数名）
- **涉及数据**：`methods-questions.json`，筛选 `type === "计算"` 的条目
- **怎么做**：
  1. 找到 `renderStatExercises()`，看懂现有硬编码数据结构
  2. 新增 `loadStatQuestions()`：fetch `methods-questions.json` → filter `type === "计算"` → 转成和硬编码一样的格式
  3. 把 `renderStatExercises()` 改成优先用动态数据，fallback 硬编码
  4. 按章节筛选逻辑保持一致
- **验收**：打开统计练习 → 看到的不止 12 道题 → 切换章节筛选正常

---

### 任务 #7：Dashboard 英语/政治进度条

- **难度**：⭐⭐ | **类型**：功能补全 | 估计 30 分钟
- **问题**：Dashboard 四个学科卡片，理论和方法有进度条（来自闪卡数据），英语和政治是空的
- **涉及函数**：`updateTodaySummary()`（行 ~3443）、闪卡进度计算逻辑
- **怎么做**：
  1. 政治进度 = 错题本里做过的题数 / 1140
  2. 英语进度 = 闪卡里复习过的单词数 / 5169
  3. 在 Dashboard 渲染时读 `LS_POL_WRONG` 和 `LS_ENG_VOCAB`，算百分比
  4. 更新对应卡片的 `.sc-pct` 和进度条宽度
- **验收**：做过政治题后切回 Dashboard → 政治卡片显示进度百分比

---

## 8. 常见改动模式

### 加一个数据 fetch

```js
async function loadMyNewData() {
  try {
    const resp = await fetch('data/my-new-data.json?v=1');
    const data = await resp.json();
    window.myNewData = data;
    return data;
  } catch(e) {
    console.warn('my-new-data 加载失败', e);
    return [];
  }
}
```

记得：**所有 fetch URL 带版本号**（`?v=1`），改数据后升版本号。数据放 `window.xxx` 全局变量供其他函数用。

### 加一个子 Tab

1. 在目标 panel 的 `.sub-tabs` 里加 `<button class="sub-tab" data-sub="xxx-newtab">新标签</button>`
2. 在 panel 里加 `<div class="sub-panel" id="sub-xxx-newtab">...</div>`
3. 去 `<script>` 顶部（行 ~1808）的子 Tab 切换回调里加一条：`else if (subId === 'xxx-newtab') myRenderFunc();`

### 加 localStorage 持久化

```js
// 在 script 顶部声明常量
const LS_MY_FEATURE = 'socio_my_feature_v1';

// 读
let myState = {};
try { myState = JSON.parse(localStorage.getItem(LS_MY_FEATURE) || '{}'); } catch(e) {}

// 写
function saveMyState() {
  try { localStorage.setItem(LS_MY_FEATURE, JSON.stringify(myState)); } catch(e) {}
}
```

**铁律**：key 前缀 `socio_`，用 try/catch 包裹（storage 可能满），存 JSON 别存裸字符串。

---

## 9. 本地开发

```bash
# 起服
cd D:/workspace/sociology-kaoyan-app/web
python -m http.server 8765
# → http://localhost:8765

# 冒烟测试（自动起服）
cd D:/workspace/sociology-kaoyan-app
npx playwright test tests/specs/01-smoke.spec.ts --reporter=list

# 数据校验
python tests/validate_data.py
python tests/validate_data_semantic.py
python tests/audit_taxonomy.py
```

**调试技巧**：
- 所有数据 fetch 带 `?v=N`，改数据后必须升版本号
- `concepts.json` 加载慢（~2.3MB），不要频繁 reload——用 Live Edit
- localStorage 清空：DevTools → Application → Clear site data

---

## 10. 部署流程

```bash
cd D:/workspace/sociology-kaoyan-app
bash deploy.sh
```

`deploy.sh` 步骤：
1. 跑 `validate_data.py`（仅警告不阻断）
2. 从 `web/` 拷贝 `index.html` 到根目录
3. 拷贝所有数据文件到根 `data/`
4. 拷贝 JS 文件到根 `js/`
5. git add + commit + push

**改代码不需要你跑 deploy**，deploy 是 Claude 的活。你只需要确保改的是 `web/index.html`。

---

## 11. 踩过的坑（别他妈再踩）

| 坑 | 教训 |
|----|------|
| **缓存版本号** | fetch URL 里 `?v=N` 是唯一的缓存控制手段（GitHub Pages 无服务端配置）。改数据不升版本号 = 用户看到旧数据 |
| **双副本结构** | 根目录和 `web/` 各一套数据。deploy.sh 从 web 拷到根。**你永远只改 web/ 下的文件** |
| **字体跨域** | GitHub Pages 的字体文件可能被浏览器 CORS 拦截，CSS `@font-face` 加 `crossorigin="anonymous"` |
| **Worker 静默** | 原 Worker 后端已废弃，health check 返回 404 是预期行为。Network 面板的红色 404 不用管 |
| **exams.json 体积** | 1.1MB，fetch 加载需 ~1-3 秒。不要把它当依赖在其他数据没加载完时就开始渲染 |
| **DeepSeek API 费用** | 模拟考批改每次约 ¥0.01-0.03，AI 出题约 ¥0.05-0.10。内置了默认 Key |
| **单文件 5000 行** | 没有模块化，全局变量遍地。改代码前先 `grep` 确认函数/变量名不被别处引用 |
| **概念 ID 格式** | `c_xxxxxxxx` 是原始概念，`lc_xxxxxxxx` 是从 lcwiki 补充的。taxonomy 只索引了 ID，需要 `conceptIndex[id]` 查详情 |
| **innerHTML 会丢事件** | 用 innerHTML 替换 DOM 后，之前绑的事件监听器全丢。要么用 `insertAdjacentHTML`，要么渲染完重新绑 |

---

## 12. 如果 Trae 要接手

1. **用户先跑** `python -m http.server 8765`（在 web/ 目录），确认页面能打开
2. **改代码在 `web/index.html`**，别动根目录那个
3. **改数据在 `web/data/`**，同步到根目录用 `deploy.sh`（Claude 跑）
4. **每次改动后保存 → 刷新浏览器 → 看效果**，别攒一堆再测
5. **改 `concepts.json` 要格外小心**——2.3MB 的 JSON，手改容易坏格式，建议用脚本操作
6. **新功能加新的 localStorage key**，前缀统一用 `socio_`，不要污染 ls
7. **不确定的事直接问用户**，别猜。猜错了浪费所有人的时间
