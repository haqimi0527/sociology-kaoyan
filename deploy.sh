#!/bin/bash
# Deploy web/ → repo root → GitHub Pages (cykaoyan.top)
# Run from: D:/workspace/sociology-kaoyan-app/
set -e

REPO_ROOT="D:/workspace/sociology-kaoyan-app"
WEB="$REPO_ROOT/web"

echo "=== Deploy sociology-kaoyan to GitHub Pages ==="

# 1. Run data validation before deploying
echo "[1/6] Run data validation..."
if python tests/validate_data.py; then
  echo "  OK format check passed"
else
  echo "  WARNING: format check found issues — review before proceeding"
  echo "  (run 'python tests/validate_data_semantic.py' for semantic checks)"
fi

# 2. Copy index.html
echo "[2/6] Copy index.html..."
cp "$WEB/index.html" "$REPO_ROOT/index.html"

# 3. Copy essential data files (not the intermediate/backup junk)
echo "[3/6] Copy data files..."
DATA_FILES=(
  concepts.json
  exams.json
  exam-prompts.json
  schools.json
  english-vocab.json
  politics.json
  politics-essay.json
  theory-topics.json
  methods-questions.json
  method-exam-freq.json
  questions-theory.json
)
for f in "${DATA_FILES[@]}"; do
  if [ -f "$WEB/data/$f" ]; then
    cp "$WEB/data/$f" "$REPO_ROOT/data/$f"
    echo "  OK $f"
  else
    echo "  SKIP $f (not found)"
  fi
done

# Copy rubric.md separately (lives in repo root data/, not web/data/)
if [ -f "$REPO_ROOT/data/rubric.md" ]; then
  echo "  OK rubric.md (in repo root)"
else
  echo "  NOTE rubric.md not found"
fi

# 4. Copy JS files
echo "[4/6] Copy JS files..."
if [ -f "$WEB/js/exam-engine.js" ]; then
  cp "$WEB/js/exam-engine.js" "$REPO_ROOT/js/exam-engine.js"
  echo "  OK exam-engine.js"
fi
# Copy any new JS files
for f in "$WEB/js"/*.js; do
  basename=$(basename "$f")
  if [ "$basename" != "exam-engine.js" ] && [ -f "$f" ]; then
    cp "$f" "$REPO_ROOT/js/$basename"
    echo "  OK $basename"
  fi
done

# 5. Cache versions are managed manually in web/index.html (bump ?v=N there when data changes).
#    Auto-bump removed: the old sed loop chain-polluted versions.
echo "[5/6] Cache versions: manually managed (bump ?v=N in web/index.html)"

# 6. Git commit & push + online verification
echo "[6/6] Git commit, push & verify..."

cd "$REPO_ROOT"
git add index.html data/ js/

if git diff --cached --quiet; then
  echo "  No changes to commit — skipping push"
else
  NOW=$(date '+%Y-%m-%d %H:%M')
  git commit -m "deploy: $NOW"
  git push origin main
  echo "  OK Pushed to GitHub"

  # Wait for GitHub Pages to start serving (usually fast, but CDN may lag)
  echo ""
  echo "--- Online verification (waiting 10s for Pages deploy) ---"
  sleep 10

  VERIFY_URL="https://cykaoyan.top"
  FAILED=0

  # Check 1: Homepage reachable
  HTTP_CODE=$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 "$VERIFY_URL" || echo "000")
  if [ "$HTTP_CODE" = "200" ]; then
    echo "  OK $VERIFY_URL → 200"
  else
    echo "  FAIL $VERIFY_URL → $HTTP_CODE"
    FAILED=1
  fi

  # Check 2: Core data files accessible and have reasonable size
  check_file() {
    local path=$1
    local min_size=$2
    local url="$VERIFY_URL/$path"
    local code
    code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 "$url" || echo "000")
    if [ "$code" != "200" ]; then
      echo "  FAIL $path → HTTP $code"
      FAILED=1
      return
    fi
    local size
    size=$(curl -s --max-time 15 "$url" | wc -c)
    if [ "$size" -lt "$min_size" ]; then
      echo "  FAIL $path → $size bytes (expected >= $min_size)"
      FAILED=1
    else
      echo "  OK $path → $size bytes"
    fi
  }

  check_file "data/concepts.json" 500000
  check_file "data/exams.json" 300000
  check_file "data/politics.json" 200000

  if [ $FAILED -eq 0 ]; then
    echo ""
    echo "=== All checks passed ==="
  else
    echo ""
    echo "=== WARNING: Some online checks failed ==="
    echo "Cloudflare CDN may be caching old versions. Try:"
    echo "  curl -H 'Cache-Control: no-cache' https://cykaoyan.top/data/concepts.json | wc -c"
  fi
fi

echo ""
echo "Live at: https://cykaoyan.top"
echo "Purge CDN: https://dash.cloudflare.com (if needed)"
