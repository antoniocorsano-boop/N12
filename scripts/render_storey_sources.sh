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

# M1-F foundation geometry and support cross-registration. TAV-01S is the primary foundation carpenteria;
# full TAV-02S is included to bind the first-storey support grid to foundation intersections/members.
render_one "TAV01S" "archive/documentazione_originaria/tavola1-2.pdf" "carpenteria_fondazioni" "fondazioni"
render_one "TAV02S" "archive/documentazione_originaria/tavola2-2.pdf" "carpenteria_I_impalcato" "G1_piano_terra"

# M1-A reinforcement source set. These are derivative renders only; immutable PDFs remain authoritative.
render_one "TAV01A" "archive/documentazione_originaria/tavola1-3.pdf" "armature_travi" "fondazioni_primo_livello"
render_one "TAV02A" "archive/documentazione_originaria/tavola 2-3.pdf" "armature_travi" "G1_piano_terra"
render_one "TAV034A" "archive/documentazione_originaria/tavola3a-4a.pdf" "armature_travi" "G2_G3"
render_one "TAV05A" "archive/documentazione_originaria/tavola 5-3.pdf" "armature_travi" "G4"
render_one "TAV06A" "archive/documentazione_originaria/tavola 6.pdf" "armature_copertura" "G5_copertura"
render_one "TAV07A" "archive/documentazione_originaria/tavola7.pdf" "abaco_dettagli_pilastri" "pilastri_particolari"

# Architectural plans are mandatory in the special-feature audit: balcony/terrace outlines, infill lines,
# useful-floor extensions and geometry omitted or simplified in the historical frame calculation.
render_one "TAV01" "archive/documentazione_originaria/tavola1.pdf" "pianta_architettonica" "controllo_geometrico"
render_one "TAV02" "archive/documentazione_originaria/tavola2.pdf" "pianta_architettonica" "piano_terra"
render_one "TAV03" "archive/documentazione_originaria/tavola 3.pdf" "pianta_architettonica" "piano_superiore"
render_one "TAV04" "archive/documentazione_originaria/tavola 4.pdf" "pianta_architettonica" "piano_superiore"

# Geometry/elevation sources retained for direct cross-registration with the reinforcement sheets.
render_one "TAV03S" "archive/documentazione_originaria/tavola3-2.pdf" "carpenteria_II_impalcato" "G2"
render_one "TAV04S" "archive/documentazione_originaria/tavola4-2.pdf" "carpenteria_III_impalcato" "G3"
render_one "TAV05S" "archive/documentazione_originaria/tavola 5.pdf" "carpenteria_IV_impalcato" "G4"
render_one "TAV05E" "archive/documentazione_originaria/tavola5-2.pdf" "prospetto_elevazione" "sviluppo_verticale"
render_one "TAV06S" "archive/documentazione_originaria/tavola 6-1.pdf" "carpenteria_copertura" "G5_copertura"
render_one "TAV06E" "archive/documentazione_originaria/tavola6-2.pdf" "sezione_elevazione" "sviluppo_verticale"

# M1-A targeted review package: existing canonical TAV-02S tiles around supports 17-24.
# These are copied unchanged only to make the reinforcement/carpenteria cross-check reproducible.
for tile in r2_c1 r2_c2 r3_c1 r3_c2 r4_c1 r4_c2; do
  cp "analysis/source_renders/TAV02S/${tile}.jpg" "$OUT/TAV02S_${tile}.jpg"
done

printf 'archive_branch,%s\narchive_commit,%s\nrender_policy,immutable_source_to_300dpi_jpeg_no_interpretation\nreview_package,TAV02S_r2_c1+r2_c2+r3_c1+r3_c2+r4_c1+r4_c2 copied unchanged from canonical tile set\nspecial_feature_audit,architectural TAV01-TAV04 included for balcony/terrace/infill geometry cross-check\nfoundation_audit,TAV01S foundation carpenteria plus full TAV02S support-grid cross-registration included for M1-F\n' "$ARCHIVE_BRANCH" "$ARCHIVE_COMMIT" > "$OUT/run_metadata.txt"