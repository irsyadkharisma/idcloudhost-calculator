import streamlit as st
import pandas as pd
import math
import re
from extreme_custom import render_cloud_vps
from paket_server import render_server_vps

# --- Konfigurasi Halaman ---
st.set_page_config(page_title="DLI - Server Estimator", page_icon="💰", layout="centered")

# --- CSS Custom untuk Tampilan Lebih Bersih ---
st.markdown("""
    <style>
        .block-container { max-width: 1000px; padding-top: 2rem; }
        .stRadio [data-testid="stMarkdownContainer"] p { font-size: 15px; font-weight: 500; }
        .price-box { 
            padding: 20px; 
            border-radius: 10px; 
            background-color: #f0f2f6; 
            border-left: 5px solid #00c853;
            margin: 10px 0;
        }
    </style>
""", unsafe_allow_html=True)

# --- Fungsi Helper ---
def parse_vcpu(value):
    match = re.search(r"(\d+)", str(value))
    return int(match.group(1)) if match else 999 

def get_smart_estimate(visitors, duration, is_ai=False, ai_params=0):
    if is_ai:
        return (ai_params * 0.8) + 2 
    else:
        cu = (visitors * duration) / 3600
        cpu = max(1, math.ceil(cu / 50))
        ram = math.ceil(1 + (cu * 0.032))
        return cu, cpu, ram

# --- MAIN UI ---
st.title("💰 Kalkulator Biaya Server")
st.caption("Estimasi spesifikasi dan biaya infrastruktur digital — Data Lab Indonesia (DLI)")

# 1. SMART ESTIMATOR (TOOLTIP)
with st.expander("🔍 Belum tahu butuh spek apa? Gunakan Smart Estimator"):
    mode_est = st.radio("Tipe Produk:", ["Web/Mobile App", "AI Model (LLM)"], horizontal=True)
    if mode_est == "Web/Mobile App":
        c1, c2 = st.columns(2)
        v = c1.number_input("User per Jam:", value=1000)
        d = c2.number_input("Durasi Sesi (detik):", value=60)
        cu, cpu, ram = get_smart_estimate(v, d)
        st.info(f"💡 Saran: **{cpu} vCPU / {ram} GB RAM** (untuk ~{math.ceil(cu)} concurrent users).")
    else:
        p = st.slider("Parameter AI (Billion):", 1, 70, 8)
        st.warning(f"💡 Saran: Minimal GPU dengan **{get_smart_estimate(0,0,True,p):.1f} GB VRAM**.")

st.divider()

# 2. REKOMENDASI INTERAKTIF DENGAN RADIO BUTTON
st.subheader("📋 Pilih Skenario & Cek Harga Instan")

try:
    # Load Data
    df_rec = pd.read_csv("data/server_recommendation.csv")
    df_rec.columns = df_rec.columns.str.strip()
    
    # Gabungkan Use Case & Description (Sesuai Permintaan)
    # Menggunakan baris baru (\n) untuk pemisahan yang jelas
    df_rec["Skenario"] = df_rec["Use Case"] + "\n\n" + df_rec["Description"]
    
    # Sorting
    df_rec["SortKey"] = df_rec["Specs"].apply(parse_vcpu)
    df_rec = df_rec.sort_values("SortKey").reset_index(drop=True)

    # Tampilan Tabel Referensi (Opsi: Bisa disembunyikan jika ingin fokus ke Radio)
    with st.expander("Lihat Tabel Perbandingan Spek"):
        st.table(df_rec[["Specs", "Typical Load", "Use Case"]])

    # RADIO BUTTON UNTUK PILIHAN
    st.markdown("#### Pilih Paket Rekomendasi:")
    # Membuat label yang informatif untuk radio button
    choice_labels = [f"{row['Specs']} — {row['Use Case']}" for _, row in df_rec.iterrows()]
    
    selected_label = st.radio(
        "Gunakan opsi ini untuk melihat estimasi biaya cepat:",
        options=choice_labels,
        index=0
    )

    # Ambil data berdasarkan pilihan radio
    selected_row = df_rec[df_rec["Specs"] + " — " + df_rec["Use Case"] == selected_label].iloc[0]

    # TAMPILKAN HARGA DI BAWAH RADIO
    st.markdown(f"**Detail Skenario:** \n{selected_row['Description']}")
    
    # Logika Pencarian Harga ke server_vps_plans.csv
    df_plans = pd.read_csv("data/server_vps_plans.csv")
    nums = re.findall(r"\d+", selected_row['Specs'])
    
    if len(nums) >= 2:
        match = df_plans[(df_plans['CPU'] == int(nums[0])) & (df_plans['RAM (GB)'] == int(nums[1]))]
        if not match.empty:
            price = match.iloc[0]['Price (IDR)']
            st.markdown(f"""
                <div class="price-box">
                    <span style="font-size: 14px; color: #555;">Estimasi Biaya Bulanan:</span><br>
                    <span style="font-size: 28px; font-weight: bold; color: #1b5e20;">Rp {price:,}</span>
                    <span style="font-size: 14px; color: #555;"> / bulan</span>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.info("💡 Spek ini memerlukan konfigurasi custom. Silakan cek kalkulator di bawah.")
    else:
        st.warning("🤖 **AI/GPU Apps:** Memerlukan GPU khusus. Silakan hubungi tim DLI untuk penawaran harga.")

except Exception as e:
    st.error(f"Gagal memuat data: {e}")

st.divider()

# 3. KALKULATOR DETAIL (EXISTING)
st.subheader("⚙️ Kalkulator Biaya Detail (Custom)")
mode = st.radio("Pilih Tipe Perhitungan:", ["Cloud VPS eXtreme", "Paket Server VPS"], horizontal=True)

if mode == "Cloud VPS eXtreme":
    render_cloud_vps()
else:
    render_server_vps()
