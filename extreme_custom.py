import streamlit as st
import json
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO

# ============================================================
# Function: Cloud VPS Price Calculation
# ============================================================
def calculate_cloud_vps(cpu, ram, storage, coef):
    per_hour = (
        (cpu * coef["cpuram1"] if cpu <= 2 else cpu * coef["cpuram2"])
        + (ram * coef["cpuram1"] if ram <= 2 else ram * coef["cpuram2"])
        + (storage * coef["storage1"] if storage < 81 else storage * coef["storage2"])
    )
    per_month = per_hour * 730
    return int(1000 * round(per_month / 1000))


# ============================================================
# Render Function: Cloud VPS Page
# ============================================================
def render_cloud_vps():
    st.subheader("Cloud VPS eXtreme Custom")

    # ------------------------------
    # Load coefficient data
    # ------------------------------
    with open("data/cloud_vps_coeff.json") as f:
        cloud_vps_data = json.load(f)

    # ------------------------------
    # Package selector
    # ------------------------------
    variant = st.radio("Pilih Varian Paket", list(cloud_vps_data.keys()), horizontal=False)

    col1, col2, col3 = st.columns(3)
    with col1:
        cpu = st.slider("CPU (Core)", 2, 10, 2)
    with col2:
        ram = st.slider("RAM (GB)", 2, 10, 2)
    with col3:
        storage = st.slider("Storage (GB)", 20, 500, 20, step=10)

    # ------------------------------
    # Price calculation
    # ------------------------------
    coef = cloud_vps_data[variant]
    base_price = calculate_cloud_vps(cpu, ram, storage, coef)
    monitoring_fee = 10_000
    vat_price = base_price * 1.11
    total_price = (base_price + monitoring_fee) * 1.11
    unit_label = "/bulan"

    # ------------------------------
    # Display pricing
    # ------------------------------
    st.markdown("### 💰 Perincian Biaya Bulanan")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f"<p style='font-size:14px; margin-bottom:4px;'>Biaya Dasar</p>"
            f"<p style='font-size:18px; font-weight:600;'>Rp {int(base_price):,}{unit_label}</p>",
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            f"<p style='font-size:14px; margin-bottom:4px;'>Biaya + PPN (11%)</p>"
            f"<p style='font-size:18px; font-weight:600;'>Rp {int(vat_price):,}{unit_label}</p>",
            unsafe_allow_html=True
        )
    with col3:
        st.markdown(
            f"<p style='font-size:14px; margin-bottom:4px;'>Biaya + PPN + Monitoring</p>"
            f"<p style='font-size:18px; font-weight:600;'>Rp {int(total_price):,}{unit_label}</p>",
            unsafe_allow_html=True
        )

    # Final total (larger, centered)
    st.markdown(
        f"<div style='text-align:center;'>"
        f"<p style='font-size:15px; margin-top:16px;'>💰 <b>Biaya Total / Final</b></p>"
        f"<h2 style='margin-top:-5px;'>Rp {int(total_price):,}{unit_label}</h2>"
        f"</div>",
        unsafe_allow_html=True
    )

    st.caption(
        "Biaya sudah termasuk PPN 11% dan biaya monitoring wajib sebesar Rp 10.000 per bulan. "
        "Semua nilai dibulatkan ke ribuan terdekat."
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
        c.drawString(50, height - 50, "Laporan Perhitungan Cloud VPS eXtreme")

        c.setFont("Helvetica", 11)
        c.drawString(50, height - 80, f"Varian Paket: {variant}")
        c.drawString(50, height - 100, f"CPU: {cpu} Core, RAM: {ram} GB, Storage: {storage} GB")

        c.line(50, height - 110, width - 50, height - 110)

        c.drawString(50, height - 130, f"Biaya Dasar: Rp {int(base_price):,}{unit_label}")
        c.drawString(50, height - 150, f"Biaya + PPN (11%): Rp {int(vat_price):,}{unit_label}")
        c.drawString(50, height - 170, f"Biaya + PPN + Monitoring: Rp {int(total_price):,}{unit_label}")
        c.drawString(50, height - 190, f"Biaya Total / Final: Rp {int(total_price):,}{unit_label}")

        c.setFont("Helvetica-Oblique", 9)
        c.drawString(50, 60, "Laporan ini dihasilkan otomatis dari kalkulator internal IDCloudHost.")
        c.drawString(50, 45, "Termasuk PPN 11% dan biaya monitoring wajib Rp 10.000/bulan.")

        c.showPage()
        c.save()

        st.download_button(
            label="📥 Unduh PDF",
            data=buffer.getvalue(),
            file_name=f"CloudVPS_{variant.replace(' ', '_')}.pdf",
            mime="application/pdf"
        )
