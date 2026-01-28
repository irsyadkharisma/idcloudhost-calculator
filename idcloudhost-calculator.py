import streamlit as st
import pandas as pd
import re

def parse_vcpu(value):
    """Mengekstrak nilai numerik vCPU untuk pengurutan."""
    match = re.search(r"(\d+)", str(value))
    return int(match.group(1)) if match else 999  # AI/GPU diletakkan paling bawah

def render_server_recommendation():
    st.subheader("Rekomendasi Server & Skenario Penggunaan")

    try:
        df = pd.read_csv("data/server_recommendation.csv")
        df.columns = df.columns.str.strip()

        # Menggabungkan Use Case dan Description
        df["Skenario Penggunaan"] = df["Use Case"] + ": " + df["Description"]

        # Memilih dan menyusun ulang kolom yang akan ditampilkan
        display_columns = ["Specs", "Storage", "Typical Load", "Skenario Penggunaan"]
        df_display = df[display_columns].copy()

        # Sort berdasarkan spesifikasi vCPU
        df_display["SortKey"] = df_display["Specs"].apply(parse_vcpu)
        df_display = df_display.sort_values("SortKey").drop(columns=["SortKey"])

        # Menampilkan tabel
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        st.caption("Gunakan tabel di atas sebagai acuan awal sebelum menghitung biaya VPS yang sesuai di bagian bawah.")
        
    except FileNotFoundError:
        st.error("File 'data/server_recommendation.csv' tidak ditemukan.")
    except Exception as e:
        st.error(f"Terjadi kesalahan saat memproses data: {e}")
