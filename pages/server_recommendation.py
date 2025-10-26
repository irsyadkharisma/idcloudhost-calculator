import streamlit as st
import pandas as pd
import re

def parse_vcpu(value):
    """Extract numeric value of vCPU for sorting."""
    match = re.search(r"(\d+)", str(value))
    return int(match.group(1)) if match else 999  # GPU/high RAM will go last

def render_server_recommendation():
    st.subheader("Rekomendasi Server Berdasarkan Penggunaan")

    try:
        df = pd.read_csv("data/server_recommendation.csv")
        df.columns = df.columns.str.strip()

        # Reorder columns
        desired_order = ["Specs", "Storage", "Typical Load", "Use Case", "Description"]
        existing_columns = [col for col in desired_order if col in df.columns]
        df = df[existing_columns]

        # Sort Specs naturally (1 vCPU, 2 vCPU, 4 vCPU, 8 vCPU, GPU/high RAM)
        df["SortKey"] = df["Specs"].apply(parse_vcpu)
        df = df.sort_values("SortKey").drop(columns=["SortKey"])

        # Display table
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.caption("Gunakan tabel di atas sebagai acuan awal sebelum menghitung biaya VPS yang sesuai.")
    except FileNotFoundError:
        st.error("File 'data/server_recommendation.csv' tidak ditemukan.")
    except Exception as e:
        st.error(f"Gagal memuat data rekomendasi: {e}")

    st.divider()
