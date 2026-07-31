#!/usr/bin/env bash
# Build the dissertation to the canonical output: Dissertation_with_figures.pdf
# Usage:  bash build.sh
set -e
cd "$(dirname "$0")"

SRC=Dissertation_IoT_AI_Poultry.tex
JOB=Dissertation_with_figures

if [ -f "$JOB.pdf" ] && ! (: > "$JOB.pdf") 2>/dev/null; then
  echo "ERROR: $JOB.pdf is open in a viewer. Close it and re-run." >&2
  exit 1
fi

# three passes so ToC / LoF / LoT / cross-references settle
for i in 1 2 3; do
  pdflatex -interaction=nonstopmode -jobname="$JOB" "$SRC" > /dev/null 2>&1 || true
done
pdflatex -interaction=nonstopmode -jobname="$JOB" "$SRC" > /dev/null 2>&1 || true

echo "errors:        $(grep -c '^!' $JOB.log || true)"
echo "overfull vbox: $(grep -c 'Overfull \\vbox' $JOB.log || true)"
echo "overfull hbox: $(grep -c 'Overfull \\hbox' $JOB.log || true)"
grep 'Output written' "$JOB.log"
