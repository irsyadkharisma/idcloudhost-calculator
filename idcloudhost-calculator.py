import streamlit as st
import pandas as pd

st.set_page_config(page_title="IDCloudHost Server Advisor", page_icon="☁️", layout="centered")

st.title("IDCloudHost Server Advisor")
st.caption("Pilih tab di kiri untuk melihat rekomendasi server atau menghitung biaya VPS.")

st.markdown("""
Selamat datang di **IDCloudHost Server Advisor**  
Gunakan dua halaman berikut:
1. **Rekomendasi Server** — untuk melihat kebutuhan server berdasarkan jenis penggunaan.  
2. **Kalkulator VPS** — untuk menghitung biaya detail dengan konfigurasi tertentu.  
""")

# Load a short preview of recommendations
st.subheader("Ringkasan Rekomendasi Server")

try:
    df = pd.read_csv("data/server_recommendation.csv")
    st.dataframe(df.head(5), use_container_width=True, hide_index=True)
    st.caption("Tabel di atas adalah ringkasan dari rekomendasi server. Buka halaman 'Rekomendasi Server' untuk versi lengkap.")
except Exception as e:
    st.error(f"Gagal memuat data rekomendasi: {e}")

# Link to calculator page
st.markdown("---")
st.markdown(
    """
    **Ingin menghitung biaya VPS untuk konfigurasi tertentu?**  
    [Buka Kalkulator VPS →](./Kalkulator_VPS)
    """,
    unsafe_allow_html=True
)
