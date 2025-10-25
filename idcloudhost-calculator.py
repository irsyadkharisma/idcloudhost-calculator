import streamlit as st

# ------------------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------------------
st.set_page_config(page_title="IDCloudHost Pricing Simulator", page_icon="💰")
st.title("💰 IDCloudHost Cloud VPS eXtreme (NVMe) Pricing Simulator")
st.caption("A faithful re-creation of the official price slider logic, using coefficients extracted from IDCloudHost's JavaScript.")

# ------------------------------------------------------------
# PRICE COEFFICIENTS (from script.min.js)
# ------------------------------------------------------------
COEFFICIENTS = {
    "Basic Standard": {"cpuram1": 25.685, "cpuram2": 51.37, "storage1": 0.856, "storage2": 1.712},
    "Intel eXtreme": {"cpuram1": 36.0, "cpuram2": 55.0, "storage1": 3.0, "storage2": 4.0},
    "AMD eXtreme": {"cpuram1": 36.0, "cpuram2": 59.0, "storage1": 3.0, "storage2": 4.0},
}


# ------------------------------------------------------------
# PRICING FUNCTION (replicated from JS)
# ------------------------------------------------------------
def calculate_price(cpu: int, ram: int, storage: int, coef: dict) -> dict:
    cpu = float(cpu)
    ram = float(ram)
    storage = float(storage)

    per_hour = (
        (cpu * coef["cpuram1"] if cpu <= 2 else cpu * coef["cpuram2"])
        + (ram * coef["cpuram1"] if ram <= 2 else ram * coef["cpuram2"])
        + (storage * coef["storage1"] if storage < 81 else storage * coef["storage2"])
    )
    per_month = per_hour * 730  # 730 hours/month
    per_month_rounded = 1000 * round(per_month / 1000)
    return {"per_hour": round(per_hour), "per_month": int(per_month_rounded)}


# ------------------------------------------------------------
# USER INPUTS
# ------------------------------------------------------------
st.header("1️⃣ Choose Plan Type")
variant = st.radio("Plan Variant", list(COEFFICIENTS.keys()), horizontal=True)

st.header("2️⃣ Configure Resources")
col1, col2, col3 = st.columns(3)
with col1:
    cpu = st.slider("CPU (Cores)", 1, 10, 2)
with col2:
    ram = st.slider("RAM (GB)", 1, 10, 2)
with col3:
    storage = st.slider("Storage (GB)", 20, 500, 20, step=10)

st.header("3️⃣ VAT Option")
vat = st.radio("Include 11% VAT?", ["No", "Yes"], horizontal=True)

# ------------------------------------------------------------
# PRICE CALCULATION
# ------------------------------------------------------------
coef = COEFFICIENTS[variant]
result = calculate_price(cpu, ram, storage, coef)
price = result["per_month"]
if vat == "Yes":
    price *= 1.11

# ------------------------------------------------------------
# OUTPUT
# ------------------------------------------------------------
st.metric(
    label="💰 Estimated Monthly Cost (IDR)",
    value=f"{int(price):,}",
    delta=f"≈ {result['per_hour']:,} / hour"
)

# ------------------------------------------------------------
# INFO BOX
# ------------------------------------------------------------
st.divider()
st.markdown(
    f"""
    **🧮 Calculation details**
    ```
    perHour = (CPU × rateCPU) + (RAM × rateRAM) + (Storage × rateStorage)
    perMonth = perHour × 730
    Rounded to nearest 1,000 IDR
    ```
    **Coefficients for {variant}:**
    ```
    {COEFFICIENTS[variant]}
    ```
    """
)

st.info(
    "These values match IDCloudHost's internal formula (found in `script.min.js?v=3.0.2`). "
    "Sliders behave like the official website — no scraping, just math."
)
