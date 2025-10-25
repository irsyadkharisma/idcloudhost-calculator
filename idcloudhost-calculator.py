import streamlit as st
from extreme-custom import render_cloud_vps
from paket-server import render_server_vps

st.set_page_config(page_title="Kalkulator dan Paket Server", page_icon="💰", layout="centered")
st.title("💰 Paket server untuk produk internal")
st.caption("Digunakan sebagai basis perhitungan biaya acuan awal")

mode = st.radio("Pilih Kategori Produk:", ["Cloud VPS eXtreme", "Server VPS"], horizontal=True)

if mode == "Cloud VPS eXtreme":
    render_cloud_vps()
else:
    render_server_vps()
    