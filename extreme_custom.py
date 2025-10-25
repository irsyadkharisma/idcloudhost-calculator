import streamlit as st
import json

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

    # ==============================
    # Load Coefficients
    # ==============================
    with open("data/cloud_vps_coeff.json") as f:
        cloud_vps_data = json.load(f)

    # ==============================
    # Variant and Spec Selection
    # ==============================
    variant = st.radio("Pilih Varian Paket", list(cloud_vps_data.keys()), horizontal=False)

    col1, col2, col3 = st.columns(3)
    with col1:
        cpu = st.slider("CPU (Core)", 2, 10, 2)
    with col2:
        ram = st.slider("RAM (GB)", 2, 10, 2)
    with col3:
        storage = st.slider("Storage (GB)", 20, 500, 20, step=10)

    # ==============================
    # Pricing Calculation
    # ==============================
    coef = cloud_vps_data[variant]
    base_price = calculate_cloud_vps(cpu, ram, storage, coef)
    monitoring_fee = 10_000
    vat_price = base_price * 1.11
    total_price = (base_price + monitoring_fee) * 1.11

    # ==============================
    # Selected Package Display
    # ==============================
    st.markdown("### 💰 Perincian Biaya Bulanan")

    # Side-by-side small font layout
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            f"<p style='font-size:14px; margin-bottom:4px;'>Harga Dasar</p>"
            f"<p style='font-size:18px; font-weight:600;'>Rp {int(base_price):,}/bulan</p>",
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            f"<p style='font-size:14px; margin-bottom:4px;'>Harga + PPN (11%)</p>"
            f"<p style='font-size:18px; font-weight:600;'>Rp {int(vat_price):,}/bulan</p>",
            unsafe_allow_html=True
        )

    # Final total below
    st.markdown(
        f"<p style='font-size:15px; margin-top:16px;'>🧾 <b>Total Harga (termasuk Monitoring)</b></p>"
        f"<h2 style='margin-top:-5px;'>Rp {int(total_price):,}/bulan</h2>",
        unsafe_allow_html=True
    )

    st.caption(
        "Harga sudah termasuk PPN 11% dan biaya monitoring wajib sebesar Rp 10.000 per bulan. "
        "Semua nilai dibulatkan ke ribuan terdekat."
    )
