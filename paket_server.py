import streamlit as st
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO

# ============================================================
# Render Function: Server VPS Page
# ============================================================
def render_server_vps():
    # ------------------------------
    # Load data
    # ------------------------------
    df = pd.read_csv("data/server_vps_plans.csv")

    # ------------------------------
    # User selection
    # ------------------------------
    st.markdown("### Pilih Jenis VPS:")
    group = st.radio(
        " ",
        sorted(df["Group"].unique()),
        horizontal=True
    )

    # Descriptions based on selection
    descriptions = {
        "DEDICATED CPU": "💡 Cocok untuk small, medium, dan moderate web/API.",
        "HIGH AVAILABILITY": "💡 Untuk workload yang membutuhkan uptime tinggi dan failover otomatis.",
        "HIGH PERFORMANCE": "💡 Cocok untuk high-load web/API atau sistem dengan intensitas CPU tinggi."
    }

    # Display relevant description if exists
    desc = descriptions.get(group.upper())
    if desc:
        st.caption(desc)

    # ------------------------------
    # Billing period
    # ------------------------------
    billing = st.radio(
        "Periode Pembayaran",
        ["Bulanan", "Tahunan"],
        horizontal=True
    )

    # ------------------------------
    # Filter dataset
    # ------------------------------
    df_group = df[df["Group"] == group].copy()

    if billing == "Tahunan":
        df_group["Biaya Dasar"] = df_group["Price (IDR)"] * 12
        monitoring_fee = 120_000
        unit_label = "/tahun"
    else:
        df_group["Biaya Dasar"] = df_group["Price (IDR)"]
        monitoring_fee = 10_000
        unit_label = "/bulan"

    df_group["Biaya + PPN (11%)"] = df_group["Biaya Dasar"] * 1.11
    df_group["Biaya + PPN + Monitoring"] = df_group["Biaya + PPN (11%)"] + monitoring_fee
    df_group["Biaya Total / Final"] = df_group["Biaya + PPN + Monitoring"]

    # ------------------------------
    # Display table
    # ------------------------------
    st.dataframe(
        df_group[[
            "Plan", "CPU", "RAM (GB)", "Storage (GB)",
            "Biaya Dasar", "Biaya + PPN (11%)", "Biaya + PPN + Monitoring"
        ]],
        hide_index=True,
        use_container_width=True
    )

    # ------------------------------
    # Package selection
    # ------------------------------
    plan = st.selectbox("Pilih Paket untuk Perhitungan:", df_group["Plan"].tolist())
    row = df_group[df_group["Plan"] == plan].iloc[0]

    # ------------------------------
    # Selected Package Display
    # ------------------------------
    st.divider()
    st.markdown("### 💼 Paket Terpilih")
    st.markdown(f"## **{plan}**")

    # 3 compact metrics horizontally
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f"<p style='font-size:14px; margin-bottom:4px;'>Biaya Dasar</p>"
            f"<p style='font-size:18px; font-weight:600;'>Rp {int(row['Biaya Dasar']):,} {unit_label}</p>",
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            f"<p style='font-size:14px; margin-bottom:4px;'>Biaya + PPN (11%)</p>"
            f"<p style='font-size:18px; font-weight:600;'>Rp {int(row['Biaya + PPN (11%)']):,} {unit_label}</p>",
            unsafe_allow_html=True
        )
    with col3:
        st.markdown(
            f"<p style='font-size:14px; margin-bottom:4px;'>Biaya + PPN + Monitoring</p>"
            f"<p style='font-size:18px; font-weight:600;'>Rp {int(row['Biaya + PPN + Monitoring']):,} {unit_label}</p>",
            unsafe_allow_html=True
        )

    # Final total (larger and centered)
    st.markdown(
        f"<div style='text-align:center;'>"
        f"<p style='font-size:15px; margin-top:16px;'>💰 <b>Biaya Total / Final</b></p>"
        f"<h2 style='margin-top:-5px;'>Rp {int(row['Biaya Total / Final']):,} {unit_label}</h2>"
        f"</div>",
        unsafe_allow_html=True
    )

    st.caption(
        "Biaya sudah termasuk PPN 11% dan biaya monitoring wajib Rp 10.000/bulan atau Rp 120.000/tahun."
    )

    # ============================================================
    # PDF EXPORT SECTION
    # ============================================================
    st.divider()
    st.markdown("### 📄 Ekspor Hasil ke PDF")

    if st.button("Export ke PDF"):
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, height - 50, "Perhitungan Paket Server VPS")

        c.setFont("Helvetica", 11)
        c.drawString(50, height - 80, f"Jenis VPS: {group}")
        c.drawString(50, height - 100, f"Periode: {billing}")
        c.drawString(50, height - 120, f"Paket Terpilih: {plan}")

        c.line(50, height - 130, width - 50, height - 130)

        c.drawString(50, height - 150, f"Biaya Dasar: Rp {int(row['Biaya Dasar']):,} {unit_label}")
        c.drawString(50, height - 170, f"Biaya + PPN (11%): Rp {int(row['Biaya + PPN (11%)']):,} {unit_label}")
        c.drawString(50, height - 190, f"Biaya + PPN + Monitoring: Rp {int(row['Biaya + PPN + Monitoring']):,} {unit_label}")
        c.drawString(50, height - 210, f"Biaya Total / Final: Rp {int(row['Biaya Total / Final']):,} {unit_label}")

        c.setFont("Helvetica-Oblique", 9)
        c.drawString(50, 60, "Laporan ini dihasilkan otomatis dari kalkulator internal IDCloudHost.")
        c.drawString(50, 45, "Termasuk PPN 11% dan biaya monitoring wajib.")

        c.showPage()
        c.save()

        st.download_button(
            label="📥 Unduh PDF",
            data=buffer.getvalue(),
            file_name=f"Paket_{plan.replace(' ', '_')}.pdf",
            mime="application/pdf"
        )
