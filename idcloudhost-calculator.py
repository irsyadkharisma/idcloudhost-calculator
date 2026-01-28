import streamlit as st
import pandas as pd
import math
import re
from extreme_custom import render_cloud_vps
from paket_server import render_server_vps

# --- Konfigurasi Halaman ---
st.set_page_config(page_title="DLI - Server Estimator", page_icon="💰", layout="centered")

# --- Fungsi Helper & Logika ---
def parse_vcpu(value):
    """Mengekstrak nilai numerik vCPU untuk pengurutan tabel."""
    match = re.search(r"(\d+)", str(value))
    return int(match.group(1)) if match else 999 

def get_smart_estimate(visitors, duration, is_ai=False, ai_params=0):
    if is_ai:
        vram = (ai_params * 0.8) + 2
        return vram
    else:
        cu = (visitors * duration) / 3600
        cpu = max(1, math.ceil(cu / 50))
        ram = math.ceil(1 + (cu * 0.032))
        return cu, cpu, ram

# --- RENDER: Tabel Rekomendasi (Refined) ---
def render_refined_recommendation():
    st.subheader("📋 Rekomendasi Server & Skenario Penggunaan")
    try:
        df = pd.read_csv("data/server_recommendation.csv")
        df.columns = df.columns.str.strip()

        # MENGGABUNGKAN Use Case dan Description
        df["Skenario Penggunaan"] = "**" + df["Use Case"] + "**: " + df["Description"]

        # Sort berdasarkan vCPU
        df["SortKey"] = df["Specs"].apply(parse_vcpu)
        df = df.sort_values("SortKey")

        # Tampilkan kolom yang diminta
        display_cols = ["Specs", "Storage", "Typical Load", "Skenario Penggunaan"]
        st.dataframe(df[display_cols], use_container_width=True, hide_index=True)
        st.caption("Gunakan tabel di atas sebagai acuan awal sebelum menghitung biaya di bawah.")
    except Exception as e:
        st.error(f"Gagal memuat tabel: {e}")

# --- UI MAIN APP ---
st.title("💰 Kalkulator Biaya Server")
st.caption("Alat bantu estimasi spek dan biaya infrastruktur digital WRI/DLI")

# 1. Smart Estimator Section
with st.expander("🔍 Belum tahu butuh spek apa? Gunakan Smart Estimator", expanded=True):
    mode_est = st.radio("Tipe Produk:", ["Web/Mobile App", "AI Model (LLM)"], horizontal=True)
    
    if mode_est == "Web/Mobile App":
        col1, col2 = st.columns(2)
        visitors = col1.number_input("Estimasi User/Jam:", min_value=0, value=1000)
        duration = col2.number_input("Rata-rata Durasi Sesi (detik):", min_value=1, value=60)
        cu, cpu, ram = get_smart_estimate(visitors, duration)
        st.info(f"💡 **Hasil Estimasi:** Anda butuh sekitar **{cpu} vCPU** dan **{ram} GB RAM**.")
    else:
        params = st.slider("Ukuran Parameter Model AI (Billion):", 1, 70, 8)
        vram = get_smart_estimate(0, 0, is_ai=True, ai_params=params)
        st.warning(f"💡 **Estimasi AI:** Anda butuh GPU dengan minimal **{vram:.1f} GB VRAM**.")

st.divider()

# 2. Tabel Rekomendasi (Sudah Digabung)
render_refined_recommendation()

st.divider()

# 3. Kalkulator Biaya
st.subheader("💵 Hitung Biaya Real")
mode = st.radio("Pilih Kategori Produk:", ["Cloud VPS eXtreme", "Paket Server VPS"], horizontal=True)

if mode == "
