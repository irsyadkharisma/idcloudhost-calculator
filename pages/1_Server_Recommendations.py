import streamlit as st
import pandas as pd

def render_server_recommendation():
    st.subheader("Rekomendasi Server Berdasarkan Penggunaan")

    try:
        df = pd.read_csv("data/server_recommendation.csv")
        df.columns = df.columns.str.strip()  # sanitize column headers

        # Sort by Use Case alphabetically if column exists
        if "Use Case" in df.columns:
            df = df.sort_values("Use Case")

        st.dataframe(df, use_container_width=True, hide_index=True)
        st.caption("Gunakan tabel di atas sebagai acuan awal sebelum menghitung biaya VPS yang sesuai.")
    except FileNotFoundError:
        st.error("File 'data/server_recommendation.csv' tidak ditemukan.")
    except Exception as e:
        st.error(f"Gagal memuat data rekomendasi: {e}")

    st.divider()
