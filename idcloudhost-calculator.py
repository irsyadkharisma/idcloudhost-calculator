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
    "Basic Standard — Dev/mock-up server API and website": {
        "cpuram1": 25.685, "cpuram2": 51.37, "storage1": 0.856, "storage2": 1.712
    },
    "Intel eXtreme — Moderate website/API (Intel)": {
        "cpuram1": 36.0, "cpuram2": 55.0, "storage1": 3.0, "storage2": 4.0
    },
    "AMD eXtreme — Moderate website/API (AMD)": {
        "cpuram1": 36.0, "cpuram2": 59.0, "storage1": 3.0, "storage2": 4.0
    },
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
    st.subheader("Cloud VPS eXtreme Custom")

    # Include descriptions directly in the title text
    variant = st.radio("Pilih Varian Paket", list(CLOUD_COEFFICIENTS.keys()), horizontal=False)

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
    st.metric("Harga Dasar", f"Rp {int(base_price):,}/bulan")
    st.metric("Harga + PPN 11%", f"Rp {int(base_price * 1.11):,}/bulan")
    st.metric("Harga Total (PPN + Monitoring)", f"Rp {int(total_price):,}/bulan")

    st.caption(
        "Harga sudah termasuk PPN 11% dan biaya monitoring wajib sebesar Rp 10.000 per bulan. "
        "Semua nilai dibulatkan ke ribuan terdekat."
    )

# ============================================================
# SERVER VPS MODE
# ============================================================
else:
    st.subheader("Paket Server VPS")

    # (✅ FIX) Use horizontal radio buttons again for VPS type
    group = st.radio(
        "Pilih Jenis VPS:",
        ["HIGH PERFORMANCE", "DEDICATED CPU", "HIGH AVAILABILITY"],
        horizontal=True
    )

    billing_cycle = st.radio("Periode Pembayaran", ["Bulanan", "Tahunan"], horizontal=True)


# Build DF
df = pd.DataFrame(SERVER_VPS[group])

# Base price
if billing_cycle == "Tahunan":
    df["Harga Dasar"] = df["Price (IDR)"] * 12
    monitoring_fee = 120_000  # flat per year
    unit_label = "/tahun"
else:
    df["Harga Dasar"] = df["Price (IDR)"]
    monitoring_fee = 10_000   # flat per month
    unit_label = "/bulan"

# VAT and Total (monitoring is NOT VAT-ed per your spec)
df["Harga + PPN (11%)"] = df["Harga Dasar"] * 1.11
df["Harga Total"] = df["Harga + PPN (11%)"] + monitoring_fee

# Show table
st.dataframe(
    df[["Plan", "CPU", "RAM (GB)", "Storage (GB)", "Harga Dasar", "Harga + PPN (11%)", "Harga Total"]],
    hide_index=True,
    use_container_width=True,
)

# Selection + summary
selected_plan = st.selectbox("Pilih Paket untuk Perhitungan:", df["Plan"].tolist())
row = df[df["Plan"] == selected_plan].iloc[0]

st.divider()
st.markdown("### 💼 Paket Terpilih")
st.markdown(f"## **{row['Plan']}**")
st.metric("Harga Dasar", f"Rp {int(row['Harga Dasar']):,} {unit_label}")
st.metric("Harga + PPN (11%)", f"Rp {int(row['Harga + PPN (11%)']):,} {unit_label}")
st.metric("🧾 Total Harga (termasuk Monitoring)", f"Rp {int(row['Harga Total']):,} {unit_label}")

st.caption(
    "Harga sudah termasuk PPN 11%. Monitoring wajib Rp 10.000/bulan atau Rp 120.000/tahun."
)
