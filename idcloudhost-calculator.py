import streamlit as st
import pandas as pd
import math
import re
from extreme_custom import render_cloud_vps
from paket_server import render_server_vps

# --- Konfigurasi Halaman ---
st.set_page_config(page_title="DLI - Server Estimator", page_icon="💰", layout="centered")

# --- Fungsi Helper ---
def parse_vcpu(value):
    """Mengekstrak angka vCPU untuk pengurutan."""
    match = re.search(r"(\d+)", str(value))
    return int(match.group(1)) if match else 999 

def get_smart_estimate(visitors, duration, is_ai=False, ai_params=0):
    if is_ai:
        return (ai_params * 0.8) + 2 # Estimasi VRAM
    else:
        cu = (visitors * duration) / 3600
        cpu = max(1, math.ceil(cu / 50))
        ram = math.ceil(1 + (cu * 0.032))
        return cu, cpu, ram

# --- UI MAIN APP ---
st.title("💰 Kalkulator Biaya Server")
st.caption("Alat bantu estimasi spek dan biaya infrastruktur digital WRI/DLI")

# 1. SMART ESTIMATOR (TOOLTIP)
with st.expander("🔍 Belum tahu butuh spek apa? Gunakan Smart Estimator", expanded=False):
    mode_est = st.radio("Tipe Produk:", ["Web/Mobile App", "AI Model (LLM)"], horizontal=True)
    if mode_est == "Web/Mobile App":
        c1, c2 = st.columns(2)
        v = c1.number_input("User/Jam:", value=1000)
        d = c2.number_input("Durasi Sesi (detik):", value=60)
        cu, cpu, ram = get_smart_estimate(v, d)
        st.info(f"💡 Saran: **{cpu} vCPU / {ram} GB RAM** (untuk ~{math.ceil(cu)} concurrent users).")
    else:
        p = st.slider("Parameter AI (Billion):", 1, 70, 8)
        st.warning(f"💡 Saran: Minimal GPU dengan **{get_smart_estimate(0,0,True,p):.1f} GB VRAM**.")

st.divider()

# 2. TABEL REKOMENDASI INTERAKTIF + RADIO
st.subheader("📋 Pilih Skenario Penggunaan")

try:
    # Load Data
    df_rec = pd.read_csv("data/server_recommendation.csv")
    df_rec.columns = df_rec.columns.str.strip()
    
    # Gabungkan Use Case & Description (Sesuai Permintaan)
    df_rec["Skenario"] = "**" + df_rec["Use Case"] + "**: " + df_rec["Description"]
    
    # Sort
    df_rec["SortKey"] = df_rec["Specs"].apply(parse_vcpu)
    df_rec = df_rec.sort_values("SortKey").reset_index(drop=True)

    # Tampilkan Tabel Statis (Sebagai Referensi Cepat)
    st.dataframe(df_rec[["Specs", "Storage", "Typical Load", "Skenario"]], 
                 use_container_width=True, hide_index=True)

    # Radio Button untuk Memilih Spek & Menampilkan Harga
    st.markdown("#### Hitung Cepat Harga Berdasarkan Tabel:")
    selected_idx = st.selectbox(
        "Pilih Spesifikasi dari tabel di atas:",
        options=df_rec.index,
        format_func=lambda x: f"{df_rec.loc[x, 'Specs']} — {df_rec.loc[x, 'Use Case']}"
    )

    # LOGIKA HARGA (Mencari di server_vps_plans.csv)
    df_plans = pd.read_csv("data/server_vps_plans.csv")
    sel = df_rec.loc[selected_idx]
    
    # Parsing angka CPU dan RAM dari string "2 vCPU / 4 GB"
    nums = re.findall(r"\d+", sel['Specs'])
    if len(nums) >= 2:
        match = df_plans[(df_plans['CPU'] == int(nums[0])) & (df_plans['RAM (GB)'] == int(nums[1]))]
        if not match.empty:
            price = match.iloc[0]['Price (IDR)']
            st.success(f"### 💵 Estimasi Biaya: Rp {price:,} / Bulan")
            st.caption(f"Spek: {sel['Specs']} | Storage: {sel['Storage']} | Beban: {sel['Typical Load']}")
        else:
            st.info("💡 Spek khusus. Silakan cek detail di Kalkulator eXtreme di bawah.")
    else:
        st.warning("🤖 Hubungi tim DLI untuk penawaran infrastruktur AI/GPU.")

except Exception as e:
    st.error(f"Terjadi kesalahan: {e}")

st.divider()

# 3. KALKULATOR DETAIL (EXISTING)
st.subheader("⚙️ Kalkulator Biaya Detail (Custom)")
mode = st.radio("Pilih Tipe Perhitungan:", ["Cloud VPS eXtreme", "Paket Server VPS"], horizontal=True)

if mode == "Cloud VPS eXtreme":
    render_cloud_vps()
else:
    render_server_vps()
