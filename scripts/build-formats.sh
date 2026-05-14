#!/usr/bin/env bash
# Build EPUB and PDF for 《代码之后：成为 AI 系统架构师》
set -euo pipefail

BOOK_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SRC_DIR="$BOOK_DIR/src"
OUT_DIR="$BOOK_DIR/output"

# Source files in book order
CHAPTERS=(
  "chapter_00.md"
  "chapter_01.md"
  "chapter_02.md"
  "chapter_03.md"
  "chapter_04.md"
  "chapter_05.md"
  "chapter_06.md"
  "chapter_07.md"
  "chapter_08.md"
  "chapter_09.md"
  "appendix_a.md"
  "appendix_b.md"
  "appendix_c.md"
  "appendix_d.md"
  "appendix_e.md"
  "appendix_f.md"
  "about.md"
)

mkdir -p "$OUT_DIR"

# Build list of source files with full paths
INPUT_FILES=""
for ch in "${CHAPTERS[@]}"; do
  INPUT_FILES="$INPUT_FILES $SRC_DIR/$ch"
done

echo "=== Building EPUB ==="
pandoc $INPUT_FILES \
  --metadata-file="$BOOK_DIR/metadata.yaml" \
  --toc --toc-depth=2 \
  --epub-cover-image="$SRC_DIR/images/cover.jpg" \
  --css="$BOOK_DIR/theme/epub.css" \
  -o "$OUT_DIR/代码之后-AI系统架构师.epub" \
  --resource-path="$SRC_DIR"
echo "  ✓ $OUT_DIR/代码之后-AI系统架构师.epub"

echo "=== Building HTML for PDF ==="
mdbook build "$BOOK_DIR"
echo "  ✓ HTML built"

echo "=== Building PDF (headless Chromium) ==="
python3 "$BOOK_DIR/scripts/build-pdf.py"
echo "  ✓ $OUT_DIR/代码之后-AI系统架构师.pdf"

echo ""
echo "Done. Output files:"
ls -lh "$OUT_DIR/"
