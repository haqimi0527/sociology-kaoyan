# 给 Trae 的开工 Prompt

> 把这个文件的内容复制粘贴给 Trae，它就知道该怎么干了。

---

## 完整版（推荐，第一次用这个）

```
你接手一个社会学考研 Web App 的前端维护和功能开发。

<project_context>
- 项目：社会学考研 AI 导师，单文件 Web App，原生 HTML+CSS+JS
- 线上：https://cykaoyan.top
- 数据：2399 条概念、5651 道真题、5169 词汇，静态 JSON 加载
- 已有 7 个功能面板（Dashboard/政治/英语/理论/方法/模拟测试/设置），大部分功能完备
- 你的工作是在现有代码上修 bug、补功能、优化体验
</project_context>

<workflow>
在写任何代码之前，严格按以下顺序操作：

1. **读文档**：打开并通读以下两份文件，两份都认真读，别跳
   - `docs/HANDOFF_TO_TRAE.md` — 前端交接文档（代码架构、函数索引、7 个任务卡片）
   - `docs/HANDOFF_TO_TRAE_BACKEND.md` — 后端管线文档（Python 脚本、数据 schema、10 条铁律）

2. **确认环境**：确认工作目录是 `D:/workspace/sociology-kaoyan-app/`，代码文件是 `web/index.html`

3. **选任务**：打开 `HANDOFF_TO_TRAE.md` 第 7 节，从任务 #2 开始，按编号顺序做

4. **每次只做一个任务**：
   a. 读任务卡片里的"涉及函数"，找到对应代码位置
   b. 写代码
   c. 告诉用户"改完了，刷新浏览器看效果"
   d. 用户确认通过后，再做下一个

5. 遇到不确定的事，直接问用户，不要猜
</workflow>

<constraints>
**必须遵守**：
- 只改 `web/index.html`，不要碰根目录的 `index.html`
- 不要引入任何新框架或 npm 依赖
- CSS 颜色用 `var(--ink)` `var(--thr)` `var(--surface)` 等已有变量，不要写 hex 值
- 所有 fetch URL 带 `?v=N` 版本号（如 `data/concepts.json?v=3`）
- localStorage key 前缀统一 `socio_`，格式 `socio_功能名_v版本号`

**禁止做**：
- 不要改 `concepts.json`、`exams.json` 等数据文件（那是 Claude 管的）
- 不要自己跑 `deploy.sh` 或 git 操作
- 不要重构/拆分 index.html 的文件结构
- 不要在 print/debug 输出里用 emoji
</constraints>

<example_good_fix>
用户说：概念浏览记录一直是"—"，Dashboard 不显示数字。

你的做法：
1. 打开 HANDOFF_TO_TRAE.md → 找到任务 #2
2. 任务卡片说：在 `showConceptDetail()` 里加 `localStorage.setItem('socio_concept_views_v1', ...)` 写入逻辑
3. 搜索 `showConceptDetail` 找到函数位置
4. 在函数里概念 ID 确定后，加：
   - 读现有 views：`var views = JSON.parse(localStorage.getItem('socio_concept_views_v1') || '{}');`
   - 数据格式是 `{"2026-07-29": ["c_xxx"]}`，不是 `{conceptId: timestamp}`
   - 写入：`var today = new Date().toISOString().slice(0,10); if(!views[today]) views[today]=[]; if(!views[today].includes(id)) views[today].push(id);`
   - 存回：`localStorage.setItem('socio_concept_views_v1', JSON.stringify(views));`
5. 改完告诉用户刷新验证
</example_good_fix>

<example_bad>
用户说：概念浏览记录不显示。

❌ 你的做法：
1. 没读文档，直接搜 `updateTodaySummary`
2. 发现函数里读 localStorage 的逻辑是对的
3. 以为是 localStorage 的 bug，开始改存储逻辑
4. 改了一个小时发现是上游没写入
5. 浪费所有人的时间

教训：先读文档！文档里已经写了"showConceptDetail() 没有写 socio_concept_views_v1"。
</example_bad>

<first_task>
你的第一个任务是 **HANDOFF_TO_TRAE.md 第 7 节的任务 #2：概念浏览记录写入**。

现在开始：先读完上面说的两份文档，然后找到任务 #2 的卡片，照着做。
</first_task>
```

---

## 精简版（后续追加任务时用）

```
继续做 HANDOFF_TO_TRAE.md 第 7 节的任务 #3：搜索快捷键 `/` 和 `Esc`。

读任务卡片 → 找到涉及函数 → 写代码 → 告诉我刷新验证。

不要碰其他任务，只做这一个。
```

---

## 后端任务版（让 Trae 写 Python/Shell）

```
接手社会学考研 App 的后端管线维护。

<workflow>
1. 先读 `docs/HANDOFF_TO_TRAE_BACKEND.md`，搞清楚你能干什么、不能干什么
2. 从任务 B2（GitHub Actions CI）开始，这是最独立的任务
3. 每个任务做完告诉我验收方法
</workflow>

<constraints>
- Python 脚本用 UTF-8 编码，文件头加 `# -*- coding: utf-8 -*-`
- 路径统一用正斜杠 `/`
- 所有脚本支持 `--dry-run` 参数（先打印要做什么，不实际执行）
- 不要在 print 里用 emoji（Windows GBK 编码会炸）
- 改 concepts.json 之前必须备份（这是铁律）
</constraints>

<first_task>
先读 `docs/HANDOFF_TO_TRAE_BACKEND.md`，然后做任务 B2：GitHub Actions CI。
</first_task>
```
