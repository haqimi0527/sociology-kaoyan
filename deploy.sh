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

# 4. Auto-bump cache version in fetch calls
echo "[4/5] Bump cache versions..."
INDEX="$REPO_ROOT/index.html"
# Find all ?v=N patterns in fetch calls and bump them
# Extract current versions, bump each by 1
grep -oP "(?<=fetch\('data/[^']+\?v=)\d+" "$INDEX" | sort -u | while read -r ver; do
  new=$((ver + 1))
  echo "  v=$ver → v=$new"
done

# Actually do the bump (macOS/BSD sed compatible)
grep -oP "fetch\('data/[^']+\?v=\K\d+" "$INDEX" | sort -u | while read -r ver; do
  new=$((ver + 1))
  sed -i "s/?v=$ver'/?v=$new'/g" "$INDEX"
done

echo "  Cache versions bumped"

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
