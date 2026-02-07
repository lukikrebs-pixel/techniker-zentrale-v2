import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Techniker Zentrale", layout="wide")

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="users", ttl=0)
    st.success("✅ Verbindung steht! Google Sheets wurde gefunden.")
    st.write("Aktuelle User in der Liste:", df)
except Exception as e:
    st.error(f"❌ Verbindung noch nicht bereit: {e}")
    st.info("Hast du die Secrets schon eingetragen?")
