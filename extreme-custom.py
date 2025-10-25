import streamlit as st
import json

def calculate_cloud_vps(cpu, ram, storage, coef):
    per_hour = (
        (cpu * coef["cpuram1"] if cpu <= 2 else cpu * coef["cpuram2"])
        + (ram * coef["cpuram1"] if ram <= 2 else ram * coef["cpuram2"])
        + (storage * coef["storage1"] if storage < 81 else storage * coef["storage2"])
    )
    per_month = per_hour * 730
    return int(1000 * round(per_month / 1000))

def render_cloud_vps():
    st.subheader("Cloud VPS eXtreme Custom")

    with open("data/cloud_vps_coeff.json") as f:
        cloud_vps_data = json.load(f)

    variant = st.radio("Pilih Varian Paket", list(cloud_vps_data.keys()), horizontal=False)

    col1, col2, col3 = st.columns(3)
    with col1:
        cpu = st.slider("CPU (Core)", 2, 10, 2)
    with col2:
        ram = st.slider("RAM (GB)", 2, 10, 2)
    with col3:
        storage = st.slider("Storage (GB)", 20, 500, 20, step=10)

    coef = cloud_vps_data[variant]
    base_price = calculate_cloud_vps(cpu, ram, storage, coef)
    total_price = (base_price + 10_000) * 1.11

    st.markdown("### 💰 Perincian Biaya Bulanan")
    st.metric("Harga Dasar", f"Rp {int(base_price):,}/bulan")
    st.metric("Harga + PPN 11%", f"Rp {int(base_price * 1.11):,}/bulan")
    st.metric("Harga Total (PPN + Monitoring)", f"Rp {int(total_price):,}/bulan")
    
