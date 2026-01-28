import streamlit as st
import pandas as pd
import math
import re
from extreme_custom import render_cloud_vps
from paket_server import render_server_vps

# --- Konfigurasi Halaman ---
st.set_page_config(page_title="DLI - Server Estimator", page_icon="💰", layout="centered")

# --- Custom Styling (Agar Mirip Gambar ke-2) ---
st.markdown("""
    <style>
        .report-card {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            border-left: 10px solid #007bff;
            margin-bottom: 20px;
        }
        .price-text {
            color: #28a745;
            font-size: 32px;
            font-weight: bold;
        }
        .spec-label {
            color: #6c757d;
            font-size: 14px;
            margin-bottom: 0px;
        }
    </style>
""", unsafe_allow_html=True)

# --- Helper Functions ---
def parse_vcpu(value):
    match = re.search(r"(\d+)", str(value))
    return int(match.group(1)) if match else 999 

# --- UI MAIN APP ---
st.title("💰 Kalkulator Biaya Server")
st.caption("Estimasi spesifikasi dan biaya infrastruktur digital — WRI / Data Lab Indonesia")

# 1. Bagian Dropdown Rekomendasi
st.subheader("📋 Pilih Skenario Penggunaan")

try:
    # Load Data Rekomendasi
    df_rec = pd.read_csv("data/server_recommendation.csv")
    df_rec.columns = df_rec.columns.str.strip()
    
    # Sort data agar rapi
    df_rec["SortKey"] = df_rec["Specs"].apply(parse_vcpu)
    df_rec = df_rec.sort_values("SortKey").reset_index(drop=True)

    # DROPDOWN (Selectbox) - Sesuai permintaan Anda
    options = [f"{row['Specs']} — {row['Use Case']}" for _, row in df_rec.iterrows()]
    selected_option = st.selectbox("Pilih kebutuhan server Anda:", options)

    # Ambil data yang dipilih
    selected_row = df_rec[df_rec["Specs"] + " — " + df_rec["Use Case"] == selected_option].iloc[0]

    # TAMPILKAN INFORMASI SEPERTI GAMBAR KE-2
    st.markdown(f"""
    <div class="report-card">
        <p class="spec-label">SKENARIO PENGGUNAAN</p>
        <p style="font-size: 18px; font-weight: bold; margin-bottom: 15px;">
            {selected_row['Use Case']}: {selected_row['Description']}
        </p>
        <div style="display: flex; justify-content: space-between; border-top: 1px solid #dee2e6; pt-3;">
            <div style="flex: 1;">
                <p class="spec-label">TARGET BEBAN</p>
                <p><b>{selected_row['Typical Load']}</b></p>
            </div>
            <div style="flex: 1;">
                <p class="spec-label">STORAGE</p>
                <p><b>{selected_row['Storage']}</b></p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. LOGIKA HARGA OTOMATIS
    df_plans = pd.read_csv("data/server_vps_plans.csv")
    nums = re.findall(r"\d+", selected_row['Specs'])
    
    if len(nums) >= 2:
        # Cari di data harga berdasarkan CPU dan RAM
        match = df_plans[(df_plans['CPU'] == int(nums[0])) & (df_plans['RAM (GB)'] == int(nums[1]))]
        if not match.empty:
            price = match.iloc[0]['Price (IDR)']
            st.markdown(f"""
                <div style="text-align: center; padding: 15px; background: #e9ecef; border-radius: 8px;">
                    <p style="margin-bottom: 0; font-size: 14px;">Estimasi Biaya Mulai Dari:</p>
                    <p class="price-text">Rp {price:,} <span style="font-size: 16px; color: #666;">/ bulan</span></p>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.info("💡 Spek ini memerlukan konfigurasi Custom. Silakan cek kalkulator di bawah.")
    else:
        st.warning("🤖 **AI/GPU Apps:** Memerlukan infrastruktur khusus. Hubungi tim DLI untuk penawaran.")

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
