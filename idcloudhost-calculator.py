import streamlit as st
import math
from extreme_custom import render_cloud_vps
from paket_server import render_server_vps
from pages.server_recommendation import render_server_recommendation

# --- Konfigurasi Halaman ---
st.set_page_config(page_title="JUBX - Server Estimator", page_icon="💰", layout="centered")

# --- Logika Estimasi (Refined) ---
def get_smart_estimate(visitors, duration, is_ai=False, ai_params=0):
    if is_ai:
        vram = (ai_params * 0.8) + 2
        return vram
    else:
        cu = (visitors * duration) / 3600
        cpu = max(1, math.ceil(cu / 50))
        ram = math.ceil(1 + (cu * 0.032))
        return cu, cpu, ram

# --- UI Header ---
st.title("💰 Smart Infrastructure Calculator")
st.caption("Alat bantu estimasi spek dan biaya untuk ekosistem JUBX")

# --- Bagian 1: Smart Estimator (Fitur Baru) ---
with st.expander("🔍 Belum tahu butuh spek apa? Gunakan Smart Estimator", expanded=True):
    mode_est = st.radio("Tipe Produk:", ["Web/Mobile App", "AI Model (LLM)"], horizontal=True)
    
    if mode_est == "Web/Mobile App":
        col1, col2 = st.columns(2)
        visitors = col1.number_input("Estimasi User/Jam:", value=1000)
        duration = col2.number_input("Rata-rata Durasi Sesi (detik):", value=60)
        cu, cpu, ram = get_smart_estimate(visitors, duration)
        st.info(f"💡 Hasil Estimasi: Anda butuh sekitar **{cpu} vCPU** dan **{ram} GB RAM** (untuk ~{math.ceil(cu)} concurrent users).")
    else:
        params = st.slider("Ukuran Parameter Model AI (Billion):", 1, 70, 8)
        vram = get_smart_estimate(0, 0, is_ai=True, ai_params=params)
        st.warning(f"💡 Estimasi AI: Anda butuh GPU dengan minimal **{vram:.1f} GB VRAM**.")

st.divider()

# --- Bagian 2: Tabel Rekomendasi Asli ---
render_server_recommendation()

# --- Bagian 3: Kalkulator Biaya Asli ---
st.subheader("Kalkulator Biaya VPS")
mode = st.radio("Pilih Kategori Produk:", ["Cloud VPS eXtreme", "Paket Server VPS"], horizontal=True)

if mode == "Cloud VPS eXtreme":
    render_cloud_vps()
else:
    render_server_vps()
