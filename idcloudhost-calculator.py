import streamlit as st
import pandas as pd

from extreme_custom import render_cloud_vps
from paket_server import render_server_vps


# ----------------------------
# Config
# ----------------------------
st.set_page_config(page_title="IDCloudHost Calculator", page_icon="💰", layout="wide")
st.markdown(
    """
    <style>
        .block-container { max-width: 1200px; padding-left: 3rem; padding-right: 3rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------
# Presets for Smart Estimator + Sliders
# ----------------------------
PRESETS = {
    "1 vCPU / 1 GB — Staging / Testing": {"cpu": 1, "ram": 1, "storage": 20},
    "2 vCPU / 1 GB — Personal Blog / Portfolio": {"cpu": 2, "ram": 1, "storage": 20},
    "2 vCPU / 6–8 GB — Medium Web App / API": {"cpu": 2, "ram": 8, "storage": 40},
    "4 vCPU / 8 GB — Moderate Web / API": {"cpu": 4, "ram": 8, "storage": 60},
    "4 vCPU / 16 GB — High-load API Gateway": {"cpu": 4, "ram": 16, "storage": 80},
    "8 vCPU / 16–32 GB — High-traffic / API": {"cpu": 8, "ram": 32, "storage": 120},
    # GPU preset intentionally excluded from sliders (since sliders are CPU/RAM/Storage)
}
CUSTOM_KEY = "Custom (manual sliders)"


def ceil_div(a: int, b: int) -> int:
    return (a + b - 1) // b


def recommend_from_concurrency(concurrent: int, product_type: str) -> str:
    # Base heuristic
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

    # Nudge up for LLM workloads
    if product_type == "AI Model (LLM)":
        if rec.startswith("1 vCPU"):
            rec = "2 vCPU / 4 GB RAM"
        elif rec.startswith("2 vCPU"):
            rec = "4 vCPU / 8 GB RAM"
        elif rec.startswith("4 vCPU / 8"):
            rec = "4 vCPU / 16 GB RAM"

    return rec


def sync_sliders_to_selected_preset():
    """If preset selected (not Custom), set sliders to that preset."""
    chosen = st.session_state.get("preset_choice")
    if chosen in PRESETS:
        spec = PRESETS[chosen]
        st.session_state["cpu"] = spec["cpu"]
        st.session_state["ram"] = spec["ram"]
        st.session_state["storage"] = spec["storage"]


def auto_switch_to_custom_if_slider_changed():
    """If user touches sliders and they don't match the currently selected preset, switch radio to Custom."""
    chosen = st.session_state.get("preset_choice")

    # If currently Custom, do nothing.
    if chosen == CUSTOM_KEY:
        return

    # If preset chosen but sliders no longer match it, flip to Custom.
    if chosen in PRESETS:
        spec = PRESETS[chosen]
        cpu = st.session_state.get("cpu")
        ram = st.session_state.get("ram")
        storage = st.session_state.get("storage")
        if cpu != spec["cpu"] or ram != spec["ram"] or storage != spec["storage"]:
            st.session_state["preset_choice"] = CUSTOM_KEY


# ----------------------------
# UI
# ----------------------------
st.title("Estimasi spesifikasi dan biaya infrastruktur digital")

# ---- Smart Estimator block (like your second image)
with st.expander("🔎 Belum tahu butuh spek apa? Gunakan Smart Estimator", expanded=True):
    st.markdown("### Tipe Produk")
    product_type = st.radio(
        " ",
        ["Web/Mobile App", "AI Model (LLM)"],
        horizontal=True,
        label_visibility="collapsed",
        key="product_type",
    )

    st.markdown("### Pilih preset (opsional) / atau Custom via slider")

    preset_options = list(PRESETS.keys()) + [CUSTOM_KEY]
    # Default: first preset, like screenshot
    if "preset_choice" not in st.session_state:
        st.session_state["preset_choice"] = preset_options[0]

    # Show presets in two columns (like screenshot)
    left, right = st.columns(2, gap="large")
    left_presets = preset_options[:2]  # first two on the left
    right_presets = preset_options[2:]  # rest on the right

    # We render two radios but keep one shared state by writing into session_state["preset_choice"].
    # Streamlit doesn't natively do "one radio split in two columns" cleanly, so we fake it.
    with left:
        picked_left = st.radio(
            " ",
            left_presets,
            index=left_presets.index(st.session_state["preset_choice"]) if st.session_state["preset_choice"] in left_presets else 0,
            key="preset_left",
            label_visibility="collapsed",
        )
    with right:
        default_right_index = 0
        if st.session_state["preset_choice"] in right_presets:
            default_right_index = right_presets.index(st.session_state["preset_choice"])
        picked_right = st.radio(
            " ",
            right_presets,
            index=default_right_index,
            key="preset_right",
            label_visibility="collapsed",
        )

    # Decide which one user actually selected this run:
    # Priority: if they clicked right, it changes; if they clicked left, it changes.
    # We'll detect by comparing to stored state.
    prev_choice = st.session_state["preset_choice"]

    # If previous choice was on left and user picked a right value, switch
    # Or if previous choice was on right and user picked a left value, switch
    # Or if they re-picked same side, keep it.
    if prev_choice in left_presets:
        # if right radio moved away from its default representing prev_choice, accept it
        if picked_right != (right_presets[0] if prev_choice not in right_presets else prev_choice):
            st.session_state["preset_choice"] = picked_right
        else:
            st.session_state["preset_choice"] = picked_left
    else:
        # prev on right side
        if picked_left != (left_presets[0] if prev_choice not in left_presets else prev_choice):
            st.session_state["preset_choice"] = picked_left
        else:
            st.session_state["preset_choice"] = picked_right

    # When preset changes (and isn't Custom), snap sliders to it
    if st.session_state["preset_choice"] != prev_choice:
        sync_sliders_to_selected_preset()

    st.markdown("### Beban Aplikasi")
    c1, c2 = st.columns(2, gap="large")
    with c1:
        users_per_hour = st.number_input("User per Jam:", min_value=0, value=1000, step=50, key="users_per_hour")
    with c2:
        session_seconds = st.number_input("Durasi Sesi (detik):", min_value=1, value=60, step=5, key="session_seconds")

    concurrent = ceil_div(int(users_per_hour * session_seconds), 3600)
    rec_text = recommend_from_concurrency(concurrent, product_type)

    st.markdown(
        f"""
        <div style="
            background:#eaf3ff;
            border-left:4px solid #3b82f6;
            padding:16px;
            border-radius:8px;
            font-weight:600;
        ">
            💡 <b>Saran:</b> {rec_text} (untuk ~{concurrent} concurrent users)
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---- Sliders (like your third image)
st.subheader("Customisasi Spesifikasi (Slider)")
st.caption("Pilih preset untuk auto-fill, atau geser slider untuk mode Custom (radio akan otomatis pindah).")

# Initialize slider values (if not set yet)
if "cpu" not in st.session_state:
    st.session_state["cpu"] = PRESETS[preset_options[0]]["cpu"]
if "ram" not in st.session_state:
    st.session_state["ram"] = PRESETS[preset_options[0]]["ram"]
if "storage" not in st.session_state:
    st.session_state["storage"] = PRESETS[preset_options[0]]["storage"]

s1, s2, s3 = st.columns(3, gap="large")
with s1:
    st.slider("CPU (Core)", min_value=1, max_value=32, value=st.session_state["cpu"], key="cpu", on_change=auto_switch_to_custom_if_slider_changed)
with s2:
    st.slider("RAM (GB)", min_value=1, max_value=128, value=st.session_state["ram"], key="ram", on_change=auto_switch_to_custom_if_slider_changed)
with s3:
    st.slider("Storage (GB)", min_value=20, max_value=2000, value=st.session_state["storage"], step=10, key="storage", on_change=auto_switch_to_custom_if_slider_changed)

st.info(
    f"Preset aktif: **{st.session_state['preset_choice']}** | "
    f"Spesifikasi sekarang: **{st.session_state['cpu']} vCPU / {st.session_state['ram']} GB RAM / {st.session_state['storage']} GB Storage**"
)

st.divider()

# ---- Existing calculator sections
st.subheader("Kalkulator VPS dan Paket Server")
mode = st.radio("Pilih Kategori Produk:", ["Cloud VPS eXtreme", "Paket Server VPS"], horizontal=True, key="mode")

if mode == "Cloud VPS eXtreme":
    render_cloud_vps()
else:
    render_server_vps()
