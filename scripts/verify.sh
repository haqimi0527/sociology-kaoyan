#!/usr/bin/env bash
# 一键数据验证链（方向3）
# 用法: bash scripts/verify.sh
# 注意: 用 Git Bash 跑（避免 PowerShell 中文乱码）
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8

echo "========== 1. validate_data（数据完整性）=========="
python tests/validate_data.py
V1=$?

echo
echo "========== 2. validate_data_semantic（语义/幻觉）=========="
python tests/validate_data_semantic.py
V2=$?

echo
echo "========== 3. audit_taxonomy（分类审计）=========="
python tests/audit_taxonomy.py
V3=$?

echo
echo "========== 4. dedupe --report（重复组统计）=========="
python pipeline/dedupe_concepts.py --report
V4=$?

echo
echo "========== 5. normalize --check（chapter 归一检查）=========="
python pipeline/normalize_chapters.py --check
V5=$?

echo
echo "========== 结果 =========="
echo "  validate_data:     $([ $V1 -eq 0 ] && echo PASS || echo FAIL)"
echo "  validate_semantic: $([ $V2 -eq 0 ] && echo PASS || echo FAIL)"
echo "  audit_taxonomy:    $([ $V3 -eq 0 ] && echo PASS || echo FAIL)"
echo "  dedupe_report:     $([ $V4 -eq 0 ] && echo PASS || echo FAIL)"
echo "  normalize_check:   $([ $V5 -eq 0 ] && echo PASS || echo FAIL)"

if [ $V1 -ne 0 ] || [ $V2 -ne 0 ] || [ $V3 -ne 0 ] || [ $V4 -ne 0 ] || [ $V5 -ne 0 ]; then
    echo "[FAIL] 验证链未通过"
    exit 1
fi
echo "[PASS] 全部验证通过"
