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
    page_size = landscape(A4)
    c = canvas.Canvas(buf, pagesize=page_size)
    width, height = page_size

    margin_x = 2 * cm
    top_y = height - 2 * cm

    # Column positions (label/value)
    label_x = margin_x
    value_x = margin_x + 8.5 * cm  # adjust to taste for alignment
    right_x = width - margin_x

    # ---- Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(margin_x, top_y, "DATA LAB INDONESIA (DLI)")

    c.setFont("Helvetica", 10)
    c.drawString(margin_x, top_y - 16, "Estimasi spesifikasi dan biaya infrastruktur digital")

    c.setFont("Helvetica", 10)
    c.drawRightString(right_x, top_y, f"Tanggal Export: {data['exported_at_str']}")

    # Divider line
    c.setLineWidth(1)
    c.line(margin_x, top_y - 28, right_x, top_y - 28)

    y = top_y - 55

    def section(title: str):
        nonlocal y
        c.setFont("Helvetica-Bold", 13)
        c.drawString(margin_x, y, title)
        y -= 18

    def row(label: str, value: str):
        """One neat label-value row, like the screenshot."""
        nonlocal y
        c.setFont("Helvetica-Bold", 11)
        c.drawString(label_x, y, label)
        c.setFont("Helvetica", 11)
        c.drawString(value_x, y, str(value))
        y -= 16

    # ---- Section 1: Ringkasan Estimasi & Beban
    section("Ringkasan Estimasi & Beban")

    row("Preset", data.get("preset_label", "—"))
    row("User per Jam", f"{int(data.get('users_per_hour', 0)):,}")
    row("Durasi Sesi", f"{int(data.get('session_seconds', 0))} detik")
    row("Concurrent Users", f"~{int(data.get('concurrent_users', 0)):,}")

    y -= 8

    # ---- Section 2: Konfigurasi & Biaya
    section("Konfigurasi & Biaya")

    cpu = data.get("cpu", 0)
    ram = data.get("ram", 0)
    storage = data.get("storage", 0)
    row("CPU / RAM / Disk", f"{cpu} vCPU / {ram} GB / {storage} GB")

    row("Tipe CPU", data.get("cpu_type", "—"))

    total_price = int(data.get("total_price", 0))
    unit_label = data.get("unit_label", "")
    row("Total (Final)", f"Rp {total_price:,}{unit_label}")

    y -= 10

    # Footer (subtle)
    c.setLineWidth(0.5)
    c.setStrokeColorRGB(0.75, 0.75, 0.75)
    c.line(margin_x, 2.2 * cm, right_x, 2.2 * cm)

    c.setFillColorRGB(0.2, 0.2, 0.2)
    c.setFont("Helvetica", 9)
    c.drawString(margin_x, 1.7 * cm, "by Data Lab Indonesia")
    c.drawRightString(right_x, 1.7 * cm, "Generated via DLI Smart Estimator")

    c.showPage()
    c.save()
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
        <p style='margin:0;'>💰 <b>Biaya Total (PPN 11% + Monitoring 4%)</b></p>
        <h2 style='margin:0; color:#1f77b4;'>Rp {int(total_price):,}{unit_label}</h2>
    </div>
""", unsafe_allow_html=True)

# ---- Section 3: Metodologi (UI-like)
section("Metodologi")

# Sub-title like UI
c.setFont("Helvetica-Bold", 12)
c.drawString(margin_x, y, "Metodologi Estimasi")
y -= 18

# --- Rumus CU
c.setFont("Helvetica-Bold", 10)
c.drawString(margin_x, y, "Rumus Concurrent Users (CU):")
y -= 16

# Centered formula (typography approximation)
c.setFont("Helvetica-Oblique", 12)
c.drawCentredString(width / 2, y, "CU = (User per Jam × Durasi Sesi (detik)) / 3600")
y -= 26

# --- Rumus RAM
c.setFont("Helvetica-Bold", 10)
c.drawString(margin_x, y, "Estimasi RAM:")
y -= 16

c.setFont("Helvetica-Oblique", 12)
c.drawCentredString(width / 2, y, "RAM = RAM dasar + (CU × RAM per request)")
y -= 26

# --- Parameter box (light blue like your UI)
box_x = margin_x
box_w = width - (2 * margin_x)
box_h = 50  # adjust if you add more lines
box_y = y - box_h + 8  # position box below current y

# Draw filled rectangle
c.saveState()
c.setFillColorRGB(0.90, 0.95, 1.00)   # light blue
c.setStrokeColorRGB(0.90, 0.95, 1.00) # no visible border
c.roundRect(box_x, box_y, box_w, box_h, 6, fill=1, stroke=1)
c.restoreState()

# Box content
text_x = box_x + 0.6 * cm
text_y = box_y + box_h - 14

c.setFont("Helvetica-Bold", 10)
c.drawString(text_x, text_y, "Parameter Acuan:")
text_y -= 14

c.setFont("Helvetica", 10)

# simple bullet helper
def bullet_line(txt, yy):
    c.drawString(text_x, yy, "•")
    c.drawString(text_x + 0.5 * cm, yy, txt)

bullet_line("RAM Dasar: 1–2 GB", text_y); text_y -= 14
bullet_line("RAM per Request: ±16–32 MB", text_y); text_y -= 14
bullet_line("CPU: 1 vCPU ≈ 20–50 req/detik", text_y); text_y -= 14

# Move y below the box
y = box_y - 18



st.divider()

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
    "unit_label": unit_label,
})

st.download_button(
    label="📄 Export PDF Estimasi Infrastruktur",
    data=pdf_bytes,
    file_name=f"DLI_Estimasi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
    mime="application/pdf",
)




