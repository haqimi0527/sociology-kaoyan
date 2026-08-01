# -*- coding: utf-8 -*-
"""概念合并方案 Step7：执行执行计划

动作:
  DELETE     - 删除概念
  MERGE_INTO - 并入 keeper（定义精华进 definition_long，term 进 related，tags 聚合），删除副本
  RELOCATE   - 改 chapter 归位

原则: 删条不重建 ID（taxonomy 依赖）；每步前备份。
"""
import os, sys, io, re, json, shutil, time, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

CONCEPTS = "D:/workspace/sociology-kaoyan-app/web/data/concepts.json"
W = "D:/workspace"
PLAN = f"{W}/_report_execution_plan.json"

def add_backup(path, tag):
    ts = time.strftime('%Y%m%d_%H%M%S')
    dest = f"{path}_backup_{tag}_{ts}"
    shutil.copy2(path, dest)
    print(f"  [备份] → {dest}")
    return dest

def merge_into_keeper(keeper, victim, termmap):
    """把 victim 的定义精华/别名/tags 聚合进 keeper"""
    vdef = victim.get('definition') or ''
    kdef = keeper.get('definition') or ''
    vlong = victim.get('definition_long') or ''
    # 定义精华：victim 定义更长 或 与 keeper 不同 → 存 definition_long
    long_parts = []
    if vlong and vlong != kdef:
        long_parts.append(vlong)
    if vdef and len(vdef) > len(kdef):
        long_parts.append(vdef)
    elif vdef and vdef != kdef:
        long_parts.append(vdef)
    if long_parts:
        klong = keeper.get('definition_long') or ''
        merged_long = '\n'.join([klong] + long_parts).strip()
        if len(merged_long) > len(kdef):
            keeper['definition_long'] = merged_long
    # 别名进 related（对象格式 [{"id","relation","term"}]）
    rel = [r for r in (keeper.get('related') or []) if isinstance(r, dict)]
    rel_terms = {r.get('term') for r in rel}
    if victim['term'] not in rel_terms and victim['term'] != keeper['term']:
        rel.append({"id": victim.get('id'), "relation": "alias", "term": victim['term']})
        rel_terms.add(victim['term'])
    for r in (victim.get('related') or []):
        if isinstance(r, dict) and r.get('term') and r['term'] not in rel_terms:
            rel.append(r)
            rel_terms.add(r['term'])
    keeper['related'] = rel
    # tags 聚合
    ktags = set(keeper.get('tags') or [])
    ktags.update(victim.get('tags') or [])
    keeper['tags'] = sorted(ktags)
    # exam_frequency 取高
    vf, kf = victim.get('exam_frequency'), keeper.get('exam_frequency')
    order = {'high': 3, 'medium': 2, 'low': 1}
    if vf and order.get(vf, 0) > order.get(kf, 0):
        keeper['exam_frequency'] = vf
    # source 空则填
    if not keeper.get('source_text') and victim.get('source_text'):
        keeper['source_text'] = victim['source_text']

def main():
    plan_data = json.load(open(PLAN, encoding='utf-8'))
    plan = plan_data['plan']
    cs = json.load(open(CONCEPTS, encoding='utf-8'))
    cmap = {c['id']: c for c in cs}

    # 解析链式合并：merged→keeper→keeper...，路径压缩到最终根
    merge_map = {pid: p['target'] for pid, p in plan.items() if p['action'] == 'MERGE_INTO'}
    def find_root(pid, seen=None):
        seen = seen if seen is not None else set()
        nxt = merge_map.get(pid)
        if nxt is None or nxt in seen:
            return pid  # 无父/成环 → 自己为根
        seen.add(pid)
        return find_root(nxt, seen)
    for pid in list(merge_map.keys()):
        merge_map[pid] = find_root(pid)

    # 校验：根不能是被删/被并的；根必须存在
    bad = []
    root_set = set(merge_map.values())
    for pid, p in plan.items():
        if p['action'] == 'MERGE_INTO':
            root = merge_map[pid]
            if root in plan and plan[root]['action'] in ('DELETE', 'MERGE_INTO'):
                bad.append(f"{cmap[pid]['term']}→根 {cmap[root]['term']} 自身是{plan[root]['action']}")
            if root not in cmap:
                bad.append(f"{cmap[pid]['term']}→根 {root} 不存在")
    if bad:
        print("[错误] 计划冲突：")
        for b in bad[:20]:
            print(f"  {b}")
        sys.exit(1)

    add_backup(CONCEPTS, "pre_merge")

    # 第一遍：决定去留 + RELOCATE + 收集 merge（用解析后的根）
    keep = []
    merge_groups = collections.defaultdict(list)  # root_id -> [victim]
    stats = collections.Counter()
    for c in cs:
        pid = c['id']
        p = plan.get(pid)
        if not p:
            keep.append(c)
            stats['KEEP'] += 1
            continue
        if p['action'] == 'DELETE':
            stats['DELETE'] += 1
            continue
        if p['action'] == 'RELOCATE':
            c['chapter'] = p['target']
            keep.append(c)
            stats['RELOCATE'] += 1
            continue
        if p['action'] == 'MERGE_INTO':
            merge_groups[merge_map[pid]].append(c)
            stats['MERGE'] += 1
            continue
        keep.append(c)
        stats['KEEP'] += 1

    # 第二遍：聚合 merged 到 keeper
    keep_map = {c['id']: c for c in keep}
    merged_detail = []
    for kid, victims in merge_groups.items():
        keeper = keep_map.get(kid)
        if not keeper:
            print(f"[警告] keeper {kid} 不在保留集，{len(victims)} 个变体悬空")
            for v in victims:
                keep.append(v)
                stats['MERGE_UNRESOLVED'] += 1
            continue
        for v in victims:
            merge_into_keeper(keeper, v, keep_map)
            merged_detail.append(f"{v['term']} → {keeper['term']}")

    with open(CONCEPTS, 'w', encoding='utf-8') as f:
        json.dump(keep, f, ensure_ascii=False, indent=1)

    print("执行结果:")
    for k in ("KEEP", "DELETE", "RELOCATE", "MERGE", "MERGE_UNRESOLVED"):
        print(f"  {k}: {stats.get(k, 0)}")
    print(f"保留总数: {len(keep)}")
    print(f"  {CONCEPTS}")
    if merged_detail:
        print("\n合并明细(前30):")
        for d in merged_detail[:30]:
            print(f"  {d}")

if __name__ == '__main__':
    main()
