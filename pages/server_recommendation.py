import streamlit as st
import pandas as pd
import re

def parse_vcpu(value):
    """Mengekstrak nilai numerik vCPU untuk pengurutan."""
    match = re.search(r"(\d+)", str(value))
    return int(match.group(1)) if match else 999  # GPU/high RAM diletakkan di akhir

def render_server_recommendation():
    st.subheader("📋 Rekomendasi Server Berdasarkan Penggunaan")

    try:
        # Load data asli
        df = pd.read_csv("data/server_recommendation.csv")
        df.columns = df.columns.str.strip()

        # --- PROSES REFINEMENT KOLOM ---
        # Menggabungkan Use Case dan Description menjadi satu narasi
        df["Skenario Penggunaan"] = df["Use Case"] + ": " + df["Description"]

        # Sort berdasarkan spesifikasi vCPU agar urut dari spek kecil ke besar
        df["SortKey"] = df["Specs"].apply(parse_vcpu)
        df = df.sort_values("SortKey")

        # Memilih kolom yang ingin ditampilkan (tanpa Use Case dan Description terpisah)
        display_columns = ["Specs", "Storage", "Typical Load", "Skenario Penggunaan"]
        df_display = df[display_columns].copy()

        # --- TAMPILAN TABEL ---
        # Menggunakan st.dataframe untuk tampilan yang clean dan lebar otomatis
        st.dataframe(
            df_display, 
            use_container_width=True, 
            hide_index=True
        )
        
        st.caption("Gunakan tabel di atas sebagai acuan awal sebelum menghitung biaya VPS di bawah.")

    except FileNotFoundError:
        st.error("File 'data/server_recommendation.csv' tidak ditemukan di folder data.")
    except Exception as e:
        st.error(f"Terjadi kesalahan: {e}")
