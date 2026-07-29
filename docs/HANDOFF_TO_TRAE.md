# 社会学考研 App — 前端交接文档（给 Trae）

> 📅 2026-07-29 | 作者：Claude Code | 线上：https://cykaoyan.top

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

## 2. 文件结构

```
D:/workspace/sociology-kaoyan-app/
├── index.html          ← GitHub Pages 服务的就是这个（deploy.sh 从 web/ 拷过来）
├── data/               ← Pages 实际服务的数据文件（deploy.sh 同步）
│   ├── concepts.json       2399 条概念，~2.3MB（核心数据）
│   ├── exams.json          5651 道真题，16 校，~1.1MB
│   ├── politics.json       1140 道政治选择，~756KB
│   ├── politics-essay.json 27 道政治材料分析题
│   ├── english-vocab.json  5169 个考研英语词汇
│   ├── concept-taxonomy.json  概念分类体系（理论：时期→学派→学者，方法：大类→子类）
│   ├── methods-questions.json 898 道方法真题
│   ├── theory-topics.json  208 条理论考点
│   ├── questions-theory.json  438 道理论真题
│   ├── method-exam-freq.json  方法概念考频
│   ├── exam-prompts.json   17 校 AI 出题风格 prompt
│   ├── schools.json        16 校信息
│   ├── resources.json      资料库索引
│   └── rubric.md           评分标准
├── web/                   ← 工作副本（开发在这个目录改）
│   ├── index.html         主文件，~5000 行
│   ├── data/              同上（开发用的数据副本）
│   └── js/
│       └── exam-engine.js  模拟考引擎（独立 JS）
├── tests/
│   ├── validate_data.py        Layer 0-A: 格式校验（ID唯一、文件大小、跨文件引用）
│   ├── validate_data_semantic.py Layer 0-B: 语义校验（幻觉检测、年份合理性）
│   ├── audit_taxonomy.py       概念分类审计
│   └── specs/01-smoke.spec.ts  Playwright 冒烟测试
├── deploy.sh              部署脚本（web/ → 根目录 → git push）
└── package.json           仅 Playwright 测试用
```

### 双副本结构（注意！）

根目录 `data/` 和 `web/data/` 是两套，`deploy.sh` 负责同步。改数据时两边都要更新，否则线上和本地不一致。

---

## 3. 面板功能状态

### Dashboard（总览）
- ✅ 四个学科入口卡片（政治/英语/理论/方法），含进度条
- ✅ 今日学习摘要（刷题数/正确率/浏览概念/闪卡复习）—— `updateTodaySummary()`
- ✅ 刷题建议（根据错题和待复习量自动提示）—— `studySuggestion`
- ❌ 每日任务系统已删除（2026-07-29，硬编码无用）
- ❌ 薄弱维度已删除（数据源单一，不准确）

### 政治 (panel-politics) — 4 子 Tab
- ✅ 选择题刷题 (sub-pol-quiz) — 模块筛选 + 即时判对错 + 错题自动入库
- ✅ 错题本 (sub-pol-wrong) — 按模块分组，可重做
- ✅ 分析题背诵 (sub-pol-essay) — 卡片式正反面
- ✅ 时政速览 (sub-pol-news) — 热点卡片
- ✅ 资料库 (sub-pol-resource)
- ⚠️ `politics.json` 有 6 题 answer 索引越界（OCR 选项合并问题，非前端 bug）

### 英语 (panel-english) — 5 子 Tab
- ✅ 单词本 (sub-eng-vocab) — SM-2 闪卡引擎，5169 词，含音标例句
- ✅ 阅读理解 (sub-eng-read) — 硬编码 5 篇范例（真题数据暂无）
- ✅ 作文 (sub-eng-write) — 模板浏览 + AI 批改输入框
- ✅ 翻译 (sub-eng-trans) — 长难句拆解
- ✅ 资料库 (sub-eng-resource)
- ⚠️ 作文 4 个 txt 模板已加载但展示偏简陋

### 理论 (panel-theory) — 4 子 Tab
- ✅ 概念学习 (sub-thr-concept) — **分类浏览双视图**：时代树 / 学者 A-Z，搜索+概念详情+关联概念
- ✅ 闪卡 (sub-thr-flash) — SM-2 间隔复习，deck 筛选
- ✅ 模拟考 (sub-thr-exam) — 出卷配置 + 计时 + DeepSeek AI 批改
- ✅ 资料库 (sub-thr-resource)
- ⚠️ 模拟考 AI 批改 prompt 偏简单，分数虚高

### 方法 (panel-methods) — 6 子 Tab
- ✅ 概念卡片 (sub-met-concept) — 分类浏览，搜索，高频筛选
- ✅ 公式手册 (sub-met-formula) — 8 章公式卡片，展开看条件+示例
- ✅ 统计练习 (sub-met-stat) — 12 道硬编码经典计算题，按章节筛选
- ✅ 研究设计 (sub-met-design) — 5 道硬编码场景设计题
- ✅ 资料库 (sub-met-resource)
- ✅ 真题题库 (sub-met-questions) — 898 题，题型筛选，HTML 表格渲染
- ⚠️ 公式卡片数据依赖 `concepts.json` 的 `core_points` 字段提取

### 模拟测试 (panel-mock-exam) — 独立面板
- ✅ 学校/年份/科目选择器
- ✅ AI 出题模式（17 校个性化 prompt）
- ✅ 真题模式（5651 题按条件筛选）
- ✅ 计时 + 作答 + AI 批改
- ⚠️ 16 校真题年份分布不均（浙大 12 题，人大 773 题）

### 设置 (panel-settings)
- ✅ API Key 管理（localStorage 持久化，内置默认 Key）
- ✅ 数据清除
- ✅ 关于信息

---

## 4. 代码架构

### 全局变量（按类别）

```
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
polWrongState{}       // {qId: {_done, correct, chosen}}
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

// localStorage keys
LS_FLASH, LS_DASH, LS_POL_WRONG, LS_POL_ESSAY, LS_ENG_VOCAB, LS_APIKEY, LS_TASKS(已废弃)
```

### 关键函数映射

| 函数 | 作用 | 行号(约) |
|------|------|---------|
| `switchPanel(id)` | 切换主面板 | ~1800 |
| `loadConcepts()` | 加载 concepts.json + taxonomy | ~1859 |
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

---

## 5. 本地开发

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
- 所有数据 fetch 带 `?v=N` 缓存版本号，改数据后必须升版本号，否则浏览器用旧缓存
- `concepts.json` 加载慢（~2.3MB），不要频繁 reload——用 Live Edit
- localStorage 清空：DevTools → Application → Clear site data

---

## 6. 部署流程

```bash
cd D:/workspace/sociology-kaoyan-app
bash deploy.sh          # 自动跑数据校验 → 拷贝 web/ → git commit → push
```

`deploy.sh` 步骤：
1. 跑 `validate_data.py`（仅警告不阻断）
2. 从 `web/` 拷贝 `index.html` 到根目录
3. 拷贝所有数据文件到根 `data/`
4. 拷贝 JS 文件到根 `js/`
5. git add + commit + push

**版本号管理**：手动在 `web/index.html` 的 fetch URL 里改 `?v=N`。改了 `exams.json` 就升 `exams.json?v=17` → `?v=18`。

---

## 7. 待办优先级（给 Trae）

### P0 — 影响核心体验
1. **政治 6 题 answer 越界** — `politics.json` 里 `pol_10/29/46/49/77/363` 的 answer 索引超出 options 数组（OCR options 合并问题），需手动修数据
2. **概念浏览记录** — `updateTodaySummary()` 读取 `socio_concept_views_v1`，但浏览概念时没有写这个 key，永远是 "—"。需要在 `renderConceptDetail()` 里加写入逻辑

### P1 — 明显改善
3. **公式手册数据增强** — 现在靠正则从 `core_points` 提取公式，命中率一般。可以给 `concepts.json` 加 `formula` 字段
4. **模拟考 AI 批改优化** — prompt 偏简单，分数虚高。需要更严格的评分标准
5. **英语作文批改接入** — HTML 和 API 都有了，但 `sub-eng-write` 的批改按钮没接线
6. **统计练习/研究设计扩容** — 目前 12 题+5 题硬编码，可从 `methods-questions.json` 的计算题导入更多

### P2 — 锦上添花
7. **概念搜索结果高亮** — 搜索匹配文字无高亮，体验差
8. **拼音搜索** — 概念搜索不支持拼音，"yihua" 搜不到"异化"
9. **快捷键** — `/` 聚焦搜索框，`Esc` 关闭详情
10. **Dashboard 学科卡片添加英语/政治进度条** — 目前理论和方法的进度条来自闪卡数据，英语和政治是空的

---

## 8. 踩过的坑

| 坑 | 教训 |
|----|------|
| **缓存版本号** | fetch URL 里 `?v=N` 是唯一的缓存控制手段（GitHub Pages 无服务端配置）。改数据不升版本号 = 用户看到旧数据 |
| **双副本结构** | 根目录和 `web/` 各一套数据。deploy.sh 从 web 拷到根。改文件时两边都要看，否则 commit 漏文件 |
| **字体跨域** | GitHub Pages 的字体文件可能被浏览器 CORS 拦截，CSS `@font-face` 加 `crossorigin="anonymous"` |
| **Worker 静默** | 原 Worker 后端已废弃，health check 返回 404 是预期行为。浏览器 Network 面板的红色 404 不用管 |
| **exams.json 体积** | 1.1MB，fetch 加载需 ~1-3 秒。不要把它当依赖在其他数据没加载完时就开始渲染 |
| **DeepSeek API 费用** | 模拟考批改每次约 ¥0.01-0.03，AI 出题约 ¥0.05-0.10。内置了默认 Key，用户零配置可用 |
| **单文件 5000 行** | 没有模块化，全局变量遍地。改代码前先 `grep` 确认函数/变量名不被别处引用。改完跑冒烟测试 |
| **概念 ID 格式** | `c_xxxxxxxx` 是原始概念，`lc_xxxxxxxx` 是从 lcwiki 补充的。taxonomy 只索引了 ID，需要 `conceptIndex[id]` 查详情 |

---

## 9. 数据文件依赖关系

```
concepts.json (核心, ~2.3MB)
  ├── concept-taxonomy.json (概念分类索引, 用 ID 关联)
  ├── conceptExtras (概念增强数据, 真题年份+多版定义, 内嵌在 concepts.json 的 _extras)
  ├── theory-topics.json (理论考点, 用 conceptName 关联)
  └── method-exam-freq.json (方法考频, 用 conceptName 关联)

exams.json (真题, ~1.1MB)
  ├── schools.json (16 校元信息)
  └── exam-prompts.json (17 校 AI 出题 prompt)

politics.json (政治选择, ~756KB)
politics-essay.json (政治分析题, ~116KB)
english-vocab.json (英语词汇, ~910KB)
methods-questions.json (方法真题, ~1.8MB 含备份)
questions-theory.json (理论真题, ~1.1MB)
resources.json (资料库索引, ~1.3MB)
```

---

## 10. 如果 Trae 要接手

1. **先跑一遍冒烟测试**，确认环境正常：`npx playwright test --reporter=list`
2. **改代码在 `web/index.html`**，别动根目录那个
3. **改数据在 `web/data/`**，同步到根目录用 `deploy.sh`
4. **提交前跑 `python tests/validate_data.py`**，确认没引入数据错误
5. **改 `concepts.json` 要格外小心**——2.3MB 的 JSON，手改容易坏格式，建议用脚本操作
6. **新功能加新的 localStorage key**，前缀统一用 `socio_`，不要污染 ls
