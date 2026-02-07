import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from streamlit_calendar import calendar
from datetime import datetime
import base64
import os

# --- 1. SEITEN-KONFIGURATION ---
st.set_page_config(
    page_title="Techniker Zentrale",
    page_icon="🛠️",
    layout="wide"
)

# --- 2. LOGO-FUNKTION ---
def get_base64_of_bin_file(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    return ""

img_base64 = get_base64_of_bin_file("logo.jpg")

# --- 3. VERBINDUNG ZU GOOGLE SHEETS ---
# WICHTIG: In den Secrets muss [connection.gsheets] stehen!
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"Kritischer Verbindungsfehler: {e}")
    st.stop()

# --- 4. SESSION STATE INITIALISIERUNG ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_name' not in st.session_state:
    st.session_state.user_name = ""
if 'user_role' not in st.session_state:
    st.session_state.user_role = ""

# --- 5. DATEN LADEN (USERS) ---
@st.cache_data(ttl=600) # Cache für 10 Minuten
def load_users():
    try:
        # Liest das Blatt "users"
        return conn.read(worksheet="users")
    except Exception as e:
        st.error("Konnte Benutzerliste nicht laden. Prüfe die Google-Freigabe!")
        return None

users_df = load_users()

# --- 6. LOGIN-BEREICH ---
if not st.session_state.logged_in:
    cols = st.columns([1, 2, 1])
    with cols[1]:
        if img_base64:
            st.markdown(
                f'<div style="text-align: center;"><img src="data:image/jpg;base64,{img_base64}" width="200"></div>',
                unsafe_allow_html=True
            )
        st.title("🔐 Techniker Login")
        
        with st.form("login_form"):
            user_input = st.text_input("Benutzername")
            pass_input = st.text_input("Passwort", type="password")
            btn = st.form_submit_button("Anmelden", use_container_width=True)
            
            if btn:
                if users_df is not None:
                    # Suche nach User
                    user_row = users_df[users_df['username'] == user_input]
                    
                    if not user_row.empty:
                        db_password = str(user_row.iloc[0]['password'])
                        if db_password == pass_input:
                            st.session_state.logged_in = True
                            st.session_state.user_name = user_input
                            st.session_state.user_role = user_row.iloc[0]['role']
                            st.success("Erfolgreich angemeldet!")
                            st.rerun()
                        else:
                            st.error("Falsches Passwort.")
                    else:
                        st.error("Benutzer nicht gefunden.")
                else:
                    st.error("Fehler beim Zugriff auf die Datenbank.")
    st.stop()

# --- 7. HAUPT-APP (NACH LOGIN) ---

# Sidebar für Navigation und Logout
with st.sidebar:
    st.image("logo.jpg") if os.path.exists("logo.jpg") else st.title("🛠️ TZ")
    st.subheader(f"Eingeloggt: {st.session_state.user_name}")
    st.write(f"Rolle: {st.session_state.user_role}")
    
    page = st.radio("Navigation", ["Dashboard", "Kalender", "Noten-Eingabe"])
    
    if st.button("Abmelden", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

# --- 8. SEITEN-INHALTE ---

if page == "Dashboard":
    st.header("🏠 Dashboard")
    st.write(f"Willkommen zurück, {st.session_state.user_name}!")
    # Hier kannst du z.B. eine Übersicht deiner Noten anzeigen
    
elif page == "Kalender":
    st.header("📅 Techniker Kalender")
    # Beispiel für Streamlit Calendar (Standard-Events)
    calendar_options = {
        "headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth,timeGridWeek"},
        "initialView": "dayGridMonth",
    }
    calendar(events=[], options=calendar_options)

elif page == "Noten-Eingabe":
    st.header("📝 Noten verwalten")
    if st.session_state.user_role == "Admin":
        st.info("Hier kannst du Noten eintragen.")
        # Hier käme deine Schreib-Logik hin: conn.update(...)
    else:
        st.warning("Nur Admins dürfen Noten ändern.")
