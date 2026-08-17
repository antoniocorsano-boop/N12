"""
Task 2: Document Registry Loader
Loads the 18 PDFs from manifest into OriginalDocument objects.
Validates file existence and SHA256 integrity.
"""
import csv
import hashlib
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

from model.etwin.document_engine import OriginalDocument

MANIFEST_PATH = Path(r"data\canonical\tavole_originali_manifest.csv")
ARCHIVE_DIR = Path(r"archive\documentazione_originaria")


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def load_registry(manifest_path: Path = MANIFEST_PATH,
                  archive_dir: Path = ARCHIVE_DIR) -> list[OriginalDocument]:
    """Load OriginalDocument objects from manifest CSV."""
    documents = []

    with open(manifest_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            doc_id = row['id']
            filename = row['file']
            file_path = archive_dir / filename

            if not file_path.exists():
                print(f"  WARNING: {file_path} not found, skipping")
                continue

            # Verify SHA256
            actual_sha = compute_sha256(file_path)
            expected_sha = row['sha256']
            sha_ok = actual_sha == expected_sha
            if not sha_ok:
                print(f"  WARNING: SHA256 mismatch for {filename}")
                print(f"    Expected: {expected_sha}")
                print(f"    Actual:   {actual_sha}")

            # Get page count and dimensions using pypdfium2
            import pypdfium2 as pdfium
            pdf = pdfium.PdfDocument(str(file_path))
            page = pdf[0]
            w_pts, h_pts = page.get_size()
            w_mm = w_pts * 25.4 / 72
            h_mm = h_pts * 25.4 / 72
            n_pages = len(pdf)
            pdf.close()

            doc = OriginalDocument(
                document_id=doc_id,
                file_path=str(file_path.relative_to(Path('.')).as_posix()),
                sha256=actual_sha,
                drawing_id=row.get('id', doc_id),
                discipline=row.get('classe', ''),
                drawing_type=row.get('classe', ''),
                page_count=n_pages,
                page_width_pts=round(w_pts, 1),
                page_height_pts=round(h_pts, 1),
                page_width_mm=round(w_mm, 1),
                page_height_mm=round(h_mm, 1),
                file_size_bytes=file_path.stat().st_size,
                notes=f"SHA256_verified={sha_ok}",
            )
            documents.append(doc)

    return documents


def main():
    print("=" * 60)
    print("TASK 2: DOCUMENT REGISTRY LOADER")
    print("=" * 60)

    if not MANIFEST_PATH.exists():
        print(f"FATAL: Manifest not found: {MANIFEST_PATH}")
        sys.exit(1)

    print(f"\nManifest: {MANIFEST_PATH}")
    print(f"Archive:  {ARCHIVE_DIR}")

    documents = load_registry()

    print(f"\nLoaded: {len(documents)} documents")
    print()

    # Summary table
    print(f"{'ID':<12} {'Type':<28} {'Pages':>5} {'Size':>8} {'Dims (mm)':<16}")
    print("-" * 75)
    for doc in documents:
        dims = f"{doc.page_width_mm:.0f}x{doc.page_height_mm:.0f}"
        size_kb = doc.file_size_bytes / 1024
        print(f"{doc.document_id:<12} {doc.discipline:<28} {doc.page_count:>5} {size_kb:>7.0f}K {dims:<16}")

    # Verify all SHAs
    all_sha_ok = all("SHA256_verified=True" in doc.notes for doc in documents)
    print(f"\nSHA256 verification: {'ALL OK' if all_sha_ok else 'MISMATCHES FOUND'}")

    # Save registry
    from model.etwin.document_engine import save_json
    output_path = Path(r"docs\FOGLIO_LAVORO\etwin_crops\document_registry.json")
    save_json([d.to_dict() for d in documents], output_path)
    print(f"Registry saved: {output_path}")

    return documents


if __name__ == "__main__":
    docs = main()
    print(f"\nDONE: {len(docs)} documents loaded")
