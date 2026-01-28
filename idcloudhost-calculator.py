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

def get_specs_from_concurrency(concurrent: int):
    """Logic mapping for sync: CU -> (CPU, RAM)"""
    if concurrent <= 20:
        return 1, 2
    elif concurrent <= 60:
        return 2, 4
    elif concurrent <= 150:
        return 4, 8
    elif concurrent <= 400:
        return 8, 16
    else:
        return 8, 32

def recommend_from_concurrency(concurrent: int) -> str:
    cpu, ram = get_specs_from_concurrency(concurrent)
    suffix = " (atau lebih)" if concurrent > 400 else ""
    return f"{cpu} vCPU / {ram} GB RAM{suffix}"

# ----------------------------
# Presets Data
# ----------------------------
CUSTOM_KEY = "Custom (manual sliders)"
PRESETS = [
    {"key": "Staging/Testing", "label": "1 vCPU / 1 GB", "desc": "Dev/staging, mock API, testing ringan.", "cpu": 1, "ram": 1, "storage": 20, "capacity_users": 600, "capacity_duration": 60},
    {"key": "Personal Blog/Portfolio", "label": "2 vCPU / 1 GB", "desc": "Blog/portfolio, landing page, web ringan.", "cpu": 2, "ram": 1, "storage": 20, "capacity_users": 2400, "capacity_duration": 30},
    {"key": "Medium Web App/API", "label": "2 vCPU / 6–8 GB", "desc": "Web app menengah, API, CRUD, worker ringan.", "cpu": 2, "ram": 8, "storage": 40, "capacity_users": 5400, "capacity_duration": 60},
    {"key": "Moderate Web/API", "label": "4 vCPU / 8 GB", "desc": "Website/API moderat, background jobs.", "cpu": 4, "ram": 8, "storage": 60, "capacity_users": 9000, "capacity_duration": 60},
    {"key": "High-load API Gateway", "label": "4 vCPU / 16 GB", "desc": "Service berat, gateway, throughput tinggi.", "cpu": 4, "ram": 16, "storage": 80, "capacity_users": 18000, "capacity_duration": 40},
    {"key": "High-traffic/API", "label": "8 vCPU / 16–32 GB", "desc": "Traffic tinggi, heavy caching, autoscale candidate.", "cpu": 8, "ram": 32, "storage": 120, "capacity_users": 36000, "capacity_duration": 40},
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
        st.session_state["cpu"] = p["cpu"]
        st.session_state["ram"] = p["ram"]
        st.session_state["storage"] = p["storage"]
        st.session_state["users_per_hour"] = p["capacity_users"]
        st.session_state["session_seconds"] = p["capacity_duration"]

def sync_sliders_to_load():
    """Triggered when users manually change traffic numbers"""
    u_hour = st.session_state.get("users_per_hour", 0)
    s_sec = st.session_state.get("session_seconds", 0)
    concurrent = ceil_div(int(u_hour * s_sec), 3600)
    
    # Auto-adjust hardware based on load
    new_cpu, new_ram = get_specs_from_concurrency(concurrent)
    st.session_state["cpu"] = new_cpu
    st.session_state["ram"] = new_ram
    
    # Switch radio to custom because we are departing from fixed presets
    st.session_state["preset_radio"] = CUSTOM_KEY

def auto_switch_to_custom():
    """Triggered when sliders are moved manually"""
    st.session_state["preset_radio"] = CUSTOM_KEY

# ----------------------------
# PDF Export
# ----------------------------
def build_pdf_report(data: dict) -> bytes:
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=landscape(A4))
    width, height = landscape(A4)
    margin_x = 2 * cm
    y = height - 2 * cm
    c.setFont("Helvetica-Bold", 14); c.drawString(margin_x, y, "DATA LAB INDONESIA (DLI)")
    c.setFont("Helvetica", 10); c.drawString(margin_x, y - 14, "Estimasi infrastruktur digital")
    c.drawRightString(width - margin_x, y, f"Tanggal: {data['exported_at_str']}")
    c.line(margin_x, y - 22, width - margin_x, y - 22)
    y -= 50
    def row(l, v, yp):
        c.setFont("Helvetica-Bold", 10); c.drawString(margin_x, yp, l)
        c.setFont("Helvetica", 10); c.drawString(margin_x + 7*cm, yp, str(v))
    row("Preset", data["preset_label"], y); y -= 15
    row("CU", f"~{data['concurrent_users']}", y); y -= 25
    row("Spec", f"{data['cpu']} vCPU / {data['ram']} GB RAM", y); y -= 15
    row("Total", f"Rp {int(data['total_price']):,}{data['unit_label']}", y)
    c.showPage(); c.save()
    return buf.getvalue()

# ----------------------------
# Main UI
# ----------------------------
st.title("Estimasi spesifikasi dan biaya infrastruktur digital")

with open("data/cloud_vps_coeff.json") as f:
    cloud_vps_data = json.load(f)

if "users_per_hour" not in st.session_state:
    st.session_state["users_per_hour"] = PRESETS[0]["capacity_users"]
    st.session_state["session_seconds"] = PRESETS[0]["capacity_duration"]
    st.session_state["cpu"] = PRESETS[0]["cpu"]
    st.session_state["ram"] = PRESETS[0]["ram"]
    st.session_state["storage"] = PRESETS[0]["storage"]

with st.expander("📁 1. Pilih Preset Infrastruktur", expanded=True):
    st.markdown('<div class="preset-radio">', unsafe_allow_html=True)
    st.radio(" ", RADIO_OPTIONS, key="preset_radio", label_visibility="collapsed", on_change=apply_preset_to_sliders)
    st.markdown("</div>", unsafe_allow_html=True)

with st.expander("📊 2. Beban Aplikasi (Estimasi Trafik)", expanded=True):
    c1, c2 = st.columns(2)
    with c1:
        u_hour = st.number_input("User per Jam:", min_value=0, key="users_per_hour", on_change=sync_sliders_to_load)
    with c2:
        s_sec = st.number_input("Durasi Sesi (detik):", min_value=1, key="session_seconds", on_change=sync_sliders_to_load)
    
    concurrent = ceil_div(int(u_hour * s_sec), 3600)
    rec_text = recommend_from_concurrency(concurrent)
    st.markdown(f'<div class="rec-box">💡 Saran: {rec_text} (untuk ~{concurrent} concurrent users)</div>', unsafe_allow_html=True)

st.divider()

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

coef = cloud_vps_data[variant]
base_price = calculate_cloud_vps(st.session_state.cpu, st.session_state.ram, st.session_state.storage, coef)
unit_label = "/tahun" if billing == "Tahunan" else "/bulan"
if billing == "Tahunan": base_price *= 12
total_price = (base_price + int(base_price * 0.04)) * 1.11

st.markdown(f"""
    <div style='text-align:center; background:#f0f2f6; padding:20px; border-radius:10px;'>
        <p style='margin:0;'>💰 <b>Biaya Total (PPN 11% + Monitoring)</b></p>
        <h2 style='margin:0; color:#1f77b4;'>Rp {int(total_price):,}{unit_label}</h2>
    </div>
""", unsafe_allow_html=True)

st.divider()
with st.expander("📐 Penjelasan Perhitungan", expanded=False):
    st.markdown("### Metodologi Estimasi")
    st.markdown("**Rumus Concurrent Users (CU):**")
    st.latex(r"CU = \frac{\text{User per Jam} \times \text{Durasi Sesi (detik)}}{3600}")
    st.markdown("**Estimasi RAM:**")
    st.latex(r"RAM = RAM_{dasar} + (CU \times RAM_{per\ request})")
    st.info("**Parameter Acuan:**\n* RAM Dasar: 1–2 GB\n* RAM per Request: ±16–32 MB\n* CPU: 1 vCPU ≈ 20–50 req/detik")

st.divider()
if st.button("📄 Buat Lampiran PDF"):
    pdf_bytes = build_pdf_report({
        "exported_at_str": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
        "preset_label": st.session_state.preset_radio,
        "users_per_hour": u_hour, "session_seconds": s_sec, "concurrent_users": concurrent,
        "cpu": st.session_state.cpu, "ram": st.session_state.ram, "storage": st.session_state.storage,
        "cpu_type": variant, "total_price": total_price, "unit_label": unit_label
    })
    st.download_button("Download PDF", pdf_bytes, "DLI_Report.pdf", "application/pdf")
