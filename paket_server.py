import streamlit as st
import pandas as pd

def render_server_vps():
    st.subheader("Paket Server VPS")

    # ==============================
    # Load Data
    # ==============================
    df = pd.read_csv("data/server_vps_plans.csv")

    # ==============================
    # User Selection: VPS Type & Billing Period
    # ==============================
    group = st.radio(
        "Pilih Jenis VPS:",
        sorted(df["Group"].unique()),
        horizontal=True
    )

    billing = st.radio(
        "Periode Pembayaran",
        ["Bulanan", "Tahunan"],
        horizontal=True
    )

    # ==============================
    # Filter & Compute Pricing
    # ==============================
    df_group = df[df["Group"] == group].copy()

    if billing == "Tahunan":
        df_group["Harga Dasar"] = df_group["Price (IDR)"] * 12
        monitoring_fee = 120_000
        unit_label = "/tahun"
    else:
        df_group["Harga Dasar"] = df_group["Price (IDR)"]
        monitoring_fee = 10_000
        unit_label = "/bulan"

    df_group["Harga + PPN (11%)"] = df_group["Harga Dasar"] * 1.11
    df_group["Harga Total"] = df_group["Harga + PPN (11%)"] + monitoring_fee

    # ==============================
    # Display Table
    # ==============================
    st.dataframe(
        df_group[[
            "Plan", "CPU", "RAM (GB)", "Storage (GB)",
            "Harga Dasar", "Harga + PPN (11%)", "Harga Total"
        ]],
        hide_index=True,
        use_container_width=True
    )

    # ==============================
    # Package Selection
    # ==============================
    plan = st.selectbox("Pilih Paket untuk Perhitungan:", df_group["Plan"].tolist())
    row = df_group[df_group["Plan"] == plan].iloc[0]

    # ==============================
    # Selected Package Display
    # ==============================
    st.markdown("### 💰 Perincian Biaya Bulanan")

    # Horizontal layout: 3 compact metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f"<p style='font-size:14px; margin-bottom:4px;'>Biaya Dasar</p>"
            f"<p style='font-size:18px; font-weight:600;'>Rp {int(base_price):,}/bulan</p>",
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            f"<p style='font-size:14px; margin-bottom:4px;'>Biaya + PPN (11%)</p>"
            f"<p style='font-size:18px; font-weight:600;'>Rp {int(base_price * 1.11):,}/bulan</p>",
            unsafe_allow_html=True
        )
    with col3:
        st.markdown(
            f"<p style='font-size:14px; margin-bottom:4px;'>Biaya + PPN + Monitoring</p>"
            f"<p style='font-size:18px; font-weight:600;'>Rp {int((base_price + 10_000) * 1.11):,}/bulan</p>",
            unsafe_allow_html=True
        )

    # Final total (larger, bold, below)
    st.markdown(
        f"<p style='font-size:15px; margin-top:16px;'>💰 <b>Biaya Total / Final</b></p>"
        f"<h2 style='margin-top:-5px;'>Rp {int((base_price + 10_000) * 1.11):,}/bulan</h2>",
        unsafe_allow_html=True
    )

    st.caption(
        "Biaya sudah termasuk PPN 11% dan biaya monitoring wajib sebesar Rp 10.000 per bulan. "
        "Semua nilai dibulatkan ke ribuan terdekat."
    )
