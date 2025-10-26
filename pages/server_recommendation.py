import streamlit as st
import pandas as pd

def render_server_recommendation():
    st.subheader("Rekomendasi Server Berdasarkan Penggunaan")

    try:
        df = pd.read_csv("data/server_recommendation.csv")
        df.columns = df.columns.str.strip()  # remove stray spaces

        # Combine Use Case + Description into one column
        df["Use Case & Description"] = df["Use Case"] + " — " + df["Description"]

        # Add a placeholder column for cost (to be updated later if pricing data available)
        df["Est. Cost/Bulan"] = "-"

        # Reorder columns
        columns_order = ["Specs", "Storage", "Typical Load", "Use Case & Description", "Est. Cost/Bulan"]
        df = df[columns_order]

        # Display table
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.caption("Gunakan tabel di atas sebagai acuan awal sebelum menghitung biaya VPS yang sesuai.")
    except FileNotFoundError:
        st.error("File 'data/server_recommendation.csv' tidak ditemukan.")
    except Exception as e:
        st.error(f"Gagal memuat data rekomendasi: {e}")

    st.divider()
