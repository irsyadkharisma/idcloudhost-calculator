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
# Pricing logic (mirrors extreme_custom.py logic)
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
# Presets with descriptions
# ----------------------------
CUSTOM_KEY = "Custom (manual sliders)"

PRESETS = [
    {
        "key": "Staging/Testing",
        "label": "1 vCPU / 1 GB",
        "desc": "Dev/staging, mock API, testing ringan, traffic kecil.",
        "cpu": 1, "ram": 1, "storage": 20,
    },
    {
        "key": "Personal Blog/Portfolio",
        "label": "2 vCPU / 1 GB",
        "desc": "Blog/portfolio, landing page, web ringan.",
        "cpu": 2, "ram": 1, "storage": 20,
    },
    {
        "key": "Medium Web App/API",
        "label": "2 vCPU / 6–8 GB",
        "desc": "Web app menengah, API, panel admin, CRUD, worker ringan.",
        "cpu": 2, "ram": 8, "storage": 40,
    },
    {
        "key": "Moderate Web/API",
        "label": "4 vCPU / 8 GB",
        "desc": "Website/API moderat, background jobs, caching basic, multi-worker.",
        "cpu": 4, "ram": 8, "storage": 60,
    },
    {
        "key": "High-load API Gateway",
        "label": "4 vCPU / 16 GB",
        "desc": "Service berat, gateway, latency-sensitive, throughput tinggi.",
        "cpu": 4, "ram": 16, "storage": 80,
    },
    {
        "key": "High-traffic/API",
        "label": "8 vCPU / 16–32 GB",
        "desc": "Traffic tinggi, banyak concurrent, heavy caching/queue, autoscale candidate.",
        "cpu": 8, "ram": 32, "storage": 120,
    },
]

PRESET_MAP = {p["key"]: p for p in PRESETS}

# Radio labels: "Medium Web App/API: desc... (2 vCPU / 6–8 GB)"
RADIO_OPTIONS = [f'{p["key"]}: {p["desc"]} ({p["label"]})' for p in PRESETS] + [CUSTOM_KEY]


def preset_key_from_radio(radio_value: str) -> str:
    if radio_value == CUSTOM_KEY:
        return CUSTOM_KEY
    return radio_value.split(":", 1)[0].strip()


# ----------------------------
# State sync callbacks
# ----------------------------
def apply_preset_to_sliders():
    chosen_radio = st.session_state.get("preset_radio", RADIO_OPTIONS[0])
    key = preset_key_from_radio(chosen_radio)
    if key in PRESET_MAP:
        p = PRESET_MAP[key]
        st.session_state["cpu"] = p["cpu"]
        st.session_state["ram"] = p["ram"]
        st.session_state["storage"] = p["storage"]


def auto_switch_to_custom_if_sliders_changed():
    chosen_radio = st.session_state.get("preset_radio", RADIO_OPTIONS[0])
    key = preset_key_from_radio(chosen_radio)
    if key == CUSTOM_KEY:
        return
    if key not in PRESET_MAP:
        return

    p = PRESET_MAP[key]
    if (
        st.session_state.get("cpu") != p["cpu"]
        or st.session_state.get("ram") != p["ram"]
        or st.session_state.get("storage") != p["storage"]
    ):
        st.session_state["preset_radio"] = CUSTOM_KEY


# ----------------------------
# PDF Export (Landscape)
# ----------------------------
def build_pdf_report(data: dict) -> bytes:
    """
    data keys expected:
    - exported_at_str
    - preset_label
    - users_per_hour
    - session_seconds
    - concurrent_users
    - recommendation
    - cpu, ram, storage
    - cpu_type
    - billing
    - base_price, vat_price, total_price
    - unit_label
    - max_duration_seconds
    """
    buf = BytesIO()

    # Landscape PDF
    page_size = landscape(A4)
    c = canvas.Canvas(buf, pagesize=page_size)
    width, height = page_size

    margin_x = 2 * cm
    y = height - 2 * cm

    # Header / Kop
    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin_x, y, "DATA LAB INDONESIA (DLI)")
    c.setFont("Helvetica", 10)
    c.drawString(margin_x, y - 14, "Estimasi spesifikasi dan biaya infrastruktur digital")
    c.setFont("Helvetica", 9)
    c.drawRightString(width - margin_x, y, f"Tanggal Export: {data['exported_at_str']}")
    c.setStrokeColorRGB(0.2, 0.2, 0.2)
    c.line(margin_x, y - 22, width - margin_x, y - 22)

    y -= 45

    def row(label: str, value: str, y_pos: float):
        c.setFont("Helvetica-Bold", 10)
        c.drawString(margin_x, y_pos, label)
        c.setFont("Helvetica", 10)
        c.drawString(margin_x + 7.0 * cm, y_pos, value)

    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin_x, y, "Ringkasan Estimasi")
    y -= 18

    row("Preset", str(data["preset_label"]), y); y -= 14
    row("User per Jam", f"{int(data['users_per_hour']):,}", y); y -= 14
    row("Durasi Sesi (detik)", f"{int(data['session_seconds']):,}", y); y -= 14
    row("Concurrent Users (CU)", f"~{int(data['concurrent_users']):,}", y); y -= 16

    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin_x, y, "Saran Spesifikasi")
    y -= 14
    c.setFont("Helvetica", 10)
    rec = str(data["recommendation"])
    max_chars = 120  # landscape gives more room
    for i in range(0, len(rec), max_chars):
        c.drawString(margin_x, y, rec[i:i + max_chars])
        y -= 12

    y -= 6
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin_x, y, "Konfigurasi & Biaya")
    y -= 18

    row("CPU / RAM / Storage", f"{data['cpu']} vCPU / {data['ram']} GB / {data['storage']} GB", y); y -= 14
    row("Tipe CPU", str(data["cpu_type"]), y); y -= 14
    row("Periode", str(data["billing"]), y); y -= 14
    row("Biaya Dasar", f"Rp {int(data['base_price']):,}{data['unit_label']}", y); y -= 14
    row("Biaya + PPN (11%)", f"Rp {int(data['vat_price']):,}{data['unit_label']}", y); y -= 14
    row("Biaya Total (Final)", f"Rp {int(data['total_price']):,}{data['unit_label']}", y); y -= 18

    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin_x, y, "Rumus Dasar")
    y -= 12
    c.setFont("Helvetica", 10)
    c.drawString(margin_x, y, "CU = (User per Jam × Durasi Sesi (detik)) / 3600")
    y -= 12
    c.setFont("Helvetica", 9)
    c.drawString(margin_x, y, f"Catatan: Durasi sesi dibatasi (timeout) maks {int(data['max_duration_seconds']):,} detik.")
    y -= 24

    # Footer
    c.setStrokeColorRGB(0.8, 0.8, 0.8)
    c.line(margin_x, 2.2 * cm, width - margin_x, 2.2 * cm)
    c.setFont("Helvetica", 9)
    c.drawString(margin_x, 1.7 * cm, "by Data Lab Indonesia")
    c.drawRightString(width - margin_x, 1.7 * cm, "Generated via Smart Estimator")

    c.showPage()
    c.save()
    return buf.getvalue()


# ----------------------------
# Main UI (single page)
# ----------------------------
st.title("Estimasi spesifikasi dan biaya infrastruktur digital")

# Load CPU type coefficients
with open("data/cloud_vps_coeff.json") as f:
    cloud_vps_data = json.load(f)

# We store these for export later
rec_text = ""
concurrent = 0

# ===== Smart Estimator =====
with st.expander("🔎 Belum tahu butuh spek apa? Gunakan Smart Estimator", expanded=True):

    st.markdown("### Pilih preset (opsional)")
    if "preset_radio" not in st.session_state:
        st.session_state["preset_radio"] = RADIO_OPTIONS[0]

    # ONE radio, styled into 2 columns
    st.markdown('<div class="preset-radio">', unsafe_allow_html=True)
    st.radio(
        " ",
        RADIO_OPTIONS,
        key="preset_radio",
        label_visibility="collapsed",
        on_change=apply_preset_to_sliders,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("### Beban Aplikasi")

    # Timeout / maximum duration
    max_duration_seconds = 3600

    c1, c2 = st.columns(2, gap="large")
    with c1:
        users_per_hour = st.number_input(
            "User per Jam:",
            min_value=0,
            value=1000,
            step=50,
            key="users_per_hour",
        )
    with c2:
        session_seconds = st.number_input(
            "Durasi Sesi (detik):",
            min_value=1,
            value=60,
            step=5,
            help=f"Maks durasi disarankan: {max_duration_seconds} detik (umumnya timeout/load balancer/app session).",
            key="session_seconds",
        )

    # Clamp absurd duration
    if session_seconds > max_duration_seconds:
        st.warning(
            f"Durasi sesi kamu {int(session_seconds):,} detik. Itu bukan sesi, itu hubungan jangka panjang. "
            f"Untuk estimasi ini, durasi dibatasi ke {max_duration_seconds} detik (timeout umum)."
        )
        session_seconds = max_duration_seconds
        st.session_state["session_seconds"] = max_duration_seconds

    concurrent = ceil_div(int(users_per_hour * session_seconds), 3600)
    rec_text = recommend_from_concurrency(concurrent)

    # store for export
    st.session_state["concurrent"] = concurrent
    st.session_state["rec_text"] = rec_text
    st.session_state["max_duration_seconds"] = max_duration_seconds

    st.markdown(
        f"""
        <div class="rec-box">
            💡 <b>Saran:</b> {rec_text} (untuk ~{concurrent} concurrent users)
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Dedicated collapsible explanation under estimator (collapsed by default)
    with st.expander("📐 Penjelasan Perhitungan", expanded=False):
        st.markdown(
            r"""
**Rumus Concurrent Users (CU):**  
\[
CU = \frac{\text{User per Jam} \times \text{Durasi Sesi (detik)}}{3600}
\]

**Estimasi RAM:**  
\[
RAM = RAM_{dasar} + (CU \times RAM_{per\ request})
\]

- RAM dasar: 1–2 GB (OS + service)  
- RAM per request: ±16–32 MB (PHP / Node.js ringan)

**Estimasi CPU:**
- 1 vCPU modern ≈ 20–50 request/detik (task ringan)  
- Untuk trafik tinggi, disarankan **horizontal scaling** dengan load balancer  

⚠️ Durasi sesi dibatasi sesuai timeout aplikasi / load balancer agar estimasi tetap realistis.
            """
        )

st.divider()

# ===== Sliders + CPU Type + Costs =====
st.subheader("Customisasi Spesifikasi")

# Initialize slider values from first preset
if "cpu" not in st.session_state:
    p0 = PRESETS[0]
    st.session_state["cpu"] = p0["cpu"]
    st.session_state["ram"] = p0["ram"]
    st.session_state["storage"] = p0["storage"]

s1, s2, s3 = st.columns(3, gap="large")
with s1:
    st.slider(
        "CPU (Core)",
        min_value=1,
        max_value=32,
        value=int(st.session_state["cpu"]),
        key="cpu",
        on_change=auto_switch_to_custom_if_sliders_changed,
    )
with s2:
    st.slider(
        "RAM (GB)",
        min_value=1,
        max_value=128,
        value=int(st.session_state["ram"]),
        key="ram",
        on_change=auto_switch_to_custom_if_sliders_changed,
    )
with s3:
    st.slider(
        "Storage (GB)",
        min_value=20,
        max_value=2000,
        value=int(st.session_state["storage"]),
        step=10,
        key="storage",
        on_change=auto_switch_to_custom_if_sliders_changed,
    )

st.markdown("### Tipe CPU")
variant = st.radio(
    " ",
    list(cloud_vps_data.keys()),
    horizontal=False,
    label_visibility="collapsed",
    key="variant",
)

billing = st.radio("Periode Pembayaran", ["Bulanan", "Tahunan"], horizontal=True, key="billing")

# ---- Cost Results ----
coef = cloud_vps_data[variant]
cpu = int(st.session_state["cpu"])
ram = int(st.session_state["ram"])
storage = int(st.session_state["storage"])

base_price = calculate_cloud_vps(cpu, ram, storage, coef)

if billing == "Tahunan":
    base_price *= 12
    unit_label = "/tahun"
else:
    unit_label = "/bulan"

monitoring_fee = int(base_price * 0.04)

vat_price = base_price * 1.11
total_price = (base_price + monitoring_fee) * 1.11

st.markdown("## 💰 Perincian Biaya " + ("Tahunan" if billing == "Tahunan" else "Bulanan"))

c1, c2, c3 = st.columns(3, gap="large")
with c1:
    st.markdown(
        f"<p style='font-size:14px; margin-bottom:4px;'>Biaya Dasar</p>"
        f"<p style='font-size:18px; font-weight:600;'>Rp {int(base_price):,}{unit_label}</p>",
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        f"<p style='font-size:14px; margin-bottom:4px;'>Biaya + PPN (11%)</p>"
        f"<p style='font-size:18px; font-weight:600;'>Rp {int(vat_price):,}{unit_label}</p>",
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        f"<p style='font-size:14px; margin-bottom:4px;'>Biaya + PPN + Monitoring</p>"
        f"<p style='font-size:18px; font-weight:600;'>Rp {int(total_price):,}{unit_label}</p>",
        unsafe_allow_html=True,
    )

st.markdown(
    f"""
    <div style='text-align:center; margin-top: 8px;'>
      <p style='font-size:15px;'>💰 <b>Biaya Total / Final</b></p>
      <h2 style='margin-top:-6px;'>Rp {int(total_price):,}{unit_label}</h2>
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption(
    f"Biaya sudah termasuk PPN 11% dan biaya monitoring wajib sebesar Rp {monitoring_fee:,} "
    f"per {'tahun' if billing == 'Tahunan' else 'bulan'}. Semua nilai dibulatkan ke ribuan terdekat."
)

st.info(
    f"Preset aktif: **{st.session_state.get('preset_radio', RADIO_OPTIONS[0])}** | "
    f"Specs: **{cpu} vCPU / {ram} GB RAM / {storage} GB** | CPU Type: **{variant}**"
)

# ===== Export PDF =====
st.divider()
st.subheader("Export PDF")

exported_at = datetime.now()
exported_at_str = exported_at.strftime("%d-%m-%Y %H:%M:%S")

pdf_bytes = build_pdf_report({
    "exported_at_str": exported_at_str,
    "preset_label": st.session_state.get("preset_radio", "—"),
    "users_per_hour": st.session_state.get("users_per_hour", 0),
    "session_seconds": st.session_state.get("session_seconds", 0),
    "concurrent_users": st.session_state.get("concurrent", concurrent),
    "recommendation": st.session_state.get("rec_text", rec_text),
    "cpu": cpu,
    "ram": ram,
    "storage": storage,
    "cpu_type": variant,
    "billing": billing,
    "base_price": base_price,
    "vat_price": vat_price,
    "total_price": total_price,
    "unit_label": unit_label,
    "max_duration_seconds": st.session_state.get("max_duration_seconds", 3600),
})

filename = f"DLI_Estimasi_Infrastruktur_{exported_at.strftime('%Y%m%d_%H%M%S')}.pdf"

st.download_button(
    label="📄 Download PDF (by Data Lab Indonesia)",
    data=pdf_bytes,
    file_name=filename,
    mime="application/pdf",
)

