import streamlit as st
import pandas as pd
import re

def parse_vcpu(value):
    """Mengekstrak nilai numerik vCPU untuk pengurutan."""
    match = re.search(r"(\d+)", str(value))
    return int(match.group(1)) if match else 999 

def render_server_recommendation():
    st.subheader("📋 Panduan Skenario & Spek Server")

    try:
        df = pd.read_csv("data/server_recommendation.csv")
        df.columns = df.columns.str.strip()

        # MENGGABUNGKAN Use Case dengan Description
        # Contoh: "Staging: Testing landing pages..."
        df["Skenario Penggunaan"] = "**" + df["Use Case"] + "**: " + df["Description"]

        # Pilih kolom yang ingin ditampilkan saja
        display_cols = ["Specs", "Storage", "Typical Load", "Skenario Penggunaan"]
        df_display = df[display_cols].copy()

        # Sorting agar rapi dari spek kecil ke besar
        df_display["SortKey"] = df_display["Specs"].apply(parse_vcpu)
        df_display = df_display.sort_values("SortKey").drop(columns=["SortKey"])

        # Tampilkan tabel
        st.markdown(df_display.to_markdown(index=False), unsafe_allow_html=True)
        st.caption("Gunakan tabel di atas sebagai acuan awal sebelum menghitung biaya di bawah.")
        
    except Exception as e:
        st.error(f"Gagal memuat tabel rekomendasi: {e}")
