# 前端需求文档 — 社会学考研 AI 导师 v3

> 交付给前端开发。当前代码在 `web/index.html`（单文件 5135 行 HTML+CSS+JS），数据在 `web/data/`。

---

## 数据接口（后端已就绪，前端只需读 JSON）

所有数据在 `data/` 目录，fetch 时带 `?v=N` 做缓存刷新。关键文件：

| 文件 | 条目 | 用途 |
|------|:--:|------|
| `concepts.json` | 2399 | 概念词典（term/definition/proponent/chapter/tags） |
| `concept-taxonomy.json` | 2243 分类 | 概念分类树，前端面包屑导航 |
| `exams.json` | 5651 | 16 校历年真题（名词解释/简答/论述/计算） |
| `methods-questions.json` | 898 | 方法专题题库 |
| `theory-questions.json` | 438 | 理论专题题库 |
| `politics.json` | 1140 | 政治选择题（马原/毛中特/史纲/思修） |
| `english-vocab.json` | 5169 | 考研英语词汇 |
| `schools.json` | 16 | 院校列表 |

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

---

## P0: 必须做的（当前是占位符/假数据）

### 1. 方法面板 — 公式手册
- **现状**：`index.html` 里有 `<div id="formula-handbook">` 空壳
- **数据**：`D:\workspace\ocr_stats_formulas_*.txt`（3个文件，统计公式 OCR 文本），需结构化后放入 data/
- **要做的**：显示公式列表，按主题分组（描述统计/推断统计/回归），支持搜索

### 2. 方法面板 — 统计练习
- **现状**：占位符 div
- **数据**：`exams.json` 里有 154 道 `type: "计算"` 的题
- **要做的**：随机抽题、计时、输入答案、对答案

### 3. 方法面板 badge 硬编码 "0"
- **现状**：`<span class="badge">0</span>` 写死的
- **修复**：读 `exams.json` 里方法相关题数，动态填入

---

## P1: 提升体验

### 4. API Key 持久化
- **现状**：输入框的值刷新就丢
- **修复**：存 `localStorage`，页面加载时恢复
- **key**: `deepseek_api_key`

### 5. 概念关系图谱（Canvas）
- **现状**：`<div id="concept-graph">` 空壳
- **数据**：`concepts.json` 里每个概念有 `related` 数组
- **要做的**：选中一个概念 → 画它和关联概念的节点图（用 D3.js 或 vis.js CDN）

### 6. 搜索快捷键 `/`
- **现状**：没有键盘快捷键
- **修复**：按 `/` → focus 搜索框

---

## P2: 锦上添花

### 7. Toast 通知组件
- 操作反馈（"已复制"、"保存成功"、"AI 回复中..."）
- 不用引入库，原生 CSS animation 就行

### 8. 设置面板 — 清除数据
- **现状**：`alert('清除成功')` 空壳
- **修复**：弹确认框 → 清 localStorage → 刷新

### 9. 概念对比模式
- 选 2-3 个概念并排显示（term/definition/proponent/异同点）

---

## 不需要做的

- 政治面板（选择题/错题本/材料分析题/时政）
- 英语面板（词汇/阅读/写作/翻译）
- 模拟考 UI
- 研究设计 UI
- DeepSeek API 客户端（AI 对话/出题）

---

## 技术约束

- **单文件**：所有 HTML+CSS+JS 在 `web/index.html`，不改架构
- **无框架**：原生 JS，不引入 React/Vue
- **CDN 库**：如需图表用 Chart.js CDN，图谱用 vis.js CDN
- **CSS 变量**：已有完整 design system（4 科主题色 + 暗色模式），复用 `var(--*)`
- **数据路径**：所有 fetch 用相对路径 `data/xxx.json?v=N`，版本号手动管理

---

## 验证

1. 本地起服：`cd web && python -m http.server 8765`
2. 浏览器打开 `http://localhost:8765`
3. 检查：概念列表加载正常、搜索可用、分类面包屑正常
4. `deploy.sh` 推到 cykaoyan.top
