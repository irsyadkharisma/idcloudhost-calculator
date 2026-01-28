import re
import pandas as pd
import streamlit as st

from extreme_custom import render_cloud_vps
from paket_server import render_server_vps


# ----------------------------
# Helpers: Recommendation table
# ----------------------------
def _parse_vcpu(value) -> int:
    """Extract numeric value of vCPU for sorting."""
    match = re.search(r"(\d+)", str(value))
    return int(match.group(1)) if match else 999  # GPU/high RAM goes last


def render_server_recommendation():
    st.subheader("Rekomendasi Server Berdasarkan Penggunaan")

    try:
        df = pd.read_csv("data/server_recommendation.csv")
        df.columns = df.columns.str.strip()

        desired_order = ["Specs", "Storage", "Typical Load", "Use Case", "Description"]
        existing_columns = [col for col in desired_order if col in df.columns]
        df = df[existing_columns]

        df["SortKey"] = df["Specs"].apply(_parse_vcpu)
        df = df.sort_values("SortKey").drop(columns=["SortKey"])

        st.dataframe(df, use_container_width=True, hide_index=True)
        st.caption("Gunakan tabel di atas sebagai acuan awal sebelum menghitung biaya VPS yang sesuai.")
    except FileNotFoundError:
        st.error("File 'data/server_recommendation.csv' tidak ditemukan.")
    except Exception as e:
        st.error(f"Gagal memuat data rekomendasi: {e}")

    st.divider()


# ----------------------------
# Smart Estimator (like screenshot)
# ----------------------------
def _recommend_from_concurrency(concurrent: int) -> str:
    """
    Simple heuristic mapping concurrent users -> suggested base spec.
    Adjust thresholds to match your infra reality.
    """
    if concurrent <= 20:
        return "1 vCPU / 2 GB RAM"
    if concurrent <= 60:
        return "2 vCPU / 4 GB RAM"
    if concurrent <= 150:
        return "4 vCPU / 8 GB RAM"
    if concurrent <= 400:
        return "8 vCPU / 16 GB RAM"
    return "GPU / High RAM (AI/ML or extreme load)"


def render_smart_estimator():
    st.title("🔎 Smart Estimator")
    st.caption("Estimasi spesifikasi awal berdasarkan trafik dan durasi sesi (mirip contoh DLI).")

    st.markdown("### Tipe Produk")
    product_type = st.radio(
        " ",
        ["Web/Mobile App", "AI Model (LLM)"],
        horizontal=True,
        label_visibility="collapsed",
    )

    st.markdown("### Pilih preset (opsional)")
    col1, col2 = st.columns(2, gap="large")

    presets = [
        "1 vCPU / 1 GB — Staging / Testing",
        "2 vCPU / 1 GB — Personal Blog / Portfolio",
        "2 vCPU / 6–8 GB — Medium Web App / API",
        "4 vCPU / 8 GB — Moderate Web / API",
        "4 vCPU / 16 GB — High-load API Gateway",
        "8 vCPU / 16–32 GB — High-traffic / API",
        "GPU / high RAM — AI / ML Apps",
    ]

    # Split presets roughly like your screenshot (left 2, right rest)
    with col1:
        preset_left = st.radio(
            " ",
            presets[:2],
            index=0,
            label_visibility="collapsed",
        )
    with col2:
        preset_right = st.radio(
            " ",
            presets[2:],
            index=0,
            label_visibility="collapsed",
        )

    st.markdown("### Beban Aplikasi")
    c1, c2 = st.columns(2, gap="large")
    with c1:
        users_per_hour = st.number_input("User per Jam:", min_value=0, value=1000, step=50)
    with c2:
        session_seconds = st.number_input("Durasi Sesi (detik):", min_value=1, value=60, step=5)

    # Core formula from screenshot behavior
    concurrent = int((users_per_hour * session_seconds + 3599) // 3600)  # ceil(users*dur/3600)

    # Recommendation
    base_rec = _recommend_from_concurrency(concurrent)

    # Small tweak if they picked LLM (because humans love underestimating AI workloads)
    if product_type == "AI Model (LLM)":
        # Nudge recommendation one tier up for LLM workloads
        if base_rec.startswith("1 vCPU"):
            base_rec = "2 vCPU / 4 GB RAM"
        elif base_rec.startswith("2 vCPU"):
            base_rec = "4 vCPU / 8 GB RAM"
        elif base_rec.startswith("4 vCPU / 8"):
            base_rec = "4 vCPU / 16 GB RAM"

    st.markdown(
        f"""
        <div style="
            background:#eaf3ff;
            border-left:4px solid #3b82f6;
            padding:16px;
            border-radius:8px;
            font-weight:600;
        ">
            💡 <b>Saran:</b> {base_rec} (untuk ~{concurrent} concurrent users)
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption(
        "Rumus: concurrent ≈ ceil(User per Jam × Durasi Sesi / 3600). "
        "Threshold rekomendasi bisa kamu ubah di fungsi _recommend_from_concurrency()."
    )


# ----------------------------
# App shell (SPA-ish)
# ----------------------------
st.set_page_config(page_title="Kalkulator dan Paket Server", page_icon="💰", layout="centered")
st.markdown(
    """
    <style>
        .block-container {
            max-width: 1200px;
            padding-left: 3rem;
            padding-right: 3rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Sidebar navigation (single file)
st.sidebar.title("Navigasi")
route = st.sidebar.radio(
    " ",
    ["Kalkulator & Paket Server", "Smart Estimator"],
    label_visibility="collapsed",
)

if route == "Smart Estimator":
    render_smart_estimator()
else:
    st.title("💰 Paket Server untuk Produk Internal")
    st.caption("Digunakan sebagai basis perhitungan biaya acuan awal")

    # Recommendation table (was previously in pages/server_recommendation.py)
    render_server_recommendation()

    st.subheader("Kalkulator VPS dan Paket Server")
    mode = st.radio("Pilih Kategori Produk:", ["Cloud VPS eXtreme", "Paket Server VPS"], horizontal=True)

    if mode == "Cloud VPS eXtreme":
        render_cloud_vps()
    else:
        render_server_vps()
