import json
import streamlit as st
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm

# ----------------------------
# Page setup
# ----------------------------
st.set_page_config(page_title="IDCloudHost Calculator", page_icon="💰", layout="wide")
st.markdown(
    """
    <style>
        .block-container { max-width: 1200px; padding-left: 3rem; padding-right: 3rem; }

        /* Make ONE radio widget display as 2 columns */
        .preset-radio div[data-testid="stRadio"] .stRadio > div {
            display: grid !important;
            grid-template-columns: 1fr 1fr;
            column-gap: 3rem;
            row-gap: 0.35rem;
        }
        .preset-radio div[data-testid="stRadio"] label {
            white-space: normal !important;
            line-height: 1.25;
        }

        /* Make recommendation box look like your screenshot */
        .rec-box {
            background:#eaf3ff;
            border-left:4px solid #3b82f6;
            padding:16px;
            border-radius:8px;
            font-weight:600;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ----------------------------
# Pricing & Logic
# ----------------------------
def calculate_cloud_vps(cpu: int, ram: int, storage: int, coef: dict) -> int:
    per_hour = (
        (cpu * coef["cpuram1"] if cpu <= 2 else cpu * coef["cpuram2"])
        + (ram * coef["cpuram1"] if ram <= 2 else ram * coef["cpuram2"])
        + (storage * coef["storage1"] if storage < 81 else storage * coef["storage2"])
    )
    per_month = per_hour * 730
    return int(1000 * round(per_month / 1000))


def ceil_div(a: int, b: int) -> int:
    return (a + b - 1) // b


def recommend_from_concurrency(concurrent: int) -> str:
    if concurrent <= 20:
        return "1 vCPU / 2 GB RAM"
    elif concurrent <= 60:
        return "2 vCPU / 4 GB RAM"
    elif concurrent <= 150:
        return "4 vCPU / 8 GB RAM"
    elif concurrent <= 400:
        return "8 vCPU / 16 GB RAM"
    else:
        return "8 vCPU / 32 GB RAM (atau lebih)"


# ----------------------------
# Presets with Capacity Logic
# ----------------------------
CUSTOM_KEY = "Custom (manual sliders)"

PRESETS = [
    {
        "key": "Staging/Testing",
        "label": "1 vCPU / 1 GB",
        "desc": "Dev/staging, mock API, testing ringan.",
        "cpu": 1, "ram": 1, "storage": 20,
        "capacity_users": 600, "capacity_duration": 60, # Result: ~10 CU
    },
    {
        "key": "Personal Blog/Portfolio",
        "label": "2 vCPU / 1 GB",
        "desc": "Blog/portfolio, landing page, web ringan.",
        "cpu": 2, "ram": 1, "storage": 20,
        "capacity_users": 2400, "capacity_duration": 30, # Result: ~20 CU
    },
    {
        "key": "Medium Web App/API",
        "label": "2 vCPU / 6–8 GB",
        "desc": "Web app menengah, API, CRUD, worker ringan.",
        "cpu": 2, "ram": 8, "storage": 40,
        "capacity_users": 5400, "capacity_duration": 60, # Result: ~90 CU
    },
    {
        "key": "Moderate Web/API",
        "label": "4 vCPU / 8 GB",
        "desc": "Website/API moderat, background jobs.",
        "cpu": 4, "ram": 8, "storage": 60,
        "capacity_users": 9000, "capacity_duration": 60, # Result: ~150 CU
    },
    {
        "key": "High-load API Gateway",
        "label": "4 vCPU / 16 GB",
        "desc": "Service berat, gateway, throughput tinggi.",
        "cpu": 4, "ram": 16, "storage": 80,
        "capacity_users": 18000, "capacity_duration": 40, # Result: ~200 CU
    },
    {
        "key": "High-traffic/API",
        "label": "8 vCPU / 16–32 GB",
        "desc": "Traffic tinggi, heavy caching, autoscale candidate.",
        "cpu": 8, "ram": 32, "storage": 120,
        "capacity_users": 36000, "capacity_duration": 40, # Result: ~400 CU
    },
]

PRESET_MAP = {p["key"]: p for p in PRESETS}
RADIO_OPTIONS = [f'{p["key"]}: {p["desc"]} ({p["label"]})' for p in PRESETS] + [CUSTOM_KEY]

def preset_key_from_radio(radio_value: str) -> str:
    if radio_value == CUSTOM_KEY: return CUSTOM_KEY
    return radio_value.split(":", 1)[0].strip()

# ----------------------------
# State Sync Callbacks
# ----------------------------
def apply_preset_to_sliders():
    chosen_radio = st.session_state.get("preset_radio", RADIO_OPTIONS[0])
    key = preset_key_from_radio(chosen_radio)
    if key in PRESET_MAP:
        p = PRESET_MAP[key]
        # Sync Hardware
        st.session_state["cpu"] = p["cpu"]
        st.session_state["ram"] = p["ram"]
        st.session_state["storage"] = p["storage"]
        # Sync Capacity/Traffic
        st.session_state["users_per_hour"] = p["capacity_users"]
        st.session_state["session_seconds"] = p["capacity_duration"]

def auto_switch_to_custom():
    chosen_radio = st.session_state.get("preset_radio", RADIO_OPTIONS[0])
    key = preset_key_from_radio(chosen_radio)
    if key == CUSTOM_KEY: return
    
    p = PRESET_MAP.get(key)
    if p:
        # Check if hardware OR traffic inputs changed
        if (st.session_state.get("cpu") != p["cpu"] or 
            st.session_state.get("ram") != p["ram"] or 
            st.session_state.get("users_per_hour") != p["capacity_users"] or
            st.session_state.get("session_seconds") != p["capacity_duration"]):
            st.session_state["preset_radio"] = CUSTOM_KEY

# ----------------------------
# PDF Export (Landscape)
# ----------------------------
def build_pdf_report(data: dict) -> bytes:
    buf = BytesIO()
    page_size = landscape(A4)
    c = canvas.Canvas(buf, pagesize=page_size)
    width, height = page_size
    margin_x = 2 * cm
    y = height - 2 * cm

    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin_x, y, "DATA LAB INDONESIA (DLI)")
    c.setFont("Helvetica", 10)
    c.drawString(margin_x, y - 14, "Estimasi spesifikasi dan biaya infrastruktur digital")
    c.drawRightString(width - margin_x, y, f"Tanggal Export: {data['exported_at_str']}")
    c.line(margin_x, y - 22, width - margin_x, y - 22)

    y -= 50
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin_x, y, "Ringkasan Estimasi & Beban")
    y -= 20

    def row(label, val, y_pos):
        c.setFont("Helvetica-Bold", 10); c.drawString(margin_x, y_pos, label)
        c.setFont("Helvetica", 10); c.drawString(margin_x + 7*cm, y_pos, str(val))

    row("Preset", data["preset_label"], y); y -= 15
    row("User per Jam", f"{int(data['users_per_hour']):,}", y); y -= 15
    row("Durasi Sesi", f"{data['session_seconds']} detik", y); y -= 15
    row("Concurrent Users", f"~{data['concurrent_users']}", y); y -= 25

    c.setFont("Helvetica-Bold", 12); c.drawString(margin_x, y, "Konfigurasi & Biaya"); y -= 20
    row("CPU / RAM / Disk", f"{data['cpu']} vCPU / {data['ram']} GB / {data['storage']} GB", y); y -= 15
    row("Tipe CPU", data["cpu_type"], y); y -= 15
    row("Total (Final)", f"Rp {int(data['total_price']):,}{data['unit_label']}", y); y -= 30

    c.setFont("Helvetica-Bold", 10); c.drawString(margin_x, y, "Metodologi")
    y -= 15
    c.setFont("Helvetica", 9)
    c.drawString(margin_x, y, "CU = (Users per Jam * Durasi) / 3600")

    c.showPage()
    c.save()
    return buf.getvalue()

# ----------------------------
# Main UI
# ----------------------------
st.title("Estimasi spesifikasi dan biaya infrastruktur digital")

with open("data/cloud_vps_coeff.json") as f:
    cloud_vps_data = json.load(f)

# Initialize Session States
if "users_per_hour" not in st.session_state:
    st.session_state["users_per_hour"] = PRESETS[0]["capacity_users"]
    st.session_state["session_seconds"] = PRESETS[0]["capacity_duration"]
    st.session_state["cpu"] = PRESETS[0]["cpu"]
    st.session_state["ram"] = PRESETS[0]["ram"]
    st.session_state["storage"] = PRESETS[0]["storage"]

# STEP 1: PRESET
with st.expander("📁 1. Pilih Preset Infrastruktur", expanded=True):
    st.markdown('<div class="preset-radio">', unsafe_allow_html=True)
    st.radio(
        " ", RADIO_OPTIONS, key="preset_radio",
        label_visibility="collapsed", on_change=apply_preset_to_sliders
    )
    st.markdown("</div>", unsafe_allow_html=True)

# STEP 2: TRAFFIC
with st.expander("📊 2. Beban Aplikasi (Estimasi Trafik)", expanded=True):
    c1, c2 = st.columns(2)
    with c1:
        u_hour = st.number_input("User per Jam:", min_value=0, key="users_per_hour", on_change=auto_switch_to_custom)
    with c2:
        s_sec = st.number_input("Durasi Sesi (detik):", min_value=1, key="session_seconds", on_change=auto_switch_to_custom)

    concurrent = ceil_div(int(u_hour * s_sec), 3600)
    rec_text = recommend_from_concurrency(concurrent)

    st.markdown(f'<div class="rec-box">💡 Saran: {rec_text} (untuk ~{concurrent} concurrent users)</div>', unsafe_allow_html=True)

st.divider()

# STEP 3: CUSTOMIZATION
st.subheader("Customisasi Spesifikasi")
s1, s2, s3 = st.columns(3)
with s1:
    st.slider("CPU (Core)", 1, 32, key="cpu", on_change=auto_switch_to_custom)
with s2:
    st.slider("RAM (GB)", 1, 128, key="ram", on_change=auto_switch_to_custom)
with s3:
    st.slider("Storage (GB)", 20, 2000, step=10, key="storage", on_change=auto_switch_to_custom)

variant = st.radio("Tipe CPU", list(cloud_vps_data.keys()), key="variant")
billing = st.radio("Periode", ["Bulanan", "Tahunan"], horizontal=True, key="billing")

# Calculations
coef = cloud_vps_data[variant]
base_price = calculate_cloud_vps(st.session_state.cpu, st.session_state.ram, st.session_state.storage, coef)
if billing == "Tahunan":
    base_price *= 12
    unit_label = "/tahun"
else:
    unit_label = "/bulan"

total_price = (base_price + int(base_price * 0.04)) * 1.11

st.markdown(f"""
    <div style='text-align:center; background:#f0f2f6; padding:20px; border-radius:10px;'>
        <p style='margin:0;'>💰 <b>Biaya Total (PPN 11% + Monitoring)</b></p>
        <h2 style='margin:0; color:#1f77b4;'>Rp {int(total_price):,}{unit_label}</h2>
    </div>
""", unsafe_allow_html=True)

# Export
if st.button("📄 Generate Report PDF"):
    pdf_bytes = build_pdf_report({
        "exported_at_str": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
        "preset_label": st.session_state.preset_radio,
        "users_per_hour": u_hour,
        "session_seconds": s_sec,
        "concurrent_users": concurrent,
        "cpu": st.session_state.cpu,
        "ram": st.session_state.ram,
        "storage": st.session_state.storage,
        "cpu_type": variant,
        "total_price": total_price,
        "unit_label": unit_label
    })
    st.download_button("Click to Download", pdf_bytes, "DLI_Report.pdf", "application/pdf")
