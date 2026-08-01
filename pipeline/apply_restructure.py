# -*- coding: utf-8 -*-
"""执行重构落地：删 DELETE + 新增补提取

决策记录：
- SYNONYM 203 条全保留（定义完整，合并有误配风险如"非理性主义~理性主义"，宁保留独立条目）
- 最终 = 现有保留(2366) + 新增补提取(91) = 2457 条

用法: python pipeline/apply_restructure.py [--dry-run]
"""
import os, sys, io, re, json, hashlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

CONCEPTS = "D:/workspace/sociology-kaoyan-app/web/data/concepts.json"
FINAL = "D:/workspace/_restructure_final.json"
NEW = "D:/workspace/_extracted_missing_clean.json"

def slugify(term):
    """ID 生成：md5(term) 前 8 位（复用 _build_concepts.py 逻辑）"""
    return "c_" + hashlib.md5(term.encode("utf-8")).hexdigest()[:8]

def infer_chapter(source, term):
    """根据来源推断 chapter 分类路径"""
    s = source or ""
    if any(k in s for k in ("方法", "风笑天", "巴比", "真题考点", "名词解释综合", "背诵笔记")):
        return "社会学研究方法/方法补充/"
    if any(k in s for k in ("全考点", "结构图", "理论", "侯钧生", "贾春增", "杨善华")):
        return "理论/补充/"
    return "概论/补充/"

def main():
    dry_run = "--dry-run" in sys.argv
    skip_delete = "--skip-delete" in sys.argv
    new_path = None
    for a in sys.argv:
        if a.startswith("--new="):
            new_path = a.split("=", 1)[1]

    concepts = json.load(open(CONCEPTS, encoding="utf-8"))
    before = len(concepts)

    # 1) 待删除 id（--skip-delete 时跳过删除，只做新增）
    kept = concepts
    removed = 0
    if not skip_delete:
        final = json.load(open(FINAL, encoding="utf-8"))
        del_ids = {d["id"] for d in final if d["classification"] == "DELETE"}
        kept = [c for c in concepts if c.get("id") not in del_ids]
        removed = before - len(kept)
        print(f"删除 DELETE: {removed} 条 (预期 {len(del_ids)})")
    else:
        print("[--skip-delete] 跳过删除，仅新增")

    # 2) 新增补提取（从 new_path 或默认 _extracted_missing_clean.json）
    new_items = json.load(open(new_path if new_path else NEW, encoding="utf-8"))
    existing_ids = {c.get("id") for c in kept}
    existing_terms = {c.get("term") for c in kept}
    added = 0
    skipped = 0
    for item in new_items:
        term = item["term"]
        # 去重：term 已存在则跳过
        if term in existing_terms:
            print(f"  [SKIP] term 已存在: {term}")
            skipped += 1
            continue
        base_id = slugify(term)
        nid = base_id
        i = 1
        while nid in existing_ids:
            nid = f"{base_id}_{i}"
            i += 1
        existing_ids.add(nid)
        existing_terms.add(term)
        kept.append({
            "id": nid,
            "term": term,
            "definition": item["definition"],
            "proponent": "",
            "chapter": item.get("chapter") or infer_chapter(item.get("source_text", ""), term),
            "core_points": [],
            "related": [],
            "source_text": item.get("source_text", ""),
            "exam_frequency": "medium",
            "tags": [],
            "textbook_ref": "",
            "school": "",
        })
        added += 1

    print(f"新增补提取: {added} 条 (跳过已存在 {skipped})")
    print(f"最终条数: {before} → {len(kept)}")

    if dry_run:
        print("[dry-run] 不写文件")
        return

    with open(CONCEPTS, "w", encoding="utf-8") as f:
        json.dump(kept, f, ensure_ascii=False, indent=1)
    print(f"→ {CONCEPTS}")

if __name__ == "__main__":
    main()
