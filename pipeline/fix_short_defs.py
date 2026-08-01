# -*- coding: utf-8 -*-
"""Step 6 简化版：从源文件为短定义概念搜索更长定义替换

仅处理 definition < 25 字的概念。复用 find_definition 逻辑。
输出: 替换统计 + 写回 concepts.json
用法: python pipeline/fix_short_defs.py [--dry-run]
"""
import os, sys, io, re, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from pipeline.utils.concept_utils import find_definition

CONCEPTS = "D:/workspace/sociology-kaoyan-app/web/data/concepts.json"
SOURCE_FILES = {
    "马工程考试大纲": "D:/workspace/sociology-kaoyan/__extracted__/笔记/马工程《社会学概论》（第2版）考试大纲.txt",
    "人大_概论名词解释": "D:/workspace/sociology-kaoyan/__extracted__/方法/人大_概论名词解释.txt",
    "人大_巴比方法名词解释": "D:/workspace/sociology-kaoyan/__extracted__/方法/人大_巴比名词解释.txt",
    "人大_贾春增名词解释": "D:/workspace/sociology-kaoyan/__extracted__/方法/人大_贾春增名词解释.txt",
    "华中师_风笑天方法笔记": "D:/workspace/_exam_texts/华中师_风笑天社会学方法笔记.txt",
    "华中师_西方理论简约版结构图": "D:/workspace/_exam_texts/华中师_西方社会学理论简约版结构图.txt",
    "南大_方法真题考点": "D:/workspace/_nanda_docx/社会研究方法_方法-真题考点.txt",
    "南大_方法名词解释综合": "D:/workspace/_nanda_docx/方法_社会研究方法--名词解释综合.txt",
    "杨善华_下卷": "D:/workspace/sociology-kaoyan/__extracted__/教材/杨善华_西方社会学理论下卷.txt",
    "杨善华_笔记": "D:/workspace/sociology-kaoyan/__extracted__/笔记/杨善华_笔记和考研真题详解.txt",
    "概论新修_名词解释": "D:/workspace/sociology-kaoyan/__extracted__/概论新修_名词解释.txt",
}
QUANKAODIAN_DIR = "D:/workspace/_nanda_docx"

_cache = {}

def get_text(path):
    if path not in _cache:
        _cache[path] = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
    return _cache[path]

def find_long_definition(term, sources):
    """在多个源中找 ≥30 字定义（复用 concept_utils.find_definition 修复版）"""
    best = None
    for src in sources:
        if src.startswith("南大全考点"):
            path = os.path.join(QUANKAODIAN_DIR, src[5:] + ".txt")
        else:
            path = SOURCE_FILES.get(src, "")
        if not path:
            continue
        text = get_text(path)
        if not text:
            continue
        d = find_definition(text, term)
        if d and len(d) >= 30 and (not best or len(d) > len(best)):
            best = d
    return best

def main():
    dry_run = "--dry-run" in sys.argv
    concepts = json.load(open(CONCEPTS, encoding="utf-8"))
    short = [c for c in concepts if len(c.get("definition", "")) < 25]
    print(f"短定义(<25字): {len(short)} 条")

    fixed, not_found = [], []
    for c in short:
        term = c.get("term", "")
        # 收集搜索源：source_text 对应的源 + 正典来源兜底
        src = c.get("source_text", "") or ""
        candidates = [src] if src else []
        # 补充常见源
        candidates += ["人大_概论名词解释", "南大_方法名词解释综合", "华中师_风笑天方法笔记"]
        new_def = find_long_definition(term, candidates)
        if new_def:
            fixed.append((term, c["definition"][:20], new_def[:40]))
            if not dry_run:
                c["definition"] = new_def
        else:
            not_found.append(term)

    print(f"替换成功: {len(fixed)}")
    if fixed:
        print("替换示例:")
        for t, old, new in fixed[:20]:
            print(f"  {t}:\n    旧: {old}...\n    新: {new}...")
    print(f"未找到长定义(保留): {len(not_found)}")
    print("  如:", not_found[:25])

    if dry_run:
        return
    with open(CONCEPTS, "w", encoding="utf-8") as f:
        json.dump(concepts, f, ensure_ascii=False, indent=1)
    print(f"\n已写回 {CONCEPTS}")

if __name__ == "__main__":
    main()
