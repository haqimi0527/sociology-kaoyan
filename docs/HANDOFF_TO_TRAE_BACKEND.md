# 社会学考研 App — 后端/数据管线交接文档（给 Trae）

> 📅 2026-07-29 | 作者：Claude Code | 线上：https://cykaoyan.top
>
> **这份文档是干什么的**：告诉你哪些后端活能写代码搞定，哪些必须我来跑。每条任务都有技术规格，照着写就行。

---

## 0. 先说清楚：Trae 能干什么，不能干什么

### ✅ 能干的（纯写代码）

| 类别 | 活 | 说明 |
|------|-----|------|
| Python 脚本 | 数据提取、格式转换、JSON 合并去重 | 正则提取、字段映射、校验规则 |
| Shell 脚本 | deploy.sh 增强、批处理 | 文件同步、git 操作、curl 验证 |
| CI/CD | GitHub Actions workflow | YAML 写 pipeline，不需要运行时 |
| 代码整理 | 脚本归档、函数抽取、加注释 | 重构不改变行为 |
| 测试 | validate 规则扩充、冒烟测试用例 | 写校验逻辑，我来跑 |

### ❌ 干不了的（需要运行时环境）

| 活 | 为什么 Trae 不行 |
|----|-------------------|
| PaddleOCR 跑 OCR | 需要 GPU/CPU 推理、大模型文件、本地环境 |
| DeepSeek API 大规模调用 | 需要 key、分 chunk 策略、网络、重试、结果校验 |
| 数据质量肉眼审查 | 需要看实际数据内容、对照 taxonomy、社会学知识 |
| Git push / deploy | 需要仓库权限、SSH 配置 |
| 任何需要"看一眼实际数据"的决策 | Trae 没有 memory，不知道 2399 条概念的结构 |

---

## 1. 项目数据管线总览

```
OCR 文本 → 提取脚本 → 中间 JSON → 合并去重 → concepts.json → validate → deploy
                             ↑                    ↑              ↑
                        _extract_*.py      _merge_all.py   validate_data.py
                        (10个散落在         build_taxonomy   validate_data_semantic.py
                         D:\workspace\)       .py           audit_taxonomy.py
```

### 文件位置（两种，别搞混）

| 位置 | 放什么 | 举例 |
|------|--------|------|
| `D:/workspace/sociology-kaoyan-app/` | 项目仓库内的脚本 | `tests/validate_data.py`、`scripts/build_taxonomy.py`、`deploy.sh` |
| `D:/workspace/` | 临时/一次性的提取脚本和中间文件 | `_extract_nouns.py`、`_merge_all.py`、OCR 输出文本 |

**后者的脚本需要整理归档到前者的 `pipeline/` 目录。** 这是任务之一（见下文）。

### 管线阶段

| 阶段 | 工具 | 输入 | 输出 |
|------|------|------|------|
| OCR | PaddleOCR（Claude 跑） | PDF/图片/扫描件 | TXT 文本 |
| 提取 | `_extract_*.py`（10 个） | TXT 文本 | 中间 JSON |
| 合并 | `_merge_all.py` | 多个中间 JSON | 去重后的增量 JSON |
| 入库 | Claude 手动 merge | 增量 JSON + 现有 concepts.json | 更新后的 concepts.json |
| 分类 | `build_taxonomy.py` | concepts.json | concept-taxonomy.json |
| 校验 | `validate_data.py` + `validate_data_semantic.py` | concepts.json + 其他 data/*.json | ERROR/WARN 报告 |
| 部署 | `deploy.sh` | web/ → repo root | git push → GitHub Pages |

---

## 2. 核心数据文件 Schema

### concepts.json — 概念词典（最核心）

```json
{
  "id": "c_5add096e",                  // 唯一 ID，c_xxxxxxxx = 原始, lc_xxxxxxxx = lcwiki补充
  "term": "社会形态论",                 // 概念名（中文）
  "definition": "...",                 // 定义文本
  "proponent": "卡尔·马克思",          // 提出者（标准化全名，不能写简称）
  "school": "",                        // 学派（大部分为空，从 chapter 推断）
  "chapter": "理论/古典/马克思/",      // 分类路径（/ 分隔，/ 结尾）
  "exam_frequency": "high",            // 考频：high / medium / low / ""
  "core_points": ["点1", "点2"],       // 核心要点（可能为空数组）
  "related": [                         // 关联概念（可能为空数组）
    {"id": "c_f6f5f5cd", "relation": "related", "term": "社会变迁理论"}
  ],
  "source_text": "lcwiki compile",     // 来源标记
  "textbook_ref": "侯钧生《西方社会学理论教程》 第61页",  // 教材出处
  "tags": ["古典时期", "马克思"]        // 标签
}
```

**铁律**：
- `id` 不可重复，`term` 可重复（同名不同源=独立概念）
- `chapter` 路径必须以 `/` 结尾
- `proponent` 必须用全名（"卡尔·马克思"），不能写简称（"马克思"）
- 不要删 `related` 或 `core_points` 字段，可以为空数组
- **改 concepts.json 前必须备份**：`cp concepts.json concepts_backup_$(date +%Y%m%d_%H%M%S).json`

### exams.json — 真题

```json
{
  "id": "e_xxx",
  "school": "中国人民大学",
  "year": 2023,
  "type": "简答",                       // 名词解释/简答/论述/计算/设计题/单选/多选/判断/填空/辨析/分析
  "subject": "theory",                  // theory / methods
  "question": "简述...",
  "answer": "参考答案...",             // 可能为空字符串
  "score": 15                           // 可能为 null
}
```

### concept-taxonomy.json — 分类树

```json
{
  "theory": {
    "古典时期 (1830s-1920s)": {
      "实证主义": {
        "desc": "...",
        "scholars": {
          "孔德": {"concepts": ["c_xxx", "c_yyy"], "keywords": ["孔德", "社会静力学", ...]}
        }
      }
    }
  },
  "methods": {
    "方法论基础": {
      "categories": {
        "科学哲学": {"desc": "...", "concepts": ["c_xxx"], "keywords": [...]}
      }
    }
  },
  "intro": {
    "社会学概论": {"concepts": ["c_xxx"], "keywords": [...]}
  }
}
```

---

## 3. 现有脚本速查

### 项目仓库内（`D:/workspace/sociology-kaoyan-app/`）

| 文件 | 行数 | 功能 |
|------|:--:|------|
| `tests/validate_data.py` | ~200 | Layer 0-A 格式校验：ID 唯一、字段完备、文件大小、跨文件引用 |
| `tests/validate_data_semantic.py` | ~250 | Layer 0-B 语义校验：题干幻觉、年份合理性、分值一致性、概念名噪声 |
| `tests/audit_taxonomy.py` | ~200 | 概念分类审计：domain 错配、重复索引、缺失分类、孤儿概念 |
| `scripts/build_taxonomy.py` | ~300 | 从 concepts.json 构建分类树（关键词匹配 + chapter 路径解析） |
| `deploy.sh` | ~145 | 部署脚本：校验 → 拷贝 web/ → git commit → push |

### D:\workspace\ 散落脚本（待归档）

| 文件 | 行数 | 功能 |
|------|:--:|------|
| `_extract_nouns.py` | ~220 | 从名词解释 TXT 提取概念（贾春增/概论新修/巴比 三个文件） |
| `_extract_yangshanhua2.py` | ~160 | 杨善华上下卷+笔记 DeepSeek 提取（分 chunk 调 API） |
| `_extract_yuanfang.py` | ~100 | 袁方方法概念提取 |
| `_extract_lushuhua.py` | ~100 | 卢淑华统计概念提取 |
| `_extract_textbooks.py` | ~170 | 多本教材批量提取 |
| `_extract_renda_gailun.py` | ~230 | 人大概论名词解释提取 |
| `_extract_methods_kaodian.py` | ~290 | 方法-真题考点提取（正则+DeepSeek 混合） |
| `_extract_methods_beisong.py` | ~100 | 方法背诵笔记提取 |
| `_extract_questionbank.py` | ~140 | 题库提取（旧版） |
| `_extract_remaining_docx.py` | ~160 | DOCX 残余文件提取 |
| `_merge_all.py` | ~60 | 多源合并去重 |
| `_merge_new_concepts.py` | ~120 | 新概念增量合并（手动 merge 辅助） |

**问题**：这些脚本散落、命名不一致、没有统一接口。任务之一就是整理它们。

---

## 4. 任务清单

### 任务 B1：deploy.sh 增强

- **难度**：⭐⭐ | **类型**：Shell 脚本 | 估计 45 分钟
- **现有文件**：`D:/workspace/sociology-kaoyan-app/deploy.sh`（145 行）
- **问题**：
  1. `concepts.json` 2.3MB 太大，单次 commit+push 容易 HTTP 408 超时
  2. 版本号手动改，容易忘
  3. 没有 pre-push 数据校验阻断（现在 validate 只警告不阻断）
- **怎么做**：
  1. **分次 commit**：先 commit concepts.json 单独 push，再 commit 剩余文件 push
  2. **自动升版本号**：扫描 `web/index.html` 里 `data/xxx.json?v=N`，如果对应的数据文件有变更，自动升 N+1 并写入 index.html
  3. **大文件检测**：如果 concepts.json > 3MB，拒绝 commit，提示手动处理
  4. 加 `--dry-run` 参数，打印将要做什么但不执行
- **输入**：`web/` 目录下的文件变更
- **输出**：git commit + push 成功/失败，版本号变更报告
- **验收**：`bash deploy.sh --dry-run` 输出变更清单不报错；`bash deploy.sh` 能成功 push 2.3MB 文件

### 任务 B2：GitHub Actions CI

- **难度**：⭐⭐ | **类型**：YAML 配置 | 估计 30 分钟
- **新建文件**：`.github/workflows/validate.yml`
- **触发条件**：push 到 main 分支、PR 到 main
- **做什么**：
  ```yaml
  name: Data Validation
  on:
    push:
      branches: [main]
      paths: ['web/data/**', 'data/**']
    pull_request:
      branches: [main]
      paths: ['web/data/**', 'data/**']
  jobs:
    validate:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - uses: actions/setup-python@v5
          with: {python-version: '3.11'}
        - run: python tests/validate_data.py
        - run: python tests/validate_data_semantic.py
  ```
- **注意**：validate 失败应该让 CI 变红但不阻断 merge（用 `continue-on-error: true`），因为数据质量问题是常驻的，不应该是 merge blocker
- **验收**：`gh workflow run validate.yml` 或 push 后看到 Actions 跑起来

### 任务 B3：validate_data.py 规则扩充

- **难度**：⭐⭐ | **类型**：Python | 估计 45 分钟
- **现有文件**：`tests/validate_data.py`（~200 行）、`tests/validate_data_semantic.py`（~250 行）
- **要加的规则**：

  | 规则 | 放哪个文件 | 检测内容 |
  |------|-----------|----------|
  | short-definition | validate_data.py | `definition` 少于 20 字符标 WARN |
  | empty-chapter | validate_data.py | `chapter` 为空字符串标 ERROR |
  | proponent-alias | validate_data_semantic.py | proponent 用了简称（"马克思"而非"卡尔·马克思"）标 WARN |
  | chapter-no-trailing-slash | validate_data.py | chapter 路径不以 `/` 结尾标 ERROR |
  | duplicate-term-same-chapter | validate_data_semantic.py | 同一个 chapter 下同名 term 出现两次标 WARN |
  | orphan-related-id | validate_data.py | `related[].id` 在 concepts.json 里找不到标 ERROR |
  | source-text-missing | validate_data.py | `source_text` 为空标 WARN |

- **怎么做**：
  1. 打开 `validate_data.py` 和 `validate_data_semantic.py`，照着现有规则的模式写
  2. 每个规则写成一个独立函数：`def check_xxx():`
  3. 在文件底部的 `if __name__ == '__main__'` 块里调用
  4. 用 `err()` / `warn()` / `ok()` 输出（这三个函数在文件顶部已定义）
- **验收**：`python tests/validate_data.py` 和 `python tests/validate_data_semantic.py` 跑过不报 Python 错误

### 任务 B4：pipeline/ 脚本归档

- **难度**：⭐⭐⭐ | **类型**：代码整理 | 估计 60 分钟
- **问题**：10 个 `_extract_*.py` + 2 个 `_merge_*.py` 散落在 `D:/workspace/`，命名不规范、路径硬编码
- **要做的事**：
  1. 在 `D:/workspace/sociology-kaoyan-app/pipeline/` 下创建目录结构：
     ```
     pipeline/
     ├── README.md            ← 管线总览（你写）
     ├── extract/             ← 提取脚本
     │   ├── extract_nouns.py        (从 _extract_nouns.py 改)
     │   ├── extract_textbooks.py    (从 _extract_textbooks.py 改)
     │   ├── extract_renda_gailun.py (从 _extract_renda_gailun.py 改)
     │   ├── extract_yuanfang.py     (从 _extract_yuanfang.py 改)
     │   ├── extract_lushuhua.py     (从 _extract_lushuhua.py 改)
     │   ├── extract_methods_kaodian.py
     │   ├── extract_methods_beisong.py
     │   └── extract_questionbank.py
     ├── merge/               ← 合并脚本
     │   ├── merge_all.py
     │   └── merge_new.py
     ├── deepseek/            ← DeepSeek API 脚本（需 key，Claude 专用）
     │   └── extract_yangshanhua.py  (从 _extract_yangshanhua2.py 改)
     └── utils/               ← 共用工具
         └── concept_utils.py ← 抽取共用函数：ID 生成、去重、JSON 读写、UTF-8 包装
   ```
  2. 每个脚本的改造：
     - 把硬编码的绝对路径改成 `pathlib.Path(__file__).parent` 相对路径（或通过命令行参数传入）
     - 抽取共用的 `load_json()` / `save_json()` / `slugify()` / `dedupe()` 到 `pipeline/utils/concept_utils.py`
     - 加 `if __name__ == '__main__'` 和 argparse
  3. **不要改逻辑，只改组织方式**

- **不碰的文件**：`_extract_yangshanhua2.py` — 它有 DeepSeek API 调用逻辑，放 `deepseek/` 目录但不需要重构（我来处理）
- **验收**：归档后的每个脚本能独立 `python pipeline/extract/extract_xxx.py --help` 输出参数说明

### 任务 B5：concept_utils.py 共用工具库

- **难度**：⭐⭐ | **类型**：Python 库 | 估计 30 分钟
- **新建文件**：`pipeline/utils/concept_utils.py`
- **要把这些函数从散落的脚本里抽取出来**：
  ```python
  def load_json(path: str) -> list|dict:
      """读取 JSON 文件，UTF-8，出错抛异常"""

  def save_json(data, path: str, indent: int = 2):
      """写入 JSON，UTF-8，ensure_ascii=False"""

  def slugify(term: str) -> str:
      """从中文概念名生成 ASCII ID（取 MD5 前 8 位）"""

  def dedupe_by_id(concepts: list, existing_ids: set) -> list:
      """按 ID 去重，返回新增的"""

  def dedupe_by_term_chapter(concepts: list, existing: list) -> list:
      """按 term+chapter 组合去重，返回新增的"""

  def backup_concepts(data_path: str):
      """备份 concepts.json 到同目录带时间戳"""

  def validate_concept(c: dict, index: int) -> list[str]:
      """校验单条概念格式，返回错误消息列表"""
  ```
- **做法**：打开 `_extract_nouns.py`、`_merge_all.py`、`validate_data.py`，找到这些函数的实现，统一写到 `concept_utils.py`，删掉各脚本里的重复实现改为 `from pipeline.utils.concept_utils import xxx`
- **验收**：`python -c "from pipeline.utils.concept_utils import load_json, slugify; print('OK')"` 不报错

### 任务 B6：build_taxonomy.py SOURCES 配置化

- **难度**：⭐⭐ | **类型**：重构 | 估计 30 分钟
- **现有文件**：`scripts/build_taxonomy.py`（~300 行）
- **问题**：SOURCES 是硬编码的列表，新增教材或笔记来源时要改脚本代码
- **怎么做**：
  1. 把 SOURCES 从硬编码列表改成读一个 JSON 配置文件：`pipeline/taxonomy_sources.json`
  2. 配置文件格式：
     ```json
     {
       "sources": [
         {
           "name": "侯钧生-西方社会学理论教程",
           "type": "textbook",
           "chapter_prefix": "理论",
           "keywords": {"孔德": ["孔德", "社会静力学", ...], ...}
         }
       ]
     }
     ```
  3. `build_taxonomy.py` 变成：读配置 → 遍历 sources → 匹配 concepts → 构建 taxonomy
- **验收**：加一个新的 source 到配置文件 → 重新跑 `build_taxonomy.py` → taxonomy 包含新 source 的概念

---

## 5. 本地开发环境

### Python 环境

```powershell
# 确认 Python 版本（3.8+）
python --version

# 依赖（目前几乎零依赖，只有标准库）
# 未来可能需要：pip install paddleocr opencv-python（OCR，Claude 装）
```

### 运行脚本

```bash
# 在 Git Bash 里（不是 PowerShell！PowerShell 中文输出 GBK 乱码）
cd D:/workspace/sociology-kaoyan-app

# 数据校验
python tests/validate_data.py
python tests/validate_data_semantic.py
python tests/audit_taxonomy.py

# 构建分类
python scripts/build_taxonomy.py
```

---

## 6. 铁律（别他妈犯）

| # | 铁律 | 原因 |
|---|------|------|
| 1 | **改 concepts.json 前必须备份** | 2.3MB 的 JSON，手改坏一行 = 整个文件报废 |
| 2 | **所有 Python 脚本用 UTF-8** | Windows 默认 GBK，中文输出乱码是日常。每个 `.py` 文件头加 `# -*- coding: utf-8 -*-`，输出用 `sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')` |
| 3 | **脚本先干跑（dry-run）** | 新脚本第一次运行先打印要做什么但不执行。直接改数据 = 哭都来不及 |
| 4 | **DeepSeek API 调用加增量缓存** | 每条 chunk 调用完立即存盘，crash 了不用重跑。这个在 `_extract_yangshanhua2.py` 里有范例 |
| 5 | **路径用正斜杠** | Windows 反斜杠在 Git Bash 和 Python 里行为不一致。统一 `/` |
| 6 | **print 不加 emoji** | emoji → GBK 编码失败 → `UnicodeEncodeError` → 脚本在最后一步崩溃 |
| 7 | **concepts.json 的 id 不可变** | 改了一个 ID → taxonomy 索引失效 → 分类浏览全崩 |
| 8 | **validate 失败不应该是 CI 阻断** | 数据质量问题是常驻的，不是 regression。让 CI 报告但不 fail |
| 9 | **新字段加在末尾** | concepts.json 每个对象的字段顺序不要改，免得 git diff 爆炸 |
| 10 | **`D:/workspace/` 下面的临时脚本标注日期** | 超过两周的可以删，别让 workspace 变成垃圾场 |

---

## 7. 踩过的后端坑

| 坑 | 教训 |
|----|------|
| **PowerShell 中文全是乱码** | python print 中文 → GBK 编码失败。用 Git Bash 跑 Python 脚本，或者在 `.py` 里强制 UTF-8 输出 |
| **`.format()` 里 JSON 示例的大括号被吃掉** | `{"term": ...}` → 写成 `{{"term": ...}}`，否则 `.format()` 当成占位符 |
| **emoji 炸 GBK** | `print("✅")` → `UnicodeEncodeError`。所有 print 去掉 emoji |
| **git SSL 连环坑** | schannel 失败 → openssl 也失败 → `sslVerify=false` 才过。代理对 git HTTPS 不稳定 |
| **三层转义地狱** | Bash heredoc → Python string → regex escape，`\w` 和反引号互相打架。复杂脚本直接写 `.py` 文件，不用 heredoc |
| **deploy.sh HTTP 408** | concepts.json 2.5MB 太大，单次 push 超时。分次 commit |
| **`_build_concepts.py` 和手动合并打架** | build 脚本有 SOURCES 硬编码，手动 merge 绕过它。应该统一入口 |
| **source_text 字段是后补的** | 1396 条老概念没有 source_text，追溯不到来源 |
| **提取脚本散落在根目录** | 6 个 `_extract_*.py` + 3 个合并脚本，无归档、无文档 |
| **API 调用没有缓存** | DeepSeek 101 chunks 跑了两次全量因为 crash。增量缓存 = 每条完立即存盘 |

---

## 8. 如果 Trae 要接手

1. **先读完这份文档**，别跳
2. **从任务 B1 或 B2 开始**（deploy.sh 增强 / GitHub Actions），这两个最独立、最容易验收
3. **别直接改 concepts.json** — 那个我来
4. **写 Python 脚本用 Git Bash 测试**，别用 PowerShell
5. **每个任务做完 commit 一次**，commit message 英文：`pipeline: add xxx validation rule`
6. **不确定的事问 Claude/用户**，别猜。数据管线猜错一个字段 = 2399 条全脏
