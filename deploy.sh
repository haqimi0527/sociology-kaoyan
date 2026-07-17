#!/bin/bash
# Deploy web/ → repo root → GitHub Pages (cykaoyan.top)
# Run from: D:/workspace/sociology-kaoyan-app/
set -e

REPO_ROOT="D:/workspace/sociology-kaoyan-app"
WEB="$REPO_ROOT/web"

echo "=== Deploy sociology-kaoyan to GitHub Pages ==="

# 1. Copy index.html
echo "[1/5] Copy index.html..."
cp "$WEB/index.html" "$REPO_ROOT/index.html"

# 2. Copy essential data files (not the intermediate/backup junk)
echo "[2/5] Copy data files..."
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
  rubric.md
)
for f in "${DATA_FILES[@]}"; do
  if [ -f "$WEB/data/$f" ]; then
    cp "$WEB/data/$f" "$REPO_ROOT/data/$f"
    echo "  ✓ $f"
  else
    echo "  ⚠ $f (not found, skipped)"
  fi
done

# 3. Copy JS files
echo "[3/5] Copy JS files..."
cp "$WEB/js/exam-engine.js" "$REPO_ROOT/js/exam-engine.js"
echo "  ✓ exam-engine.js"

# 4. Cache versions are managed in web/index.html (bump ?v=N there when data changes).
#    Auto-bump removed: the old sed loop chain-polluted versions (v=1→2 then v=2→3 hit the same file twice)
#    and only patched the root copy, so web/ and root drifted apart.
echo "[4/5] Cache versions: managed manually in web/index.html (no auto-bump)"

# 5. Git commit & push
echo "[5/5] Git commit & push..."
cd "$REPO_ROOT"
git add index.html data/ js/
git status --short

if git diff --cached --quiet; then
  echo "  No changes to commit"
else
  NOW=$(date '+%Y-%m-%d %H:%M')
  git commit -m "deploy: $NOW"
  git push origin main
  echo "  ✓ Pushed to GitHub"
fi

echo ""
echo "=== Deploy complete ==="
echo "Live at: https://cykaoyan.top"
echo "Verify:  https://cykaoyan.top/?v=$(date +%s)"
