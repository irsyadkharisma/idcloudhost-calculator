import json
import streamlit as st


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


def recommend_from_concurrency(concurrent: int, product_type: str) -> str:
    if concurrent <= 20:
        rec = "1 vCPU / 2 GB RAM"
    elif concurrent <= 60:
        rec = "2 vCPU / 4 GB RAM"
    elif concurrent <= 150:
        rec = "4 vCPU / 8 GB RAM"
    elif concurrent <= 400:
        rec = "8 vCPU / 16 GB RAM"
    else:
        rec = "8 vCPU / 32 GB RAM (atau lebih)"

    # LLM tends to be heavier
    if product_type == "AI Model (LLM)":
        if rec.startswith("1 vCPU"):
            rec = "2 vCPU / 4 GB RAM"
        elif rec.startswith("2 vCPU"):
            rec = "4 vCPU / 8 GB RAM"
        elif rec.startswith("4 vCPU / 8"):
            rec = "4 vCPU / 16 GB RAM"

    return rec


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
# Main UI (single page)
# ----------------------------
st.title("Estimasi spesifikasi dan biaya infrastruktur digital")

# Load CPU type coefficients
with open("data/cloud_vps_coeff.json") as f:
    cloud_vps_data = json.load(f)

# ===== Smart Estimator =====
with st.expander("🔎 Belum tahu butuh spek apa? Gunakan Smart Estimator", expanded=True):
    st.markdown("### Tipe Produk")
    product_type = st.radio(
        " ",
        ["Web/Mobile App", "AI Model (LLM)"],
        horizontal=True,
        label_visibility="collapsed",
        key="product_type",
    )

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
    # Set default to 3600 seconds (1 hour). You can change this.
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
    rec_text = recommend_from_concurrency(concurrent, product_type)

    st.markdown(
        f"""
        <div class="rec-box">
            💡 <b>Saran:</b> {rec_text} (untuk ~{concurrent} concurrent users)
        </div>
        """,
        unsafe_allow_html=True,
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
    monitoring_fee = 120_000
    unit_label = "/tahun"
else:
    monitoring_fee = 10_000
    unit_label = "/bulan"

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
