import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from streamlit_calendar import calendar

# 1. Konfiguration & Design
st.set_page_config(page_title="Techniker Zentrale", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    </style>
    """, unsafe_allow_html=True)

# 2. Verbindung zu Google Sheets
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("Verbindung zu Google Sheets fehlgeschlagen. Prüfe deine Secrets!")
    st.stop()

# 3. Login-Logik
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def login():
    st.title("🔐 Techniker Login")
    with st.form("login_form"):
        user = st.text_input("Benutzername")
        pw = st.text_input("Passwort", type="password")
        submit = st.form_submit_button("Anmelden")
        
        if submit:
            try:
                # User-Daten aus Sheet "users" laden
                user_df = conn.read(worksheet="users", ttl=0)
                # Validierung
                if not user_df[(user_df['username'] == user) & (user_df['password'].astype(str) == pw)].empty:
                    st.session_state.logged_in = True
                    st.session_state.username = user
                    st.rerun()
                else:
                    st.error("Falscher Benutzername oder Passwort")
            except Exception as e:
                st.error(f"Fehler beim Laden der Benutzerdaten: {e}")

# 4. Hauptprogramm (wenn eingeloggt)
if not st.session_state.logged_in:
    login()
else:
    st.sidebar.title(f"Willkommen, {st.session_state.username}!")
    menu = st.sidebar.radio("Navigation", ["Dashboard & Noten", "Klassen-Kalender", "Privater Kalender"])
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    # --- SEITE: DASHBOARD & NOTEN ---
    if menu == "Dashboard & Noten":
        st.header("📊 Deine Notenübersicht")
        try:
            noten_df = conn.read(worksheet="noten", ttl=0)
            user_noten = noten_df[noten_df['username'] == st.session_state.username]
            
            if user_noten.empty:
                st.info("Noch keine Noten eingetragen.")
            else:
                st.table(user_noten)
                # Kleine Berechnung (Beispiel)
                schnitt = user_noten['note'].mean()
                st.metric("Dein aktueller Schnitt", f"{schnitt:.2f}")
        except:
            st.warning("Konnte Notenliste nicht laden.")

    # --- SEITE: KLASSEN-KALENDER ---
    elif menu == "Klassen-Kalender":
        st.header("📅 Gemeinsame Termine")
        try:
            cal_df = conn.read(worksheet="termine_klasse", ttl=0)
            events = []
            for _, row in cal_df.iterrows():
                events.append({"title": row['event'], "start": str(row['datum']), "color": "#FF4B4B"})
            
            calendar(events=events, options={"headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth"}})
        except:
            st.info("Keine Klassentermine gefunden.")

    # --- SEITE: PRIVATER KALENDER ---
    elif menu == "Privater Kalender":
        st.header("🔒 Deine privaten Termine")
        st.write("Hier könntest du Termine nur für dich speichern.")
        # Analog zum Klassentender, nur Filter auf username
