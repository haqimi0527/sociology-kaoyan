#!/usr/bin/env bash
# 一键数据验证链（方向3 升级版）
# 用法: bash scripts/verify.sh [--strict]
# 注意: 用 Git Bash 跑（避免 PowerShell 中文乱码）
#
# 退出码语义（audit_runner 统一出口）:
#   0 = 真PASS（0 ERROR / 0 blocker WARN）
#   1 = FAIL（有 ERROR，数据真错位/结构破坏）
#   2 = REVIEW（0 ERROR 但有 blocker WARN 须人审，不再是"全绿"）
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8

STRICT=""
if [[ "${1:-}" == "--strict" ]]; then
  STRICT="--strict"
fi

echo "========== 统一审计出口 audit_runner =========="
python pipeline/audit_runner.py $STRICT
V=$?

echo
echo "========== 旧链兼容（保留单跑能力） =========="
python tests/validate_data.py >/dev/null 2>&1
T1=$?
python tests/validate_data_semantic.py >/dev/null 2>&1
T2=$?
python tests/audit_taxonomy.py >/dev/null 2>&1
T3=$?
python pipeline/dedupe_concepts.py --report >/dev/null 2>&1
T4=$?
python pipeline/normalize_chapters.py --check >/dev/null 2>&1
T5=$?

echo "  validate_data:       $([ $T1 -eq 0 ] && echo PASS || echo FAIL)"
echo "  validate_semantic:   $([ $T2 -eq 0 ] && echo PASS || echo FAIL)"
echo "  audit_taxonomy:      $([ $T3 -eq 0 ] && echo PASS || echo FAIL)"
echo "  dedupe_report:       $([ $T4 -eq 0 ] && echo PASS || echo FAIL)"
echo "  normalize_check:     $([ $T5 -eq 0 ] && echo PASS || echo FAIL)"

case $V in
  0) echo "[PASS] 0 ERROR / 0 blocker WARN";;
  1) echo "[FAIL] 有 ERROR，见 D:/workspace/_audit_report.md";;
  2) echo "[REVIEW] 0 ERROR 但有 blocker WARN 须人审，见 D:/workspace/_audit_report.md";;
esac
exit $V
