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

SPEC_LOAD_RULES = [
    {"cpu": 1, "ram": 1, "users_per_hour": 600, "session_seconds": 60},
    {"cpu": 1, "ram": 2, "users_per_hour": 1200, "session_seconds": 60},
    {"cpu": 2, "ram": 4, "users_per_hour": 3600, "session_seconds": 60},
    {"cpu": 4, "ram": 8, "users_per_hour": 9000, "session_seconds": 60},
    {"cpu": 8, "ram": 16, "users_per_hour": 36000, "session_seconds": 40},
    {"cpu": 8, "ram": 32, "users_per_hour": 45000, "session_seconds": 40},
]

def get_load_from_specs(cpu: int, ram: int) -> tuple[int, int]:
    """Estimate traffic inputs from the selected CPU/RAM."""
    matching_rules = [
        rule for rule in SPEC_LOAD_RULES
        if cpu >= rule["cpu"] and ram >= rule["ram"]
    ]
    selected = matching_rules[-1] if matching_rules else SPEC_LOAD_RULES[0]
    return selected["users_per_hour"], selected["session_seconds"]

def recommend_from_concurrency(concurrent: int) -> str:
    cpu, ram = get_specs_from_concurrency(concurrent)
    suffix = " (atau lebih)" if concurrent > 400 else ""
    return f"{cpu} vCPU / {ram} GB RAM{suffix}"

# ----------------------------
# Additional Cost Config
# ----------------------------
OBJECT_STORAGE_PER_GB_MONTH = 507
OBJECT_STORAGE_PER_GB_HOUR = 0.694
SECURITY_SCAN_PER_PROJECT_MONTH = 100_000
DEFAULT_DOMAIN_PRICE_YEARLY = 300_000
VPS_RESERVE_MONTHS_PER_YEAR = 2
MONTHS_PER_YEAR = 12
DOMAIN_ACTION_OPTIONS = ["Register", "Renewal", "Transfer"]
DOMAIN_PRICES_YEARLY = {
    ".my.id": {"Register": 25_000, "Renewal": 25_000, "Transfer": 25_000},
    ".biz.id": {"Register": 55_000, "Renewal": 55_000, "Transfer": 55_000},
    ".ponpes.id": {"Register": 55_000, "Renewal": 55_000, "Transfer": 55_000},
    ".sch.id": {"Register": 55_000, "Renewal": 55_000, "Transfer": 55_000},
    ".ac.id": {"Register": 55_000, "Renewal": 100_000, "Transfer": 55_000},
    ".or.id": {"Register": 55_000, "Renewal": 55_000, "Transfer": 55_000},
    ".web.id": {"Register": 55_000, "Renewal": 55_000, "Transfer": 55_000},
    ".id": {"Register": 210_000, "Renewal": 210_000, "Transfer": 210_000},
    ".co.id": {"Register": 270_000, "Renewal": 300_000, "Transfer": 300_000},
    ".net.id": {"Register": 400_000, "Renewal": 400_000, "Transfer": 400_000},
    ".top": {"Register": 121_000, "Renewal": 121_000, "Transfer": 121_000},
    ".xyz": {"Register": 292_000, "Renewal": 292_000, "Transfer": 292_000},
    ".asia": {"Register": 235_000, "Renewal": 235_000, "Transfer": 235_000},
    ".icu": {"Register": 287_300, "Renewal": 287_300, "Transfer": 287_300},
    ".com": {"Register": 160_000, "Renewal": 185_000, "Transfer": 185_000},
    ".click": {"Register": 190_000, "Renewal": 190_000, "Transfer": 190_000},
    ".net": {"Register": 295_000, "Renewal": 295_000, "Transfer": 295_000},
    ".org": {"Register": 230_000, "Renewal": 230_000, "Transfer": 230_000},
    ".info": {"Register": 451_000, "Renewal": 451_000, "Transfer": 451_000},
    ".vip": {"Register": 311_000, "Renewal": 311_000, "Transfer": 311_000},
    ".website": {"Register": 640_000, "Renewal": 640_000, "Transfer": 640_000},
    ".pw": {"Register": 415_000, "Renewal": 415_000, "Transfer": 415_000},
    ".space": {"Register": 640_000, "Renewal": 640_000, "Transfer": 640_000},
    ".co": {"Register": 641_000, "Renewal": 641_000, "Transfer": 641_000},
    ".site": {"Register": 721_000, "Renewal": 721_000, "Transfer": 721_000},
    ".com.sg": {"Register": 800_000, "Renewal": 800_000, "Transfer": 800_000},
    ".design": {"Register": 1_150_000, "Renewal": 1_150_000, "Transfer": 1_150_000},
    ".io": {"Register": 1_500_000, "Renewal": 1_500_000, "Transfer": 1_500_000},
}

def get_domain_extension(domain_name: str) -> str:
    normalized = domain_name.strip().lower()
    for extension in sorted(DOMAIN_PRICES_YEARLY, key=len, reverse=True):
        if normalized.endswith(extension):
            return extension
    return "Lainnya"

def get_domain_yearly_price(extension: str, action: str) -> int:
    if extension not in DOMAIN_PRICES_YEARLY:
        return DEFAULT_DOMAIN_PRICE_YEARLY
    return DOMAIN_PRICES_YEARLY[extension].get(action, DEFAULT_DOMAIN_PRICE_YEARLY)

def get_domain_period_price(domain: dict, duration_months: int) -> int:
    yearly_price = int(domain.get("price_yearly", 0))
    return int(round(yearly_price * duration_months / MONTHS_PER_YEAR))

def get_buffer_months(duration_months: int) -> float:
    """Scale the two-month annual VPS buffer to the application duration."""
    return duration_months * VPS_RESERVE_MONTHS_PER_YEAR / MONTHS_PER_YEAR

def format_duration_months(months: float) -> str:
    if months >= 1:
        return f"{months:g} bulan"

    weeks = months * 4
    rounded_weeks = round(weeks, 1)
    return f"{rounded_weeks:g} minggu"

def normalize_domain_entry(domain_entry):
    if isinstance(domain_entry, dict):
        domain_name = domain_entry.get("name", "").strip()
        action = domain_entry.get("action", "Register")
    else:
        domain_name = str(domain_entry).strip()
        action = "Register"

    if action not in DOMAIN_ACTION_OPTIONS:
        action = "Register"

    extension = get_domain_extension(domain_name)
    price = get_domain_yearly_price(extension, action)
    return {
        "name": domain_name,
        "extension": extension,
        "action": action,
        "price_yearly": price,
    }

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
        st.session_state["cpu_manual"] = p["cpu"]
        st.session_state["ram_manual"] = p["ram"]
        st.session_state["storage_manual"] = p["storage"]
        st.session_state["object_storage_gb_manual"] = st.session_state.get("object_storage_gb", 100)

def sync_sliders_to_load():
    """Triggered when users manually change traffic numbers"""
    u_hour = st.session_state.get("users_per_hour", 0)
    s_sec = st.session_state.get("session_seconds", 0)
    concurrent = ceil_div(int(u_hour * s_sec), 3600)
    
    # Auto-adjust hardware based on load
    new_cpu, new_ram = get_specs_from_concurrency(concurrent)
    st.session_state["cpu"] = new_cpu
    st.session_state["ram"] = new_ram
    st.session_state["cpu_manual"] = new_cpu
    st.session_state["ram_manual"] = new_ram
    
    # Switch radio to custom because we are departing from fixed presets
    st.session_state["preset_radio"] = CUSTOM_KEY

def auto_switch_to_custom():
    """Triggered when sliders are moved manually"""
    st.session_state["preset_radio"] = CUSTOM_KEY

def sync_load_to_specs():
    users_per_hour, session_seconds = get_load_from_specs(
        int(st.session_state.get("cpu", 1)),
        int(st.session_state.get("ram", 1)),
    )
    st.session_state["users_per_hour"] = users_per_hour
    st.session_state["session_seconds"] = session_seconds

def on_cpu_slider_change():
    auto_switch_to_custom()
    st.session_state["cpu_manual"] = st.session_state["cpu"]
    sync_load_to_specs()

def on_ram_slider_change():
    auto_switch_to_custom()
    st.session_state["ram_manual"] = st.session_state["ram"]
    sync_load_to_specs()

def on_storage_slider_change():
    auto_switch_to_custom()
    st.session_state["storage_manual"] = st.session_state["storage"]

def on_object_storage_slider_change():
    auto_switch_to_custom()
    st.session_state["object_storage_gb_manual"] = st.session_state["object_storage_gb"]

def on_cpu_manual_change():
    auto_switch_to_custom()
    st.session_state["cpu"] = st.session_state["cpu_manual"]
    sync_load_to_specs()

def on_ram_manual_change():
    auto_switch_to_custom()
    st.session_state["ram"] = st.session_state["ram_manual"]
    sync_load_to_specs()

def on_storage_manual_change():
    auto_switch_to_custom()
    st.session_state["storage"] = st.session_state["storage_manual"]

def on_object_storage_manual_change():
    auto_switch_to_custom()
    st.session_state["object_storage_gb"] = st.session_state["object_storage_gb_manual"]

def set_domain_action(index: int, action: str):
    domains = [normalize_domain_entry(domain) for domain in st.session_state.get("domains", [])]
    if 0 <= index < len(domains):
        domains[index] = normalize_domain_entry({"name": domains[index]["name"], "action": action})
        st.session_state["domains"] = domains

def set_new_domain_action(action: str):
    st.session_state["new_domain_action"] = action

def add_domain():
    domain_name = st.session_state.get("domain_name_input", "").strip()
    if not domain_name:
        return

    domains = st.session_state.setdefault("domains", [])
    action = st.session_state.get("new_domain_action", "Register")
    domain_entry = normalize_domain_entry({"name": domain_name, "action": action})
    if not any(normalize_domain_entry(existing)["name"].lower() == domain_name.lower() for existing in domains):
        domains.append(domain_entry)
    st.session_state["domain_name_input"] = ""

def remove_domain(index: int):
    domains = st.session_state.get("domains", [])
    if 0 <= index < len(domains):
        st.session_state["domains"] = domains[:index] + domains[index + 1:]

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

    object_storage_gb = data.get("object_storage_gb", 0)
    row("Object Storage", f"{object_storage_gb} GB")

    row("Tipe CPU", data.get("cpu_type", "—"))
    row("Durasi Aplikasi", f"{int(data.get('duration_months', 1))} bulan")
    domains = [normalize_domain_entry(domain) for domain in data.get("domains", [])]
    domain_label = ", ".join(
        f"{domain['name']} ({domain['action']}, {domain['extension']})"
        for domain in domains
    ) if domains else "Tidak ada"
    row("Domain", domain_label)

    row("Biaya VPS Dasar", f"Rp {int(data.get('base_price', 0)):,}{data.get('unit_label', '')}")
    if data.get("include_vps_buffer", True):
        row(
            f"Buffer {data.get('buffer_duration_label', '—')}",
            f"Rp {int(data.get('vps_buffer_price', 0)):,}{data.get('unit_label', '')}",
        )
    else:
        row("Buffer Server", "Tidak aktif")
    row("Biaya Object Storage", f"Rp {int(data.get('object_storage_price', 0)):,}{data.get('unit_label', '')}")
    if domains:
        for domain in domains:
            domain_period_price = get_domain_period_price(domain, int(data.get("duration_months", 1)))
            row(f"Domain {domain['name']}", f"Rp {domain_period_price:,}{data.get('unit_label', '')}")
    else:
        row("Biaya Domain", f"Rp {int(data.get('domain_price', 0)):,}{data.get('unit_label', '')}")
    row("Subtotal Pra-Pajak", f"Rp {int(data.get('pre_tax_subtotal', 0)):,}{data.get('unit_label', '')}")
    row("Monitoring (4%)", f"Rp {int(data.get('monitoring_fee', 0)):,}{data.get('unit_label', '')}")
    row("PPN (11%)", f"Rp {int(data.get('tax_fee', 0)):,}{data.get('unit_label', '')}")
    if data.get("include_security_scan", True):
        row(
            "Security Scan",
            f"Rp {int(data.get('security_scan_price', 0)):,}{data.get('unit_label', '')} "
            f"(Rp {int(data.get('security_scan_monthly_price', 0)):,}/bulan)",
        )
    else:
        row("Security Scan", "Tidak aktif")

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
    st.session_state["object_storage_gb"] = 100
    st.session_state["cpu_manual"] = PRESETS[0]["cpu"]
    st.session_state["ram_manual"] = PRESETS[0]["ram"]
    st.session_state["storage_manual"] = PRESETS[0]["storage"]
    st.session_state["object_storage_gb_manual"] = 100
    st.session_state["manual_override"] = False
    st.session_state["include_vps_buffer"] = True
    st.session_state["include_security_scan"] = True
    st.session_state["security_scan_monthly_price"] = SECURITY_SCAN_PER_PROJECT_MONTH
    st.session_state["domains"] = []
    st.session_state["new_domain_action"] = "Register"

if "new_domain_action" not in st.session_state:
    st.session_state["new_domain_action"] = "Register"

if "include_security_scan" not in st.session_state:
    st.session_state["include_security_scan"] = True

if "security_scan_monthly_price" not in st.session_state:
    st.session_state["security_scan_monthly_price"] = SECURITY_SCAN_PER_PROJECT_MONTH

if "duration_months" not in st.session_state:
    st.session_state["duration_months"] = 12

if "include_vps_buffer" not in st.session_state:
    st.session_state["include_vps_buffer"] = True

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
s1, s2, s3, s4 = st.columns(4)
with s1:
    st.slider("CPU (Core)", 1, 32, key="cpu", on_change=on_cpu_slider_change)
with s2:
    st.slider("RAM (GB)", 1, 128, key="ram", on_change=on_ram_slider_change)
with s3:
    st.slider("Storage (GB)", 20, 2000, step=10, key="storage", on_change=on_storage_slider_change)
with s4:
    st.slider("Object Storage (GB)", 0, 10000, step=10, key="object_storage_gb", on_change=on_object_storage_slider_change)

st.toggle("Manual type override", key="manual_override")
if st.session_state.manual_override:
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.number_input("CPU (manual)", min_value=1, max_value=32, key="cpu_manual", on_change=on_cpu_manual_change)
    with m2:
        st.number_input("RAM (manual)", min_value=1, max_value=128, key="ram_manual", on_change=on_ram_manual_change)
    with m3:
        st.number_input("Storage (manual)", min_value=20, max_value=2000, step=10, key="storage_manual", on_change=on_storage_manual_change)
    with m4:
        st.number_input("Object Storage (manual)", min_value=0, max_value=10000, step=10, key="object_storage_gb_manual", on_change=on_object_storage_manual_change)

st.subheader("Domain")
st.write("Jenis domain baru")
new_domain_action = st.session_state.get("new_domain_action", "Register")
new_action_cols = st.columns(3)
for action_index, action in enumerate(DOMAIN_ACTION_OPTIONS):
    new_action_cols[action_index].button(
        action,
        key=f"new_domain_{action.lower()}",
        on_click=set_new_domain_action,
        args=(action,),
        type="primary" if new_domain_action == action else "secondary",
        use_container_width=True,
    )
st.caption(f"Domain baru akan ditambahkan sebagai: {new_domain_action}")

d1, d2 = st.columns([3, 1])
with d1:
    st.text_input("Nama domain", placeholder="contoh: datalab.co.id", key="domain_name_input")
with d2:
    st.write("")
    st.button("Tambah Domain", on_click=add_domain, use_container_width=True)

domains = [normalize_domain_entry(domain) for domain in st.session_state.get("domains", [])]
st.session_state["domains"] = domains
if domains:
    st.caption("Pilih Register, Renewal, atau Transfer untuk masing-masing domain.")
    for index, domain in enumerate(domains):
        st.markdown(f"**{domain['name']}**")
        st.caption(f"{domain['extension']} | {domain['action']} | Rp {domain['price_yearly']:,}/tahun")
        action_cols = st.columns([1, 1, 1, 1])
        for action_index, action in enumerate(DOMAIN_ACTION_OPTIONS):
            action_cols[action_index].button(
                action,
                key=f"domain_{index}_{action.lower()}",
                on_click=set_domain_action,
                args=(index, action),
                type="primary" if domain["action"] == action else "secondary",
                use_container_width=True,
            )
        action_cols[3].button(
            "Hapus",
            key=f"remove_domain_{index}",
            on_click=remove_domain,
            args=(index,),
            use_container_width=True,
        )
        st.divider()
else:
    st.caption("Belum ada domain yang ditambahkan. Tambahkan domain dulu, lalu pilih Register, Renewal, atau Transfer pada domain tersebut.")

variant = st.radio("Tipe CPU", list(cloud_vps_data.keys()), key="variant")
duration_months = st.number_input(
    "Durasi aplikasi (bulan)",
    min_value=1,
    max_value=120,
    step=1,
    key="duration_months",
    help="Semua biaya bulanan dan buffer akan disesuaikan dengan durasi ini.",
)

st.subheader("Buffer Server")
st.toggle(
    "Tambahkan buffer server",
    key="include_vps_buffer",
    help="Jika aktif, buffer dihitung proporsional sebesar 2 bulan untuk setiap 12 bulan durasi aplikasi.",
)

st.subheader("Security Scan")
sec1, sec2 = st.columns([1, 1])
with sec1:
    st.toggle("Tambahkan security scan", key="include_security_scan")
with sec2:
    st.number_input(
        "Biaya security scan per bulan",
        min_value=0,
        step=10_000,
        key="security_scan_monthly_price",
        disabled=not st.session_state.include_security_scan,
    )

coef = cloud_vps_data[variant]
monthly_base_price = calculate_cloud_vps(st.session_state.cpu, st.session_state.ram, st.session_state.storage, coef)
duration_months = int(duration_months)
buffer_months = get_buffer_months(duration_months)
buffer_duration_label = format_duration_months(buffer_months)
unit_label = f" ({duration_months} bulan)"
domains = [normalize_domain_entry(domain) for domain in st.session_state.get("domains", [])]
security_scan_monthly_price = (
    int(st.session_state.security_scan_monthly_price)
    if st.session_state.include_security_scan
    else 0
)
base_price = monthly_base_price * duration_months
vps_buffer_price = (
    int(round(monthly_base_price * buffer_months))
    if st.session_state.include_vps_buffer
    else 0
)
object_storage_price = int(round(
    st.session_state.object_storage_gb * OBJECT_STORAGE_PER_GB_MONTH * duration_months
))
security_scan_price = security_scan_monthly_price * duration_months
domain_cost_items = [
    {
        **domain,
        "period_price": get_domain_period_price(domain, duration_months),
    }
    for domain in domains
]
domain_price = sum(domain["period_price"] for domain in domain_cost_items)

pre_tax_subtotal = base_price + vps_buffer_price + object_storage_price + domain_price
monitoring_fee = int(pre_tax_subtotal * 0.04)
tax_fee = int((pre_tax_subtotal + monitoring_fee) * 0.11)
total_price = pre_tax_subtotal + monitoring_fee + tax_fee + security_scan_price

st.markdown(f"""
    <div style='text-align:center; background:#f0f2f6; padding:20px; border-radius:10px;'>
        <p style='margin:0;'>💰 <b>Biaya Total (VPS + Object Storage + Domain + Monitoring 4% + PPN 11%)</b></p>
        <h2 style='margin:0; color:#1f77b4;'>Rp {int(total_price):,}{unit_label}</h2>
    </div>
""", unsafe_allow_html=True)

st.caption(
    f"Tarif Object Storage: Rp {OBJECT_STORAGE_PER_GB_MONTH:,}/GB/bulan "
    f"(~Rp {OBJECT_STORAGE_PER_GB_HOUR}/GB/jam) | Security Scan opsional: Rp {security_scan_monthly_price:,}/bulan/proyek. "
    f"Domain mengikuti ekstensi dan jenis domain yang dipilih. "
    + (
        f"Buffer server {buffer_duration_label} dihitung proporsional dari durasi aplikasi "
        f"({VPS_RESERVE_MONTHS_PER_YEAR} bulan buffer per tahun)."
        if st.session_state.include_vps_buffer
        else "Buffer server tidak aktif."
    )
)

st.markdown("**Rincian biaya:**")
st.write(f"- VPS dasar: Rp {int(base_price):,}{unit_label}")
if st.session_state.include_vps_buffer:
    st.write(f"- Buffer {buffer_duration_label}: Rp {int(vps_buffer_price):,}{unit_label}")
else:
    st.write("- Buffer server: tidak aktif")
st.write(f"- Object storage: Rp {int(object_storage_price):,}{unit_label}")
if domain_cost_items:
    for domain in domain_cost_items:
        st.write(f"- Domain {domain['name']} ({domain['action']}): Rp {domain['period_price']:,}{unit_label}")
else:
    st.write(f"- Domain: Rp 0{unit_label}")
st.write(f"- Subtotal pra-pajak: Rp {int(pre_tax_subtotal):,}{unit_label}")
st.write(f"- Monitoring 4%: Rp {int(monitoring_fee):,}{unit_label}")
st.write(f"- PPN 11%: Rp {int(tax_fee):,}{unit_label}")
security_scan_label = "aktif" if st.session_state.include_security_scan else "tidak aktif"
st.write(f"- Security scan ({security_scan_label}, non-pajak): Rp {int(security_scan_price):,}{unit_label}")

st.divider()
# Dedicated collapsible explanation under estimator
with st.expander("📐 Penjelasan Perhitungan", expanded=False):
    st.write("### Metodologi Estimasi")
    
    # Using st.latex for better centering and font rendering
    st.markdown("**Rumus Concurrent Users (CU):**")
    st.latex(r"CU = \frac{\text{User per Jam} \times \text{Durasi Sesi (detik)}}{3600}")
    st.markdown("**Rumus biaya komponen:**")
    st.latex(r"Bulan_{buffer} = Jumlah_{bulan} \times \frac{2}{12}")
    st.latex(r"Buffer_{server} = Biaya_{VPS\ bulanan} \times Bulan_{buffer}")
    st.latex(r"Biaya_{objek} = GB_{objek} \times 507 \times Jumlah_{bulan}")
    st.latex(r"Biaya_{domain} = \sum Harga_{domain\ per\ ekstensi}")
    st.latex(r"Subtotal_{kena\ pajak} = Biaya_{VPS} + Buffer_{server} + Biaya_{objek} + Biaya_{domain}")
    st.latex(r"Security_{scan} = Biaya_{security\ scan\ bulanan} \times Jumlah_{bulan}")
    st.latex(r"Total = (Subtotal_{kena\ pajak} + 4\%\times Subtotal_{kena\ pajak})\times(1 + 11\%) + Security_{scan}")

    st.info("""
    **Parameter Acuan:**
    * **RAM Dasar:** 1–2 GB (Alokasi OS & Service background).
    * **RAM per Request:** ±16–32 MB (Standar PHP-FPM atau Node.js).
    * **Kapasitas CPU:** 1 vCPU modern mampu menangani ≈ 20–50 req/detik.
    """)
    
    st.warning("⚠️ **Catatan:** Durasi sesi dibatasi sesuai timeout agar estimasi tetap realistis.")

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
    "object_storage_gb": st.session_state.object_storage_gb,
    "domains": st.session_state.get("domains", []),
    "duration_months": duration_months,
    "include_vps_buffer": st.session_state.include_vps_buffer,
    "buffer_duration_label": buffer_duration_label,
    "cpu_type": variant,
    "base_price": base_price,
    "vps_buffer_price": vps_buffer_price,
    "object_storage_price": object_storage_price,
    "include_security_scan": st.session_state.include_security_scan,
    "security_scan_monthly_price": security_scan_monthly_price,
    "security_scan_price": security_scan_price,
    "domain_price": domain_price,
    "pre_tax_subtotal": pre_tax_subtotal,
    "monitoring_fee": monitoring_fee,
    "tax_fee": tax_fee,
    "total_price": total_price,
    "unit_label": unit_label,
})

st.download_button(
    label="📄 Export PDF Estimasi Infrastruktur",
    data=pdf_bytes,
    file_name=f"DLI_Estimasi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
    mime="application/pdf",
)
