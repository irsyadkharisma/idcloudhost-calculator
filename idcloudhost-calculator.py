import streamlit as st
import pandas as pd

# ------------------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------------------
st.set_page_config(page_title="Kalkulator dan Paket Server", page_icon="💰", layout="centered")
st.title("💰 Paket server untuk produk internal")
st.caption("Digunakan sebagai basis perhitungan biaya acuan awal")

# ============================================================
# SECTION 1: DATA & FORMULAS
# ============================================================

# Cloud VPS coefficients from IDCloudHost's official JS
CLOUD_COEFFICIENTS = {
    "Basic Standard": {"cpuram1": 25.685, "cpuram2": 51.37, "storage1": 0.856, "storage2": 1.712},
    "Intel eXtreme": {"cpuram1": 36.0, "cpuram2": 55.0, "storage1": 3.0, "storage2": 4.0},
    "AMD eXtreme": {"cpuram1": 36.0, "cpuram2": 59.0, "storage1": 3.0, "storage2": 4.0},
}


def calculate_cloud_vps(cpu: int, ram: int, storage: int, coef: dict) -> dict:
    """Replicate the JS pricing formula for Cloud VPS."""
    per_hour = (
        (cpu * coef["cpuram1"] if cpu <= 2 else cpu * coef["cpuram2"])
        + (ram * coef["cpuram1"] if ram <= 2 else ram * coef["cpuram2"])
        + (storage * coef["storage1"] if storage < 81 else storage * coef["storage2"])
    )
    per_month = per_hour * 730
    per_month_rounded = 1000 * round(per_month / 1000)
    return {"per_hour": round(per_hour), "per_month": int(per_month_rounded)}


# Server VPS static pricing data
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

main_choice = st.radio("Select Product Category:", ["Cloud VPS eXtreme", "Server VPS"], horizontal=True)

# ============================================================
# CLOUD VPS MODE
# ============================================================
if main_choice == "Cloud VPS eXtreme":
    st.subheader("Cloud VPS eXtreme Simulator")

    variant = st.radio("Choose Plan Variant", list(CLOUD_COEFFICIENTS.keys()), horizontal=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        cpu = st.slider("CPU (Cores)", 1, 10, 2)
    with col2:
        ram = st.slider("RAM (GB)", 1, 10, 2)
    with col3:
        storage = st.slider("Storage (GB)", 20, 500, 20, step=10)

    add_monitoring = st.checkbox("Add 5% Monitoring Add-on", value=False)

    # compute
    coef = CLOUD_COEFFICIENTS[variant]
    result = calculate_cloud_vps(cpu, ram, storage, coef)
    total_price = result["per_month"]

    # apply monitoring
    if add_monitoring:
        total_price *= 1.05

    # mandatory VAT
    total_price *= 1.11

    st.metric("💰 Monthly Cost (IDR)", f"{int(total_price):,}", delta=f"{result['per_hour']:,} / hour (before tax)")
    st.caption("Includes 11% VAT. Add-on Monitoring increases cost by 5%.")

    st.divider()
    st.markdown(
        f"""
        **Formula Used (from IDCloudHost JS)**  
        `price = (cpu×coef + ram×coef + storage×coef) × 730 hrs × 1.11 VAT × (1.05 if monitoring)`
        \nCoefficients for *{variant}*:
        ```
        {CLOUD_COEFFICIENTS[variant]}
        ```
        """
    )

# ============================================================
# SERVER VPS MODE
# ============================================================
else:
    st.subheader("Server VPS Packages")
    group = st.selectbox("Choose VPS Type:", list(SERVER_VPS.keys()))

    add_monitoring = st.checkbox("Add 5% Monitoring Add-on", value=False)

    df = pd.DataFrame(SERVER_VPS[group])
    df["Price (IDR)"] = df["Price (IDR)"].apply(lambda x: int(x * (1.05 if add_monitoring else 1.0) * 1.11))

    st.dataframe(df, hide_index=True, use_container_width=True)

    col1, col2 = st.columns(2)
    col1.metric("Lowest Plan", f"Rp {df['Price (IDR)'].min():,}")
    col2.metric("Highest Plan", f"Rp {df['Price (IDR)'].max():,}")

    st.caption("All prices include 11% VAT. Monitoring add-on adds 5%.")

