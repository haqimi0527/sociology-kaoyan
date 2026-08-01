# -*- coding: utf-8 -*-
"""补提取缺失正典概念

1. 计算缺失概念：高价值源(S0/A)概念名 - 现有保留
2. 噪声过滤：残句/列表项/描述短语剔除
3. 规整源定义定位：概念名 → 冒号后内容 / 后续段落
4. 输出 D:/workspace/_extracted_missing.json

用法: python pipeline/extract_missing_concepts.py [--dry-run]
"""
import os, sys, io, re, json, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from pipeline.utils.concept_utils import is_noise, find_definition, clean_term

CANON = "D:/workspace/_canonical_names.json"
FINAL = "D:/workspace/_restructure_final.json"
OUT = "D:/workspace/_extracted_missing.json"

# 源文件路径表
SOURCE_FILES = {
    "马工程考试大纲": "D:/workspace/sociology-kaoyan/__extracted__/笔记/马工程《社会学概论》（第2版）考试大纲.txt",
    "人大_概论名词解释": "D:/workspace/sociology-kaoyan/__extracted__/方法/人大_概论名词解释.txt",
    "人大_巴比方法名词解释": "D:/workspace/sociology-kaoyan/__extracted__/方法/人大_巴比名词解释.txt",
    "人大_贾春增名词解释": "D:/workspace/sociology-kaoyan/__extracted__/方法/人大_贾春增名词解释.txt",
    "华中师_风笑天方法笔记": "D:/workspace/_exam_texts/华中师_风笑天社会学方法笔记.txt",
    "华中师_西方理论简约版结构图": "D:/workspace/_exam_texts/华中师_西方社会学理论简约版结构图.txt",
    "南大_方法真题考点": "D:/workspace/_nanda_docx/社会研究方法_方法-真题考点.txt",
    "南大_方法名词解释综合": "D:/workspace/_nanda_docx/方法_社会研究方法--名词解释综合.txt",
}
QUANKAODIAN_DIR = "D:/workspace/_nanda_docx"

def norm_term(t):
    return clean_term(t)

def main():
    dry_run = "--dry-run" in sys.argv
    canon = json.load(open(CANON, encoding="utf-8"))
    final = json.load(open(FINAL, encoding="utf-8"))
    keep_terms = {d["term"] for d in final if d["classification"] in ("CANON", "SYNONYM", "KEEP")}

    # 缺失概念
    missing = [r for r in canon if r["priority"] in ("S0", "A") and r["term"] not in keep_terms]
    clean = [r for r in missing if not is_noise(r["term"])]
    print(f"缺失概念: {len(missing)} → 过滤噪声后干净: {len(clean)}")
    noise_cnt = len(missing) - len(clean)
    print(f"噪声剔除: {noise_cnt}")
    if noise_cnt:
        noise_terms = [r["term"] for r in missing if is_noise(r["term"])]
        print("噪声示例:", noise_terms[:25])

    # 定义定位
    found, not_found = [], []
    for r in clean:
        term = norm_term(r["term"])
        # 搜索源：马工程大纲概念优先从人大概论名词解释找定义
        search_sources = list(r["sources"])
        if "马工程考试大纲" in search_sources and "人大_概论名词解释" not in search_sources:
            search_sources.insert(0, "人大_概论名词解释")
        # 找定义源
        definition = None
        src_used = None
        for src in search_sources:
            if src.startswith("南大全考点"):
                path = os.path.join(QUANKAODIAN_DIR, src[5:] + ".txt")
            else:
                path = SOURCE_FILES.get(src)
            if not path or not os.path.exists(path):
                continue
            text = open(path, encoding="utf-8").read()
            definition = find_definition(text, term)
            # 定义质量门槛：≥25 字才采用
            if definition and len(definition) >= 25:
                src_used = src
                break
            else:
                definition = None
        rec = {"term": term, "priority": r["priority"], "sources": r["sources"]}
        if definition:
            rec["definition"] = definition
            rec["source_text"] = src_used
            found.append(rec)
        else:
            not_found.append(rec)

    print(f"\n定义可提取: {len(found)} / {len(clean)}")
    print(f"定义未找到(需DeepSeek或跳过): {len(not_found)}")
    if not_found:
        print("未找到示例:", [r["term"] for r in not_found[:30]])

    # 抽检
    if found:
        import random
        random.seed(1)
        print("\n抽检已提取定义 20 条:")
        for r in random.sample(found, min(20, len(found))):
            print(f"  {r['term']} [{r['source_text']}] | {r['definition'][:40]}")

    if dry_run:
        return
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(found, f, ensure_ascii=False, indent=1)
    print(f"\n→ {OUT} ({len(found)} 条)")

if __name__ == "__main__":
    main()
