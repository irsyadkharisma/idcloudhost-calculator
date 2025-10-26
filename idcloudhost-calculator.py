import streamlit as st
import pandas as pd
from extreme_custom import render_cloud_vps
from paket_server import render_server_vps

st.set_page_config(page_title="Kalkulator dan Paket Server", page_icon="💰", layout="centered")
st.title("💰 Paket Server untuk Produk Internal")
st.caption("Digunakan sebagai basis perhitungan biaya acuan awal")

# ------------------------------
# Show server recommendation table first
# ------------------------------
st.subheader("Rekomendasi Server Berdasarkan Penggunaan")

try:
    df = pd.read_csv("data/server_recommendation.csv")
    order = [
        "Staging / Testing",
        "Personal Blog / Portfolio",
        "Company Profile",
        "Small Web App / Login",
        "Business / E-Commerce",
        "Corporate / API Gateway",
        "High-Traffic / API",
        "AI / ML Apps"
    ]
    df["Use Case"] = pd.Categorical(df["Use Case"], categories=order, ordered=True)
    df = df.sort_values("Use Case")

    st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption("Gunakan tabel di atas sebagai acuan awal sebelum menghitung biaya VPS yang sesuai.")
except Exception as e:
    st.error(f"Gagal memuat data rekomendasi: {e}")

st.divider()

# ------------------------------
# VPS Calculator section
# ------------------------------
st.subheader("Kalkulator VPS dan Paket Server")

mode = st.radio("Pilih Kategori Produk:", ["Cloud VPS eXtreme", "Server VPS"], horizontal=True)

if mode == "Cloud VPS eXtreme":
    render_cloud_vps()
else:
    render_server_vps()
