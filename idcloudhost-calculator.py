import streamlit as st
import pandas as pd

# ------------------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------------------
st.set_page_config(page_title="IDCloudHost Full Pricing Calculator", page_icon="💰", layout="centered")
st.title("💰 IDCloudHost Pricing Calculator (Cloud VPS & Server VPS)")
st.caption("Dynamic pricing calculator for Cloud VPS eXtreme and Server VPS packages with 11% VAT and optional monitoring add-on.")

# ============================================================
# SECTION 1: DATA & FORMULAS
# ============================================================

# Cloud VPS coefficients (from idcloudhost JS)
CLOUD_COEFFICIENTS = {
    "Basic Standard": {"cpuram1": 25.685, "cpuram2": 51.37, "storage1": 0.856, "storage2": 1.712},
    "Intel eXtreme": {"cpuram1": 36.0, "cpuram2": 55.0, "storage1": 3.0, "storage2": 4.0},
    "AMD eXtreme": {"cpuram1": 36.0, "cpuram2": 59.0, "storage1": 3.0, "storage2": 4.0},
}


def calculate_cloud_vps(cpu: int, ram: int, storage: int, coef: dict) -> dict:
    """Replicate the official JS pricing formula for Cloud VPS."""
    per_hour = (
        (cpu * coef["cpuram1"] if cpu <= 2 else cpu * coef["cpuram2"])
        + (ram * coef["cpuram1"] if ram <= 2 else ram * coef["cpuram2"])
        + (storage * coef["storage1"] if storage < 81 else storage * coef["storage2"])
    )
    per_month = per_hour * 730
    per_month_rounded = 1000 * round(per_month / 1000)
    return {"per_hour": round(per_hour), "per_month": int(per_month_rounded)}


# Server VPS pricing data
SERVER_VPS = {
    "HIGH PERFORMANCE": [
        {"Plan": "NVME 1", "CPU": 1, "RAM (GB)": 1, "Storage (GB)": 25, "Price (IDR)": 112_000},
        {"Plan": "NVME 2", "CPU": 1, "RAM (GB)": 2, "Storage (GB)": 30, "Price (IDR)": 180_000},
        {"Plan": "NVME 3", "CPU": 2, "RAM (GB)": 2, "Storage (GB)": 40, "Price (IDR)": 270_000},
        {"Plan": "NVME 4", "CPU": 2, "RAM (GB)": 4, "Storage (GB)": 80, "Price (IDR)": 360_000},
        {"Plan": "NVME 5", "CPU": 4, "RAM (GB)": 8, "Storage (GB)": 140, "Price (IDR)": 700_000},
        {"Plan": "NVME 6", "CPU": 4, "RAM (GB)": 12, "Storage (GB)": 200, "Price (IDR)": 1_050_000},
        {"Plan": "NVME 7", "CPU": 8, "RAM (GB)": 16, "Storage (GB)": 250, "Price (IDR)": 1_400_000},
        {"Plan": "NVME 8", "CPU": 12, "RAM (GB)": 24, "Storage (GB)": 350, "Price (IDR)": 2_100_000},
        {"Plan": "NVME 9", "CPU": 16, "RAM (GB)": 32, "Storage (GB)": 400, "Price (IDR)": 3_600_000},
        {"Plan": "NVME 10", "CPU": 32, "RAM (GB)": 64, "Storage (GB)": 500, "Price (IDR)": 5_500_000},
    ],
    "DEDICATED CPU": [
        {"Plan": "eXtreme 1", "CPU": 1, "RAM (GB)": 1, "Storage (GB)": 25, "Price (IDR)": 112_000},
        {"Plan": "eXtreme 2", "CPU": 1, "RAM (GB)": 2, "Storage (GB)": 30, "Price (IDR)": 180_000},
        {"Plan": "eXtreme 3", "CPU": 2, "RAM (GB)": 2, "Storage (GB)": 40, "Price (IDR)": 270_000},
        {"Plan": "eXtreme 4", "CPU": 2, "RAM (GB)": 4, "Storage (GB)": 80, "Price (IDR)": 360_000},
        {"Plan": "eXtreme 5", "CPU": 4, "RAM (GB)": 8, "Storage (GB)": 140, "Price (IDR)": 700_000},
        {"Plan": "eXtreme 6", "CPU": 4, "RAM (GB)": 12, "Storage (GB)": 200, "Price (IDR)": 1_050_000},
        {"Plan": "eXtreme 7", "CPU": 8, "RAM (GB)": 16, "Storage (GB)": 250, "Price (IDR)": 1_400_000},
        {"Plan": "eXtreme 8", "CPU": 12, "RAM (GB)": 24, "Storage (GB)": 350, "Price (IDR)": 2_100_000},
        {"Plan": "eXtreme 9", "CPU": 16, "RAM (GB)": 32, "Storage (GB)": 400, "Price (IDR)": 3_600_000},
        {"Plan": "eXtreme 10", "CPU": 32, "RAM (GB)": 64, "Storage (GB)": 500, "Price (IDR)": 5_500_000},
    ],
    "HIGH AVAILABILITY": [
        {"Plan": "Rocket VPS 1", "CPU": 2, "RAM (GB)": 4, "Storage (GB)": 60, "Price (IDR)": 105_000},
        {"Plan": "Rocket VPS 2", "CPU": 4, "RAM (GB)": 4, "Storage (GB)": 80, "Price (IDR)": 145_000},
        {"Plan": "Rocket VPS 3", "CPU": 4, "RAM (GB)": 8, "Storage (GB)": 100, "Price (IDR)": 215_000},
        {"Plan": "Rocket VPS 4", "CPU": 4, "RAM (GB)": 16, "Storage (GB)": 120, "Price (IDR)": 245_000},
        {"Plan": "Rocket VPS 5", "CPU": 8, "RAM (GB)": 8, "Storage (GB)": 120, "Price (IDR)": 270_000},
        {"Plan": "Rocket VPS 6", "CPU": 8, "RAM (GB)": 16, "Storage (GB)": 120, "Price (IDR)": 360_000},
        {"Plan": "Rocket VPS 7", "CPU": 16, "RAM (GB)": 16, "Storage (GB)": 120, "Price (IDR)": 420_000},
    ],
}

# ============================================================
# SECTION 2: MAIN UI FLOW
# ============================================================

main_choice = st.radio("Pilih Kategori Produk:", ["Cloud VPS eXtreme", "Server VPS"], horizontal=True)

# ============================================================
# CLOUD VPS MODE
# ============================================================
if main_choice == "Cloud VPS eXtreme":
    st.subheader("Simulasi Cloud VPS eXtreme")

    variant = st.radio("Pilih Varian Paket", list(CLOUD_COEFFICIENTS.keys()), horizontal=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        cpu = st.slider("CPU (Core)", 1, 10, 2)
    with col2:
        ram = st.slider("RAM (GB)", 1, 10, 2)
    with col3:
        storage = st.slider("Storage (GB)", 20, 500, 20, step=10)

    add_monitoring = st.checkbox("Tambahkan Monitoring (Rp 100.000 / bulan)", value=False)

    coef = CLOUD_COEFFICIENTS[variant]
    result = calculate_cloud_vps(cpu, ram, storage, coef)
    total_price = result["per_month"]

    # add monitoring fee
    if add_monitoring:
        total_price += 100_000

    # apply VAT
    total_price *= 1.11

    st.metric("💰 Perkiraan Biaya Bulanan (IDR)", f"Rp {int(total_price):,} / bulan", delta=f"{result['per_hour']:,} / jam (sebelum PPN)")
    st.caption("Harga sudah termasuk PPN 11%. Monitoring menambah biaya Rp 100.000 per bulan.")

# ============================================================
# SERVER VPS MODE
# ============================================================
else:
    st.subheader("Paket Server VPS")

    group = st.selectbox("Pilih Jenis VPS:", list(SERVER_VPS.keys()))
    billing_cycle = st.radio("Periode Pembayaran", ["Bulanan", "Tahunan"], horizontal=True)
    add_monitoring = st.checkbox("Tambahkan Monitoring (Rp 100.000 / bulan)", value=False)

    df = pd.DataFrame(SERVER_VPS[group])
    df["Base (with VAT)"] = df["Price (IDR)"] * 1.11

    if billing_cycle == "Tahunan":
        df["Base (with VAT)"] *= 12

    view_df = df[["Plan", "CPU", "RAM (GB)", "Storage (GB)", "Base (with VAT)"]]
    view_df.rename(columns={"Base (with VAT)": "Harga (IDR)"}, inplace=True)

    st.dataframe(view_df, hide_index=True, use_container_width=True)

    selected_plan = st.selectbox("Pilih Paket untuk Perhitungan:", view_df["Plan"].tolist())
    selected_row = view_df[view_df["Plan"] == selected_plan].iloc[0]
    base_price = selected_row["Harga (IDR)"]

    # monitoring
    monitoring_cost = 0
    if add_monitoring:
        monitoring_cost = 100_000 * (12 if billing_cycle == "Tahunan" else 1)

    total = base_price + monitoring_cost
    unit_label = "/bulan" if billing_cycle == "Bulanan" else "/tahun"

    st.divider()
    st.metric("💼 Paket Terpilih", selected_plan)
    st.metric("Harga Dasar (sudah PPN 11%)", f"Rp {int(base_price):,} {unit_label}")
    if add_monitoring:
        st.metric("Biaya Monitoring", f"Rp {int(monitoring_cost):,} {unit_label}")
    st.metric("🧾 Total Biaya", f"Rp {int(total):,} {unit_label}")

    st.caption(
        f"Harga sudah termasuk PPN 11%. Monitoring menambah biaya Rp 100.000 per bulan "
        f"({'× 12 = Rp 1.200.000 / tahun' if billing_cycle == 'Tahunan' else 'per bulan'})."
    )
