import streamlit as st
import pandas as pd

def render_server_vps():
    st.subheader("Paket Server VPS")

    df = pd.read_csv("data/server_vps_plans.csv")

    group = st.radio(
        "Pilih Jenis VPS:",
        sorted(df["Group"].unique()),
        horizontal=True
    )
    billing = st.radio("Periode Pembayaran", ["Bulanan", "Tahunan"], horizontal=True)

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

    st.dataframe(df_group[["Plan", "CPU", "RAM (GB)", "Storage (GB)", "Harga Dasar", "Harga + PPN (11%)", "Harga Total"]],hide_index=True, use_container_width=True)

    plan = st.selectbox("Pilih Paket untuk Perhitungan:", df_group["Plan"].tolist())
    row = df_group[df_group["Plan"] == plan].iloc[0]

    st.divider()
    st.markdown("### 💼 Paket Terpilih")
    st.markdown(f"## **{plan}**")
    st.metric("Harga Dasar", f"Rp {int(row['Harga Dasar']):,} {unit_label}")
    st.metric("Harga + PPN (11%)", f"Rp {int(row['Harga + PPN (11%)']):,} {unit_label}")
    st.metric("🧾 Total Harga (termasuk Monitoring)", f"Rp {int(row['Harga Total']):,} {unit_label}")
