from __future__ import annotations

import base64
import json
import math
import statistics
import uuid
from pathlib import Path

import cv2
import ezdxf
import numpy as np
import pytesseract
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "analysis" / "source_renders" / "TAV07"
OUT = ROOT / "analysis" / "scan2dxf_test" / "TAV07"
DPI = 300.0
MM_PER_IN = 25.4

CFG = {
    "denoise_kernel": 3,
    "adaptive_block_size": 41,
    "adaptive_c": 12,
    "hough_threshold": 70,
    "min_line_length_px": 80,
    "max_line_gap_px": 12,
    "ocr_min_confidence": 40.0,
}


def preprocess(path: Path) -> np.ndarray:
    img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise RuntimeError(f"Immagine non leggibile: {path}")
    img = cv2.medianBlur(img, CFG["denoise_kernel"])
    return cv2.adaptiveThreshold(
        img,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        CFG["adaptive_block_size"],
        CFG["adaptive_c"],
    )


def detect_lines(binary: np.ndarray) -> list[dict]:
    raw = cv2.HoughLinesP(
        binary,
        rho=1,
        theta=np.pi / 180.0,
        threshold=CFG["hough_threshold"],
        minLineLength=CFG["min_line_length_px"],
        maxLineGap=CFG["max_line_gap_px"],
    )
    if raw is None:
        return []
    # OpenCV 4 commonly returns (N,1,4), while OpenCV 5 may return (N,4).
    # Normalise both representations to the same stable iteration contract.
    normalized = np.asarray(raw).reshape(-1, 4)
    h, w = binary.shape[:2]
    diag = max(1.0, math.hypot(h, w))
    out = []
    for x1, y1, x2, y2 in normalized:
        dx, dy = float(x2 - x1), float(y2 - y1)
        length = math.hypot(dx, dy)
        angle = math.degrees(math.atan2(dy, dx))
        if angle < 0:
            angle += 180.0
        if angle <= 5 or angle >= 175:
            family = "horizontal"
        elif 85 <= angle <= 95:
            family = "vertical"
        else:
            family = "diagonal"
        out.append(
            {
                "x1": float(x1), "y1": float(y1), "x2": float(x2), "y2": float(y2),
                "length_px": length,
                "angle_deg": angle,
                "family": family,
                "confidence": min(1.0, length / (0.15 * diag)),
            }
        )
    return out


def detect_text(path: Path) -> tuple[list[dict], str | None]:
    try:
        data = pytesseract.image_to_data(
            Image.open(path),
            lang="ita+eng",
            config="--psm 11",
            output_type=pytesseract.Output.DICT,
        )
    except Exception as exc:
        return [], str(exc)
    out = []
    for i, raw in enumerate(data.get("text", [])):
        txt = (raw or "").strip()
        try:
            conf = float(data["conf"][i])
        except Exception:
            conf = -1.0
        if not txt or conf < CFG["ocr_min_confidence"]:
            continue
        out.append(
            {
                "id": f"T-{uuid.uuid4().hex[:10]}",
                "text": txt,
                "x": float(data["left"][i]), "y": float(data["top"][i]),
                "w": float(data["width"][i]), "h": float(data["height"][i]),
                "confidence": conf / 100.0,
                "state": "candidate",
                "engine": "tesseract",
            }
        )
    return out, None


def px_to_mm(v: float) -> float:
    return v * MM_PER_IN / DPI


def write_dxf(path: Path, width: int, height: int, lines: list[dict], texts: list[dict]) -> None:
    doc = ezdxf.new("R2010")
    doc.units = ezdxf.units.MM
    for name, color in [
        ("00_SOURCE_REF", 8),
        ("10_GEOMETRY_CANDIDATE", 7),
        ("20_TEXT_CANDIDATE", 1),
        ("30_TEXT_VALIDATED", 5),
        ("90_REVIEW_MARKUP", 3),
    ]:
        if name not in doc.layers:
            doc.layers.add(name=name, color=color)
    msp = doc.modelspace()
    page_h_mm = px_to_mm(height)

    def cad_xy(x: float, y: float) -> tuple[float, float]:
        return px_to_mm(x), page_h_mm - px_to_mm(y)

    for line in lines:
        msp.add_line(
            cad_xy(line["x1"], line["y1"]),
            cad_xy(line["x2"], line["y2"]),
            dxfattribs={"layer": "10_GEOMETRY_CANDIDATE"},
        )
    off_px = 5.0 * DPI / MM_PER_IN
    for t in texts:
        x, y = cad_xy(t["x"] + t["w"] + off_px, t["y"] + t["h"])
        text_h = max(1.5, px_to_mm(max(t["h"], 12)))
        msp.add_text(t["text"], dxfattribs={"layer": "20_TEXT_CANDIDATE", "height": text_h}).set_placement((x, y))
    doc.saveas(path)


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def write_embedded_review_svg(path: Path, image_path: Path, lines: list[dict], texts: list[dict]) -> None:
    im = Image.open(image_path).convert("L")
    ow, oh = im.size
    max_w = 1500
    scale = min(1.0, max_w / ow)
    pw, ph = max(1, round(ow * scale)), max(1, round(oh * scale))
    if scale < 1.0:
        im = im.resize((pw, ph), Image.Resampling.LANCZOS)
    from io import BytesIO
    buf = BytesIO()
    im.save(buf, format="JPEG", quality=55, optimize=True)
    data_uri = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" width="{pw}" height="{ph}" viewBox="0 0 {pw} {ph}">',
        '<g inkscape:groupmode="layer" inkscape:label="00_SOURCE_REF" id="layer-bg">',
        f'<image x="0" y="0" width="{pw}" height="{ph}" opacity="0.42" href="{data_uri}"/>',
        '</g>',
        '<g inkscape:groupmode="layer" inkscape:label="10_GEOMETRY_CANDIDATE" id="layer-geom" fill="none" stroke="#111" stroke-width="0.8">',
    ]
    for l in lines:
        parts.append(f'<line x1="{l["x1"]*scale:.2f}" y1="{l["y1"]*scale:.2f}" x2="{l["x2"]*scale:.2f}" y2="{l["y2"]*scale:.2f}"/>')
    parts += [
        '</g>',
        '<g inkscape:groupmode="layer" inkscape:label="20_TEXT_CANDIDATE" id="layer-text" fill="#c00" stroke="#c00" stroke-width="0.7" font-family="sans-serif">',
    ]
    for t in texts:
        x, y, w, h = (t[k] * scale for k in ("x", "y", "w", "h"))
        parts.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" fill="none"/>')
        parts.append(f'<text x="{x+w+5:.2f}" y="{y+max(h,10):.2f}" font-size="{max(h,10):.2f}" stroke="none">{esc(t["text"])}</text>')
    parts += ['</g>', '</svg>']
    path.write_text("\n".join(parts), encoding="utf-8")


def median(values: list[float]) -> float:
    return statistics.median(values) if values else 0.0


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tiles = sorted(SRC.glob("r[1-4]_c[1-3].jpg"))
    if len(tiles) != 12:
        raise RuntimeError(f"Attesi 12 tile TAV07, trovati {len(tiles)}")

    all_results = []
    for tile in tiles:
        with Image.open(tile) as im:
            width, height = im.size
        binary = preprocess(tile)
        lines = detect_lines(binary)
        texts, ocr_error = detect_text(tile)
        lengths = [l["length_px"] for l in lines]
        families = {name: sum(1 for l in lines if l["family"] == name) for name in ("horizontal", "vertical", "diagonal")}
        confs = [t["confidence"] for t in texts]
        row = {
            "tile": tile.name,
            "source_path": str(tile.relative_to(ROOT)),
            "width_px": width,
            "height_px": height,
            "source_bytes": tile.stat().st_size,
            "line_count": len(lines),
            "line_families": families,
            "median_line_length_px": round(median(lengths), 2),
            "max_line_length_px": round(max(lengths) if lengths else 0.0, 2),
            "ocr_candidate_count": len(texts),
            "ocr_mean_confidence": round(statistics.fmean(confs), 4) if confs else 0.0,
            "ocr_median_confidence": round(median(confs), 4),
            "ocr_error": ocr_error,
            "lines": lines,
            "texts": texts,
        }
        all_results.append(row)

    representative = max(all_results, key=lambda r: (r["line_count"], r["ocr_candidate_count"]))
    rep_tile = SRC / representative["tile"]
    write_embedded_review_svg(OUT / "review_representative.svg", rep_tile, representative["lines"], representative["texts"])
    write_dxf(OUT / "review_representative.dxf", representative["width_px"], representative["height_px"], representative["lines"], representative["texts"])

    compact = []
    for r in all_results:
        compact.append({k: v for k, v in r.items() if k not in ("lines", "texts")})
    (OUT / "metrics.json").write_text(json.dumps({
        "source": "TAV.7 — Piano Quarto e Piano Copertura",
        "dpi_assumed_from_source_render": DPI,
        "config": CFG,
        "representative_tile": representative["tile"],
        "tiles": compact,
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    (OUT / "geometry_representative.json").write_text(json.dumps(representative["lines"], indent=2), encoding="utf-8")
    (OUT / "text_candidates_representative.json").write_text(json.dumps(representative["texts"], indent=2, ensure_ascii=False), encoding="utf-8")

    total_lines = sum(r["line_count"] for r in all_results)
    total_ocr = sum(r["ocr_candidate_count"] for r in all_results)
    total_bytes = sum(r["source_bytes"] for r in all_results)
    ocr_confs = [t["confidence"] for r in all_results for t in r["texts"]]
    all_lengths = [l["length_px"] for r in all_results for l in r["lines"]]
    fam_total = {name: sum(r["line_families"][name] for r in all_results) for name in ("horizontal", "vertical", "diagonal")}
    sample_texts = sorted(
        [t for r in all_results for t in r["texts"]], key=lambda t: t["confidence"], reverse=True
    )[:30]

    lines_md = [
        "# Test Scan2DXF su TAV.7 — Piano Quarto e Piano Copertura",
        "",
        "## Fonte",
        "",
        f"- 12 tile raster persistenti 4×3 in `analysis/source_renders/TAV07/`.",
        f"- Dimensione complessiva dei tile: {total_bytes/1024/1024:.2f} MiB.",
        f"- Elaborazione geometrica eseguita alla risoluzione originale dei tile, con conversione CAD assunta a {DPI:.0f} DPI.",
        "- Nessun candidato automatico viene promosso a dato validato.",
        "",
        "## Risultati quantitativi",
        "",
        f"- Segmenti Hough candidati: **{total_lines}**.",
        f"- Famiglie: orizzontali **{fam_total['horizontal']}**, verticali **{fam_total['vertical']}**, diagonali **{fam_total['diagonal']}**.",
        f"- Lunghezza mediana segmento: **{median(all_lengths):.1f} px**.",
        f"- Candidati OCR con confidenza ≥ {CFG['ocr_min_confidence']:.0f}%: **{total_ocr}**.",
        f"- Confidenza OCR media: **{(statistics.fmean(ocr_confs)*100 if ocr_confs else 0):.1f}%**.",
        f"- Tile rappresentativo scelto automaticamente: **{representative['tile']}** ({representative['line_count']} segmenti; {representative['ocr_candidate_count']} testi).",
        "",
        "## Valutazione del collaudo",
        "",
        "- **Raster / provenienza:** PASS — i 12 tile vengono letti direttamente dalla fonte persistente.",
        "- **Geometria candidata:** PASS TECNICO PARZIALE — la catena produce segmenti reali, ma Hough non distingue ancora travi/assi/quote/cartiglio/retini; serve classificazione e fusione delle collinearità prima della promozione CAD.",
        "- **Testo:** REVIEW REQUIRED — Tesseract è soltanto una base per stampatello; il manoscritto tecnico deve restare candidato e richiede HTR dedicato + verifica umana.",
        "- **SVG/DXF di revisione:** PASS — generati con livelli separati e senza promozione automatica dei testi.",
        "",
        "## Prime letture OCR ad alta confidenza (non validate)",
        "",
    ]
    for t in sample_texts:
        lines_md.append(f"- `{t['text']}` — {t['confidence']*100:.1f}%")
    lines_md += [
        "",
        "## Output",
        "",
        "- `review_representative.svg`: raster alleggerito incorporato + linee candidate + testi candidati.",
        "- `review_representative.dxf`: geometrie/testi candidati in livelli CAD separati.",
        "- `geometry_representative.json`: segmenti con coordinate, lunghezza, angolo e famiglia.",
        "- `text_candidates_representative.json`: letture OCR con bbox e confidenza.",
        "- `metrics.json`: metriche di tutti i 12 tile.",
        "",
        "## Gate successivo suggerito",
        "",
        "Prima di usare il DXF come geometria strutturale occorre introdurre: (1) rimozione bordi/cartiglio/pieghe, (2) fusione segmenti collineari, (3) classificazione semantica linea/trave/quota/testo/retino, (4) HTR manoscritto mirato, (5) approvazione visuale per entità o regione.",
    ]
    (OUT / "REPORT_TEST_TAV07.md").write_text("\n".join(lines_md) + "\n", encoding="utf-8")

    print(json.dumps({
        "status": "PASS_WITH_REVIEW",
        "tiles": len(all_results),
        "total_lines": total_lines,
        "total_ocr_candidates": total_ocr,
        "representative_tile": representative["tile"],
        "output_dir": str(OUT.relative_to(ROOT)),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
