import streamlit as st
import pandas as pd
import math
import re
from extreme_custom import render_cloud_vps
from paket_server import render_server_vps

# --- Konfigurasi Halaman ---
st.set_page_config(page_title="DLI - Server Estimator", page_icon="💰", layout="centered")

# --- Custom CSS untuk Card & Radio ---
st.markdown("""
    <style>
        .report-card {
            background-color: #ffffff;
            padding: 20px;
            border-radius: 10px;
            border: 1px solid #e0e0e0;
            border-left: 8px solid #28a745;
            margin-top: 20px;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
        }
        .price-container {
            background-color: #f1f8e9;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            margin-top: 15px;
            border: 1px dashed #2e7d32;
        }
        .price-val {
            color: #1b5e20;
            font-size: 30px;
            font-weight: bold;
        }
        .label-text {
            color: #757575;
            font-size: 13px;
            text-transform: uppercase;
            font-weight: bold;
            margin-bottom: 5px;
        }
        /* Style untuk membuat radio button lebih terlihat jelas */
        .stRadio [data-testid="stMarkdownContainer"] p {
            font-size: 16px;
        }
    </style>
""", unsafe_allow_html=True)

# --- Helper Functions ---
def parse_vcpu(value):
    match = re.search(r"(\d+)", str(value))
    return int(match.group(1)) if match else 999 

# --- UI MAIN APP ---
st.title("💰 Kalkulator Biaya Server")
st.caption("Estimasi spesifikasi dan biaya infrastruktur digital — Data Lab Indonesia")

# 1. SMART ESTIMATOR (TOOLTIP)
with st.expander("🔍 Belum tahu butuh spek apa? Gunakan Smart Estimator"):
    mode_est = st.radio("Tipe Produk:", ["Web/Mobile App", "AI Model (LLM)"], horizontal=True)
    if mode_est == "Web/Mobile App":
        c1, c2 = st.columns(2)
        v = c1.number_input("User/Jam:", value=1000)
        d = c2.number_input("Sesi (detik):", value=60)
        cu = (v * d) / 3600
        cpu, ram = max(1, math.ceil(cu/50)), math.ceil(1+(cu*0.032))
        st.info(f"💡 Saran: **{cpu} vCPU / {ram} GB RAM**")
    else:
        p = st.slider("Parameter AI (Billion):", 1, 70, 8)
        st.warning(f"💡 Saran: Minimal GPU dengan **{(p*0.8)+2:.1f} GB VRAM**")

st.divider()

# 2. RADIO BUTTON SELECTION (DATA DARI TABEL REKOMENDASI)
st.subheader("📋 Pilih Paket Rekomendasi")

try:
    # Load Data
    df_rec = pd.read_csv("data/server_recommendation.csv")
    df_rec.columns = df_rec.columns.str.strip()
    
    # Sorting
    df_rec["SortKey"] = df_rec["Specs"].apply(parse_vcpu)
    df_rec = df_rec.sort_values("SortKey").reset_index(drop=True)

    # RADIO BUTTON - Menampilkan Specs dan Use Case
    options = [f"{row['Specs']} — {row['Use Case']}" for _, row in df_rec.iterrows()]
    selected_label = st.radio(
        "Pilih skenario yang sesuai dengan kebutuhan Anda:",
        options=options,
        index=0
    )

    # Ambil data baris yang dipilih
    selected_row = df_rec[df_rec["Specs"] + " — " + df_rec["Use Case"] == selected_label].iloc[0]

    # --- TAMPILAN DETAIL (REPORT CARD) ---
    st.markdown(f"""
    <div class="report-card">
        <div class="label-text">SKENARIO & DESKRIPSI</div>
        <p style="font-size: 18px; margin-bottom: 20px;">
            <strong>{selected_row['Use Case']}</strong>: {selected_row['Description']}
        </p>
        <div style="display: flex; gap: 50px; border-top: 1px solid #eee; padding-top: 15px;">
            <div>
                <div class="label-text">TARGET BEBAN</div>
                <div style="font-size: 16px; font-weight: bold;">{selected_row['Typical Load']}</div>
            </div>
            <div>
                <div class="label-text">STORAGE</div>
                <div style="font-size: 16px; font-weight: bold;">{selected_row['Storage']}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- LOGIKA HARGA OTOMATIS ---
    df_plans = pd.read_csv("data/server_vps_plans.csv")
    nums = re.findall(r"\d+", selected_row['Specs'])
    
    if len(nums) >= 2:
        match = df_plans[(df_plans['CPU'] == int(nums[0])) & (df_plans['RAM (GB)'] == int(nums[1]))]
        if not match.empty:
            price = match.iloc[0]['Price (IDR)']
            st.markdown(f"""
                <div class="price-container">
                    <div class="label-text">ESTIMASI BIAYA BULANAN</div>
                    <div class="price-val">Rp {price:,} <span style="font-size: 14px; font-weight: normal; color: #666;">/ bulan</span></div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.info("💡 Paket ini memerlukan konfigurasi Custom. Cek kalkulator di bawah.")
    else:
        st.warning("🤖 **Infrastruktur AI:** Memerlukan GPU. Hubungi tim DLI untuk penawaran harga.")

except Exception as e:
    st.error(f"Error memuat data: {e}")

st.divider()

# 3. KALKULATOR DETAIL (EXISTING)
st.subheader("⚙️ Kalkulator Biaya Detail (Custom)")
mode = st.radio("Mode Kalkulator:", ["Cloud VPS eXtreme", "Paket Server VPS"], horizontal=True)

if mode == "Cloud VPS eXtreme":
    render_cloud_vps()
else:
    render_server_vps()
