# -*- coding: utf-8 -*-
"""概念合并方案 Step4：待审 1024 条预分类三档（减负，用户只审模糊带+删除候选）

分档:
  KEEP   - 来源笔记/lcwiki 或 真题高频 → 自动保留候选
  BORDER - 定义完整但来源不明/其他 → 模糊带（用户逐条审）
  DELETE - 碎片/残句/教材裸文本无信号 → 删除候选（仍需用户过目）

输出: D:/workspace/_report_review_1024.json/.md
"""
import os, sys, io, re, json, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from pipeline.utils.concept_utils import classify_fragment

CLASSIFY = "D:/workspace/_report_classify.json"
CONCEPTS = "D:/workspace/sociology-kaoyan-app/web/data/concepts.json"
OUT_JSON = "D:/workspace/_report_review_1024.json"
OUT_MD = "D:/workspace/_report_review_1024.md"

TRUSTED = re.compile(r"笔记|名词解释|背诵|考点|lcwiki|风笑天|南大|华中师|杨善华_笔记|论文映射|真题")
ACCEPT_RULES = {"泛化词", "纯虚词", "含标点", "含笔记符号", "教学前缀", "教学后缀",
                "句子碎片", "导航文本", "编号前缀", "开头残句"}

def main():
    rows = json.load(open(CLASSIFY, encoding='utf-8'))
    cs = json.load(open(CONCEPTS, encoding='utf-8'))
    by_id = {c['id']: c for c in cs}

    review = [r for r in rows if r['classification'] == 'REVIEW']
    buckets = {"KEEP": [], "KEEP_EMPTY": [], "BORDER": [], "DELETE": []}

    for r in review:
        c = by_id.get(r['id']) or r
        term = r['term']
        source = r['source_text']
        freq = r['exam_frequency']
        defn = c.get('definition') or ''
        deflen = len(defn)
        frag = classify_fragment(term)

        # 明确碎片：term 含 OCR残渣/序号/标点 且定义短
        hard_frag = (frag == "编号前缀") or re.search(r'[（(）)\d][）)]|^[①②③④⑤⑥⑦⑧⑨⑩]', term) or (frag in ("含标点","含笔记符号","OCR残渣") and deflen < 15)
        if TRUSTED.search(source) or freq == 'high':
            buckets["KEEP"].append((r, defn, "笔记源/真题高频"))
        elif deflen >= 30:
            buckets["KEEP_EMPTY"].append((r, defn, "定义完整(≥30字,疑似早期优质提取)"))
        elif hard_frag:
            buckets["DELETE"].append((r, defn, f"明确碎片·{frag}"))
        elif deflen < 10 and frag:
            buckets["DELETE"].append((r, defn, f"定义<10字+碎片"))
        else:
            buckets["BORDER"].append((r, defn, "模糊带(含教材短定义·用户审)"))

    out = {}
    for k, items in buckets.items():
        out[k] = [{"id": it[0]['id'], "term": it[0]['term'], "chapter": it[0]['chapter'],
                   "source_text": it[0]['source_text'], "exam_frequency": it[0]['exam_frequency'],
                   "definition": it[1][:120], "def_len": len(it[1]), "mark": it[2]}
                  for it in items]
    json.dump(out, open(OUT_JSON, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    L = [f"# Step4 待审区预分类（{len(review)} 条）", ""]
    L.append(f"- **KEEP(笔记源/真题高频·自动保留)**: {len(buckets['KEEP'])}")
    L.append(f"- **KEEP_EMPTY(空源+定义≥30·建议保留·用户抽检)**: {len(buckets['KEEP_EMPTY'])}")
    L.append(f"- **BORDER(模糊带·用户逐条审)**: {len(buckets['BORDER'])}")
    L.append(f"- **DELETE(删除候选·用户过目)**: {len(buckets['DELETE'])}")
    for k in ("DELETE", "BORDER", "KEEP_EMPTY", "KEEP"):
        L.append(f"\n## {k} ({len(buckets[k])})")
        for r, defn, mark in buckets[k][:80]:
            L.append(f"- {r['term']} | {mark} | src={r['source_text'][:16] or '空'} | def={len(defn)}字 | freq={r['exam_frequency']}")
        if len(buckets[k]) > 80:
            L.append(f"  ... 共 {len(buckets[k])} 条")
    with open(OUT_MD, 'w', encoding='utf-8') as f:
        f.write('\n'.join(L))

    print(f"待审总数: {len(review)}")
    for k in ("KEEP", "KEEP_EMPTY", "BORDER", "DELETE"):
        print(f"  {k}: {len(buckets[k])}")
    print(f"→ {OUT_JSON}\n→ {OUT_MD}")

if __name__ == '__main__':
    main()
