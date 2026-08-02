# -*- coding: utf-8 -*-
"""从 build_taxonomy.THEORY_TAXONOMY 生成完整 scholar_to_era_school 映射表

背景：chapter_mappings.json 的 scholar_to_era_school 只有 18 条（缺 34 个正典学者），
导致 normalize_chapters 无法给 807 条缺学派层 chapter 补全。

用法（Git Bash）:
  python scripts/build_scholar_map.py --dry-run   # 只打印，不回写
  python scripts/build_scholar_map.py --apply     # 回写 chapter_mappings.json
"""
import os, sys, io, json, re

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from scripts.build_taxonomy import THEORY_TAXONOMY  # 权威结构

MAPPINGS = os.path.join(BASE, 'pipeline', 'config', 'chapter_mappings.json')
ALIASES = os.path.join(BASE, 'pipeline', 'config', 'translation_aliases.json')


def era_short(full):
    """'古典时期 (1830s-1920s)' → '古典时期'"""
    return re.sub(r'\s*\(.*?\)\s*$', '', full)


def build_scholar_map():
    """遍历 THEORY_TAXONOMY → {学者: [era短名, 学派, 学者]} + 别名条目"""
    result = {}
    for era_full, era_data in THEORY_TAXONOMY.items():
        era = era_short(era_full)
        for school, school_data in era_data.items():
            for scholar, _ in school_data.get('scholars', {}).items():
                if scholar in ('理论综合', '理论对比'):
                    continue
                result[scholar] = [era, school, scholar]
    return result


def add_alias_entries(scholar_map, aliases):
    """为每个正典学者的别名生成同名条目（如 迪尔凯姆→[古典时期,社会学主义,涂尔干]）"""
    canonical = aliases.get('canonical', {})
    for canon_name, alias_list in canonical.items():
        if canon_name not in scholar_map:
            continue
        entry = scholar_map[canon_name]
        for alias in alias_list:
            if alias and alias not in scholar_map:
                # 别名条目指向正典的 era/school，但 scholar 段写正典名
                scholar_map[alias] = [entry[0], entry[1], canon_name]
    return scholar_map


def main():
    mode = '--apply' if '--apply' in sys.argv else '--dry-run'

    aliases = json.load(open(ALIASES, encoding='utf-8'))
    mappings = json.load(open(MAPPINGS, encoding='utf-8'))

    new_map = build_scholar_map()
    add_alias_entries(new_map, aliases)

    old_map = mappings.get('scholar_to_era_school', {})
    added = {k: v for k, v in new_map.items() if k not in old_map}
    changed = {k: v for k, v in new_map.items()
               if k in old_map and old_map[k] != v}

    print(f'映射表: {len(old_map)} → {len(new_map)}')
    print(f'新增 {len(added)} 条，变更 {len(changed)} 条')
    print()
    print('=== 新增学者映射 ===')
    for k, v in sorted(added.items()):
        print(f'  {k}: {v}')
    if changed:
        print()
        print('=== 变更映射 ===')
        for k, v in sorted(changed.items()):
            print(f'  {k}: {old_map[k]} → {v}')

    if mode == '--apply':
        mappings['scholar_to_era_school'] = new_map
        with open(MAPPINGS, 'w', encoding='utf-8') as f:
            json.dump(mappings, f, ensure_ascii=False, indent=2)
        print(f'\n已回写 {MAPPINGS}')
    else:
        print(f'\n[dry-run] 未写文件。确认后用 --apply')


if __name__ == '__main__':
    main()
