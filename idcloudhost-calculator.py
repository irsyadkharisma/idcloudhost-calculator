import streamlit as st
import math
from extreme_custom import render_cloud_vps
from paket_server import render_server_vps
from pages.server_recommendation import render_server_recommendation

# --- Konfigurasi Halaman ---
st.set_page_config(page_title="DLI - Server Estimator", page_icon="💰", layout="centered")

# --- Logika Estimasi (Refined) ---
def get_smart_estimate(visitors, duration, is_ai=False, ai_params=0):
    if is_ai:
        # Estimasi VRAM untuk 4-bit quantization + overhead
        vram = (ai_params * 0.8) + 2
        return vram
    else:
        # Menghitung Concurrent Users (CU)
        cu = (visitors * duration) / 3600
        # 1 vCPU per 50 concurrent users (asumsi general)
        cpu = max(1, math.ceil(cu / 50))
        # 1GB OS + 32MB per concurrent user
        ram = math.ceil(1 + (cu * 0.032))
        return cu, cpu, ram

# --- UI Header ---
st.title("💰 Kalkulator Biaya Server")
st.caption("Alat bantu estimasi spek dan biaya infrastruktur digital")

# --- Bagian 1: Smart Estimator ---
with st.expander("🔍 Belum tahu butuh spek apa? Gunakan Smart Estimator", expanded=True):
    mode_est = st.radio("Tipe Produk:", ["Web/Mobile App", "AI Model (LLM)"], horizontal=True)
    
    if mode_est == "Web/Mobile App":
        col1, col2 = st.columns(2)
        visitors = col1.number_input("Estimasi User/Jam:", min_value=0, value=1000)
        duration = col2.number_input("Rata-rata Durasi Sesi (detik):", min_value=1, value=60)
        cu, cpu, ram = get_smart_estimate(visitors, duration)
        
        st.info(f"💡 **Hasil Estimasi:** Anda membutuhkan sekitar **{cpu} vCPU** dan **{ram} GB RAM** untuk melayani ~{math.ceil(cu)} pengguna bersamaan (*concurrent users*).")
    else:
        params = st.slider("Ukuran Parameter Model AI (Billion):", 1, 70, 8)
        vram = get_smart_estimate(0, 0, is_ai=True, ai_params=params)
        
        st.warning(f"💡 **Estimasi AI:** Untuk model {params}B, Anda membutuhkan GPU dengan minimal **{vram:.1f} GB VRAM**.")

st.divider()

# --- Bagian 2: Tabel Rekomendasi (Dari pages/server_recommendation.py) ---
render_server_recommendation()

# --- Bagian 3: Kalkulator Biaya Utama ---
st.subheader("Kalkulator Biaya VPS")
mode = st.radio("Pilih Kategori Produk:", ["Cloud VPS eXtreme", "Paket Server VPS"], horizontal=True)

if mode == "Cloud VPS eXtreme":
    render_cloud_vps()
else:
    render_server_vps()
