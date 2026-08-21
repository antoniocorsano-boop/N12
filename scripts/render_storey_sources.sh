#!/usr/bin/env bash
set -euo pipefail

ARCHIVE_BRANCH="archive/originali-alta-risoluzione"
OUT="analysis/storey_source_renders"
mkdir -p "$OUT"
rm -f "$OUT"/*

git fetch --no-tags --depth=1 origin "$ARCHIVE_BRANCH"
ARCHIVE_COMMIT="$(git rev-parse FETCH_HEAD)"

cat > "$OUT/manifest.csv" <<'EOF'
source_id,archive_path,role,level,archive_commit,render_file,pdf_pages,pdf_width_pt,pdf_height_pt,render_dpi,status
EOF

render_one() {
  local id="$1"
  local path="$2"
  local role="$3"
  local level="$4"
  local pdf="/tmp/${id}.pdf"
  local stem="$OUT/${id}"

  git show "${ARCHIVE_COMMIT}:${path}" > "$pdf"
  local pages width height
  pages="$(pdfinfo "$pdf" | awk -F: '/^Pages:/ {gsub(/ /,"",$2); print $2}')"
  width="$(pdfinfo "$pdf" | awk '/^Page size:/ {print $3}')"
  height="$(pdfinfo "$pdf" | awk '/^Page size:/ {print $5}')"

  pdftoppm -jpeg -jpegopt quality=92 -r 300 -singlefile "$pdf" "$stem"
  mv "${stem}.jpg" "${stem}_300dpi.jpg"
  printf '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' \
    "$id" "$path" "$role" "$level" "$ARCHIVE_COMMIT" "${id}_300dpi.jpg" "$pages" "$width" "$height" "300" "RENDERED_FROM_IMMUTABLE_ARCHIVE" \
    >> "$OUT/manifest.csv"
}

render_one "TAV03S" "archive/documentazione_originaria/tavola3-2.pdf" "carpenteria_II_impalcato" "G2"
render_one "TAV04S" "archive/documentazione_originaria/tavola4-2.pdf" "carpenteria_III_impalcato" "G3"
render_one "TAV05S" "archive/documentazione_originaria/tavola 5.pdf" "carpenteria_IV_impalcato" "G4"
render_one "TAV05E" "archive/documentazione_originaria/tavola5-2.pdf" "prospetto_elevazione" "sviluppo_verticale"
render_one "TAV06S" "archive/documentazione_originaria/tavola 6-1.pdf" "carpenteria_copertura" "G5_copertura"
render_one "TAV06E" "archive/documentazione_originaria/tavola6-2.pdf" "sezione_elevazione" "sviluppo_verticale"

printf 'archive_branch,%s\narchive_commit,%s\nrender_policy,immutable_source_to_300dpi_jpeg_no_interpretation\n' "$ARCHIVE_BRANCH" "$ARCHIVE_COMMIT" > "$OUT/run_metadata.txt"
