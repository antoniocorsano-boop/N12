"""N12 Floor Comparison — Side-by-side carpenteria viewer with zoom."""
import streamlit as st
import pdfplumber
from PIL import Image
import os

st.set_page_config(page_title="N12 — Confronto Impalcati", layout="wide")

PDF_DIR = r"C:\Users\anton\Progetti ingegneria civile\Condominio N.12\documentazione originaria"

FLOORS = {
    "G1 — I° Impalcato": "tavola2-2.pdf",
    "G2 — II° Impalcato": "tavola3-2.pdf",
    "G3 — III° Impalcato": "tavola4-2.pdf",
    "G4 — IV° Impalcato": "tavola 5.pdf",
}

st.title("Confronto Impalcati G1↔G4")
st.caption("Seleziona due livelli da confrontare. Identifica le differenze nelle travi.")

col1_label, col2_label = st.columns(2)
with col1_label:
    left = st.selectbox("Livello A:", list(FLOORS.keys()), index=0, key="left")
with col2_label:
    right = st.selectbox("Livello B:", list(FLOORS.keys()), index=3, key="right")

dpi = st.slider("Risoluzione:", 100, 300, 200)
max_w = st.slider("Larghezza per livello:", 400, 900, 600)

def render_page(filename, dpi_val, max_width):
    path = os.path.join(PDF_DIR, filename)
    with pdfplumber.open(path) as pdf:
        page = pdf.pages[0]
        img = page.to_image(resolution=dpi_val)
        pil = img.original.convert("RGB")
        ratio = max_width / pil.width
        pil = pil.resize((max_width, int(pil.height * ratio)), Image.LANCZOS)
        return pil, page.width, page.height

col_l, col_r = st.columns(2)

with col_l:
    st.subheader(left)
    pil_l, w_l, h_l = render_page(FLOORS[left], dpi, max_w)
    st.image(pil_l, use_container_width=False)

with col_r:
    st.subheader(right)
    pil_r, w_r, h_r = render_page(FLOORS[right], dpi, max_w)
    st.image(pil_r, use_container_width=False)

st.divider()
st.subheader("Registra differenze")

if "diffs" not in st.session_state:
    st.session_state.diffs = []

with st.form("diff_form", clear_on_submit=True):
    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        beam_id = st.text_input("ID Trave (es. B17, C005)", placeholder="B17")
    with c2:
        section_left = st.text_input(f"Sezione {left.split('—')[0].strip()}", placeholder="25×70")
        section_right = st.text_input(f"Sezione {right.split('—')[0].strip()}", placeholder="30×45")
    with c3:
        diff_type = st.selectbox("Tipo:", ["SECTION_CHANGE", "GEOMETRY_CHANGE", "BEAM_ADDED", "BEAM_REMOVED", "TYPE_CHANGE", "UNRESOLVED"])
    
    note = st.text_input("Nota (opzionale)")
    submitted = st.form_submit_button("Aggiungi")
    
    if submitted and beam_id:
        st.session_state.diffs.append({
            "beam": beam_id,
            f"{left.split('—')[0].strip()}": section_left,
            f"{right.split('—')[0].strip()}": section_right,
            "type": diff_type,
            "note": note,
        })

if st.session_state.diffs:
    st.subheader(f"Differenze registrate ({len(st.session_state.diffs)})")
    for i, d in enumerate(st.session_state.diffs):
        cols = st.columns([1, 2, 2, 2, 2])
        cols[0].write(f"**{d['beam']}**")
        for k, v in d.items():
            if k not in ("beam", "type", "note"):
                cols[1].write(f"{k}: {v}")
        cols[2].write(d["type"])
        cols[3].write(d.get("note", ""))
        if cols[4].button("×", key=f"del_{i}"):
            st.session_state.diffs.pop(i)
            st.rerun()
