import streamlit as st
import pandas as pd

def render_server_recommendation():
    st.subheader("Rekomendasi Server Berdasarkan Penggunaan")

    try:
        df = pd.read_csv("data/server_recommendation.csv")
        df.columns = df.columns.str.strip()

        # --- Reorder columns dynamically ---
        desired_order = ["Specs", "Storage", "Typical Load", "Use Case", "Description"]
        existing_columns = [col for col in desired_order if col in df.columns]
        df = df[existing_columns]

        # --- Display table ---
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.caption("Gunakan tabel di atas sebagai acuan awal sebelum menghitung biaya VPS yang sesuai.")
    except FileNotFoundError:
        st.error("File 'data/server_recommendation.csv' tidak ditemukan.")
    except Exception as e:
        st.error(f"Gagal memuat data rekomendasi: {e}")

    st.divider()
