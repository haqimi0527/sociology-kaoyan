# -*- coding: utf-8 -*-
"""四分类匹配：现有 concepts.json 每条 vs 正典清单

分类:
  CANON   - term 精确/归一化 ∈ 正典清单 → 保留
  SYNONYM - term 与正典概念高相似（difflib ≥ 0.85）→ 合并候选
  REVIEW  - ∉正典 但来源可信（笔记/名词解释/lcwiki）或 exam_frequency=high → 人工审核
  DELETE  - ∉正典 且来源=教材裸文本/空/未知 且无高频信号 → 删除候选

输出: D:/workspace/_restructure_classification.json
  [{"id","term","source_text","exam_frequency","classification","matched_canon","reason"}]
"""
import os, sys, io, re, json, difflib, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

CONCEPTS = "D:/workspace/sociology-kaoyan-app/web/data/concepts.json"
CANON = "D:/workspace/_canonical_names.json"
OUT = "D:/workspace/_restructure_classification.json"

TRUSTED_SOURCE = r"笔记|名词解释|lcwiki|背诵|考点|人大_|华中师|南大|杨善华_笔记|论文映射"
TEXTBOOK_SOURCE = r"杨善华_下卷|教材|裸文本"

def norm(t):
    """归一化：去括号内容、去空格、去尾部符号"""
    t = str(t or "")
    t = t.replace('（', '(').replace('）', ')')
    t = re.sub(r'\(.*?\)', '', t)
    t = re.sub(r'[　 ]+', '', t)
    t = t.strip(' \t\n*#△^←→√※.·、—-—')
    return t

def load_concepts():
    return json.load(open(CONCEPTS, encoding='utf-8'))

def load_canon():
    return json.load(open(CANON, encoding='utf-8'))

def is_garbage_entry(term, definition, def_len):
    """明确垃圾特征：term 是垃圾词/编号/残句，或定义极短且残句"""
    GARBAGE_TERM = {"重要概念","不足之处","基本主张","基本假设","基本要点","研究目的","研究重点",
        "概述","结论","总结","复习笔记","真题","参考答案","答案","引言","小节","本章","第一节",
        "第二节","具体内容","主要内容","基本情况","相关概念","学习要点","复习重点","思考题"}
    if term in GARBAGE_TERM:
        return True
    if re.search(r'^\d', term) or re.match(r'^[①②③④⑤⑥⑦⑧⑨⑩]', term):
        return True
    if def_len < 10:
        return True
    # term 含 OCR 残渣（3·．纪律、L维模功能、3：来德）
    if re.search(r'\d\s*[·．.、]', term) or re.match(r'^[A-Z]\w{0,2}[维模功]', term):
        return True
    # 定义是残句（介词/连词开头且很短）
    if def_len < 18 and re.match(r'^(于|在|从|把|被|以|对|由|与|而|即|其|它|这|那|所|但|或)', definition):
        return True
    return False

def main():
    concepts = load_concepts()
    canon = load_canon()
    canon_terms = [r["term"] for r in canon]
    canon_norm_set = {norm(t) for t in canon_terms}
    canon_set = set(canon_terms)

    # 3-gram 倒排索引（加速模糊匹配）
    gram_idx = collections.defaultdict(list)
    for i, t in enumerate(canon_terms):
        tn = norm(t)
        if len(tn) >= 3:
            for j in range(len(tn) - 2):
                gram_idx[tn[j:j+3]].append(i)
    # 去重 gram 候选
    gram_idx = {k: list(set(v)) for k, v in gram_idx.items()}

    def fuzzy_match(tn):
        """返回 (最佳正典term, 相似度) 或 (None, 0)"""
        if len(tn) < 3:
            return None, 0.0
        cand = set()
        for j in range(len(tn) - 2):
            cand.update(gram_idx.get(tn[j:j+3], []))
        best, best_t = 0.0, None
        for i in cand:
            r = difflib.SequenceMatcher(None, tn, norm(canon_terms[i])).ratio()
            if r > best:
                best, best_t = r, canon_terms[i]
        return best_t, best

    result = []
    stats = collections.Counter()
    for c in concepts:
        term = c.get("term", "")
        tn = norm(term)
        source = c.get("source_text", "") or ""
        freq = c.get("exam_frequency", "") or ""
        definition = c.get("definition", "") or ""
        def_len = len(definition)
        # 定义有效：长度≥30（不要求句号结尾，很多定义提取时句号丢失）
        good_def = def_len >= 30

        # 1) 精确匹配
        if term in canon_set or tn in canon_norm_set:
            cls = "CANON"
            matched = term if term in canon_set else (tn if tn in canon_norm_set else "")
            reason = f"正典匹配: {matched}"
        else:
            # 2) 模糊匹配
            matched, score = fuzzy_match(tn)
            if matched and score >= 0.80:
                cls = "SYNONYM"
                reason = f"同义变体: {matched} (相似度 {score:.2f})"
            else:
                # 3) REVIEW vs DELETE：只删明确垃圾，其余一律 REVIEW 兜底
                trusted = bool(re.search(TRUSTED_SOURCE, source))
                high_freq = (freq == "high")
                garbage = is_garbage_entry(term, definition, def_len)
                if trusted or high_freq or good_def or (not garbage):
                    cls = "REVIEW"
                    flags = []
                    if trusted: flags.append("来源可信")
                    if high_freq: flags.append("高频")
                    if good_def: flags.append(f"定义有效({def_len}字)")
                    if garbage: flags.append("短定义但term合理")
                    reason = ";".join(flags) + f";未匹配正典"
                else:
                    cls = "DELETE"
                    reason = f"明确垃圾(定义{def_len}字)"

        stats[cls] += 1
        result.append({
            "id": c.get("id", ""),
            "term": term,
            "chapter": c.get("chapter", ""),
            "source_text": source,
            "exam_frequency": freq,
            "proponent": c.get("proponent", ""),
            "definition_len": def_len,
            "classification": cls,
            "matched_canon": matched if cls in ("CANON", "SYNONYM") else "",
            "reason": reason,
        })

    # 输出
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)

    print(f"现有概念: {len(concepts)} 条")
    print(f"正典清单: {len(canon_terms)} 概念名")
    print("四分类统计:")
    for k in ("CANON", "SYNONYM", "REVIEW", "DELETE"):
        print(f"  {k}: {stats[k]} ({stats[k]/len(concepts)*100:.1f}%)")
    print(f"→ {OUT}")

if __name__ == "__main__":
    main()
