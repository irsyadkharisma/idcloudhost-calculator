import streamlit as st
from extreme_custom import render_cloud_vps
from paket_server import render_server_vps
from pages.server_recommendation import render_server_recommendation

st.set_page_config(page_title="Kalkulator dan Paket Server", page_icon="💰", layout="centered")
st.markdown("""
    <style>
        /* make content area wider, but keep margins */
        .block-container {
            max-width: 1200px;   /* default ~700px, "wide" is ~1800px */
            padding-left: 3rem;
            padding-right: 3rem;
        }
    </style>
""", unsafe_allow_html=True)

st.title("💰 Paket Server untuk Produk Internal")
st.caption("Digunakan sebagai basis perhitungan biaya acuan awal")

# --- Show Recommendation Table ---
render_server_recommendation()

# --- VPS Calculator Section ---
st.subheader("Kalkulator VPS dan Paket Server")

mode = st.radio("Pilih Kategori Produk:", ["Cloud VPS eXtreme", "Paket Server VPS"], horizontal=True)

if mode == "Cloud VPS eXtreme":
    render_cloud_vps()
else:
    render_server_vps()
