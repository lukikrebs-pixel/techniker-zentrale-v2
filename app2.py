import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.title("🔍 Diagnose-Modus")

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="users", ttl=0)
    st.success("✅ Verbindung zu Google Sheets erfolgreich!")
    st.write("Daten aus 'users':", df)
except Exception as e:
    st.error(f"❌ Verbindung fehlgeschlagen: {e}")
