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

# Cloud VPS coefficients (from IDCloudHost JS)
CLOUD_COEFFICIENTS = {
    "Basic Standard": {"cpuram1": 25.685, "cpuram2": 51.37, "storage1": 0.856, "storage2": 1.712},
    "Intel eXtreme": {"cpuram1": 36.0, "cpuram2": 55.0, "storage1": 3.0, "storage2": 4.0},
    "AMD eXtreme": {"cpuram1": 36.0, "cpuram2": 59.0, "storage1": 3.0, "storage2": 4.0},
}


def calculate_cloud_vps(cpu: int, ram: int, storage: int, coef: dict) -> int:
    """Replicate IDCloudHost Cloud VPS pricing logic (monthly base price)."""
    per_hour = (
        (cpu * coef["cpuram1"] if cpu <= 2 else cpu * coef["cpuram2"])
        + (ram * coef["cpuram1"] if ram <= 2 else ram * coef["cpuram2"])
        + (storage * coef["storage1"] if storage < 81 else storage * coef["storage2"])
    )
    per_month = per_hour * 730
    return int(1000 * round(per_month / 1000))  # round to nearest thousand


# Static Server VPS pricing data
SERVER_VPS = {
    "HIGH PERFORMANCE": [
        {"Plan": "NVME 1", "CPU": 1, "RAM (GB)": 1, "Storage (GB)": 25, "Price (IDR)": 112_000},
        {"Plan": "NVME 2", "CPU": 1, "RAM (GB)": 2, "Storage (GB)": 30, "Price (IDR)": 180_000},
        {"Plan": "NVME 3", "CPU": 2, "RAM (GB)": 2, "Storage (GB)": 40, "Price (IDR)": 270_000},
        {"Plan": "NVME 4", "CPU": 2, "RAM (GB)": 4, "Storage (GB)": 80, "Price (IDR)": 360_000},
        {"Plan": "NVME 5", "CPU": 4, "RAM (GB)": 8, "Storage (GB)": 140, "Price (IDR)": 700_000},
    ],
    "DEDICATED CPU": [
        {"Plan": "eXtreme 1", "CPU": 1, "RAM (GB)": 1, "Storage (GB)": 25, "Price (IDR)": 112_000},
        {"Plan": "eXtreme 2", "CPU": 1, "RAM (GB)": 2, "Storage (GB)": 30, "Price (IDR)": 180_000},
        {"Plan": "eXtreme 3", "CPU": 2, "RAM (GB)": 2, "Storage (GB)": 40, "Price (IDR)": 270_000},
        {"Plan": "eXtreme 4", "CPU": 2, "RAM (GB)": 4, "Storage (GB)": 80, "Price (IDR)": 360_000},
        {"Plan": "eXtreme 5", "CPU": 4, "RAM (GB)": 8, "Storage (GB)": 140, "Price (IDR)": 700_000},
        {"Plan": "eXtreme 6", "CPU": 4, "RAM (GB)": 12, "Storage (GB)": 200, "Price (IDR)": 1_050_000},
        {"Plan": "eXtreme 7", "CPU": 8, "RAM (GB)": 16, "Storage (GB)": 250, "Price (IDR)": 1_400_000},
    ],
    "HIGH AVAILABILITY": [
        {"Plan": "Rocket VPS 1", "CPU": 2, "RAM (GB)": 4, "Storage (GB)": 60, "Price (IDR)": 105_000},
        {"Plan": "Rocket VPS 2", "CPU": 4, "RAM (GB)": 4, "Storage (GB)": 80, "Price (IDR)": 145_000},
        {"Plan": "Rocket VPS 3", "CPU": 4, "RAM (GB)": 8, "Storage (GB)": 100, "Price (IDR)": 215_000},
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
        cpu = st.slider("CPU (Core)", 2, 10, 2)
    with col2:
        ram = st.slider("RAM (GB)", 2, 10, 2)
    with col3:
        storage = st.slider("Storage (GB)", 20, 500, 20, step=10)

    coef = CLOUD_COEFFICIENTS[variant]

    base_price = calculate_cloud_vps(cpu, ram, storage, coef)
    monitoring_fee = 10_000  # per month
    subtotal = base_price + monitoring_fee
    total_price = subtotal * 1.11

    st.markdown("### 💰 Perincian Biaya Bulanan")
    col1, col2, col3 = st.columns(3)
    col1.metric("Harga Dasar", f"Rp {int(base_price):,}")
    col2.metric("Harga + PPN 11%", f"Rp {int(base_price * 1.11):,}")
    col3.metric("Harga Total (PPN + Monitoring)", f"Rp {int(total_price):,}")

    st.caption(
        "Harga sudah termasuk PPN 11% dan biaya monitoring wajib sebesar Rp 10.000 per bulan. "
        "Semua nilai dibulatkan ke ribuan terdekat."
    )

# ============================================================
# SERVER VPS MODE
# ============================================================
else:
    st.subheader("Paket Server VPS")

    # Use radio instead of dropdown
    group = st.radio("Pilih Jenis VPS:", list(SERVER_VPS.keys()), horizontal=False)
    billing_cycle = st.radio("Periode Pembayaran", ["Bulanan", "Tahunan"], horizontal=True)

    df = pd.DataFrame(SERVER_VPS[group])
    df["Harga Dasar"] = df["Price (IDR)"]
    df["Harga + PPN (11%)"] = df["Harga Dasar"] * 1.11
    monitoring_cost = 10_000 * (12 if billing_cycle == "Tahunan" else 1)
    df["Harga Total"] = df["Harga + PPN (11%)"] + monitoring_cost

    if billing_cycle == "Tahunan":
        df["Harga Dasar"] *= 12
        df["Harga + PPN (11%)"] *= 12
        df["Harga Total"] *= 12

    # Add selection column
    df_display = df.copy()
    selected_index = st.radio(
        "Pilih Paket:",
        range(len(df_display)),
        format_func=lambda i: df_display.loc[i, "Plan"],
        horizontal=True if len(df_display) <= 5 else False,
    )

    st.dataframe(
        df_display[["Plan", "CPU", "RAM (GB)", "Storage (GB)", "Harga Dasar", "Harga + PPN (11%)", "Harga Total"]],
        hide_index=True,
        use_container_width=True,
    )

    row = df_display.iloc[selected_index]
    base = row["Harga Dasar"]
    vat = row["Harga + PPN (11%)"]
    total = row["Harga Total"]
    plan_name = row["Plan"]
    unit_label = "/bulan" if billing_cycle == "Bulanan" else "/tahun"

    st.divider()
    st.markdown("### 💼 Paket Terpilih")
    st.markdown(f"## **{plan_name}**")

    col1, col2, col3 = st.columns(3)
    col1.metric("Harga Dasar", f"Rp {int(base):,} {unit_label}")
    col2.metric("Harga + PPN (11%)", f"Rp {int(vat):,} {unit_label}")
    col3.metric("🧾 Total Harga (termasuk Monitoring)", f"Rp {int(total):,} {unit_label}")

    st.caption(
        f"Harga sudah termasuk PPN 11% dan biaya monitoring wajib Rp 10.000 per bulan "
        f"({'× 12 = Rp 120.000 / tahun' if billing_cycle == 'Tahunan' else 'per bulan'})."
    )
