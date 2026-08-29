"""N12 PDF Viewer — Visualizza le tavole originali del Condominio N.12."""
import streamlit as st
import pdfplumber
from PIL import Image
import os

st.set_page_config(page_title="N12 — Visualizzatore Tavole", layout="wide")

PDF_DIR = r"C:\Users\anton\Progetti ingegneria civile\Condominio N.12\documentazione originaria"

PDFS = {
    "TAV-01S Fondazioni": "tavola1-2.pdf",
    "TAV-02S I° Impalcato": "tavola2-2.pdf",
    "TAV-03S II° Impalcato": "tavola3-2.pdf",
    "TAV-04S III° Impalcato": "tavola4-2.pdf",
    "TAV-05S IV° Impalcato": "tavola 5.pdf",
    "TAV-06S Copertura": "tavola 6-1.pdf",
    "TAV-01 Architettonica": "tavola1.pdf",
    "TAV-02 Architettonica": "tavola2.pdf",
    "TAV-03 Architettonica": "tavola3.pdf",
    "TAV-04 Architettonica": "tavola4.pdf",
    "TAV-05E Prospetto": "tavola5-2.pdf",
    "TAV-06E Sezione": "tavola6-2.pdf",
    "TAV-07A Dettagli": "tavola7.pdf",
    "TAV-1": "tavola 2-3.pdf",
    "TAV-2": "tavola1-3.pdf",
    "TAV-3": "tavola5-3.pdf",
    "TAV-3a": "tavola3a-4a.pdf",
    "TAV-6": "tavola6.pdf",
}

st.title("N12 — Visualizzatore Tavole Originali")
st.caption("Condominio N.12, Ariano Irpino — documentazione originaria")

selected = st.selectbox("Seleziona tavola:", list(PDFS.keys()))
filename = PDFS[selected]
path = os.path.join(PDF_DIR, filename)

if not os.path.exists(path):
    st.error(f"File non trovato: {path}")
else:
    with pdfplumber.open(path) as pdf:
        n_pages = len(pdf.pages)
        if n_pages > 1:
            page_num = st.number_input("Pagina:", 1, n_pages, 1) - 1
        else:
            page_num = 0

        page = pdf.pages[page_num]
        st.write(f"**{selected}** — {filename} — Pagina {page_num+1}/{n_pages} — {page.width:.0f}×{page.height:.0f} pt")

        # Render at configurable DPI
        dpi = st.slider("Risoluzione (DPI):", 100, 300, 200)
        img = page.to_image(resolution=dpi)
        pil_img = img.original.convert("RGB")

        # Scale to fit width
        max_width = st.slider("Larghezza display:", 600, 1600, 1000)
        ratio = max_width / pil_img.width
        new_size = (max_width, int(pil_img.height * ratio))
        pil_img = pil_img.resize(new_size, Image.LANCZOS)

        st.image(pil_img, use_container_width=False)

        st.info("Confronta le 4 tavole carpenteria (TAV-02S → TAV-05S) per verificare se G1-G4 hanno configurazioni strutturali diverse.")
