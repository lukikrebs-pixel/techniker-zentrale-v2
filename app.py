import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from streamlit_calendar import calendar
from datetime import datetime
import base64
import os

# --- 1. KONFIGURATION & LOGO ---
st.set_page_config(page_title="Techniker Zentrale", layout="wide")

def get_base64_of_bin_file(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    return ""

img_base64 = get_base64_of_bin_file("logo.jpg")

# --- 2. VERBINDUNG ZU GOOGLE SHEETS ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("Verbindung zu Google Sheets fehlgeschlagen!")
    st.stop()

# --- 3. SESSION STATE ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'page' not in st.session_state:
    st.session_state.page = "Dashboard"

# --- 4. DESIGN ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #3b7ab0; color: white; }}
    .logo-container {{ position: fixed; top: 20px; right: 20px; z-index: 1000; }}
    .logo-container img {{ width: 110px; border-radius: 5px; }}
    div.stButton > button {{
        background: rgba(255, 255, 255, 0.12) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 15px !important; color: white !important;
        padding: 20px !important; min-height: 80px !important;
    }}
    .mini-metric {{ padding: 15px; border-radius: 15px; text-align: center; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); }}
    .fach-card {{ padding: 10px; border-radius: 12px; text-align: center; border: 1px solid rgba(0,0,0,0.1); margin-bottom: 10px; font-weight: bold; }}
    </style>
    <div class="logo-container"><img src="data:image/jpg;base64,{img_base64}"></div>
    """, unsafe_allow_html=True)

# --- 5. LOGIN & REGISTRIERUNG ---
if not st.session_state.logged_in:
    st.title("🔐 Techniker Zentrale")
    t_log, t_reg = st.tabs(["Anmelden", "Registrieren"])
    
    with t_log:
        u = st.text_input("Benutzername")
        p = st.text_input("Passwort", type="password")
        if st.button("Login"):
            users_df = conn.read(worksheet="users", ttl=0)
            if not users_df[(users_df['username'] == u) & (users_df['password'].astype(str) == p)].empty:
                st.session_state.logged_in, st.session_state.user = True, u
                st.rerun()
            else: st.error("Falsch!")
            
    with t_reg:
        nu = st.text_input("Neuer User")
        np = st.text_input("Neues Passwort", type="password")
        if st.button("Konto erstellen"):
            users_df = conn.read(worksheet="users", ttl=0)
            if nu and np and nu not in users_df['username'].values:
                new_user = pd.DataFrame([{"username": nu, "password": np}])
                updated_users = pd.concat([users_df, new_user], ignore_index=True)
                conn.update(worksheet="users", data=updated_users)
                st.success("Konto erstellt!")
            else: st.error("Fehler!")
    st.stop()

# --- 6. NAVIGATION ---
def back():
    if st.button("⬅️ Zurück"): 
        st.session_state.page = "Dashboard"
        st.rerun()

# --- SEITE: DASHBOARD ---
if st.session_state.page == "Dashboard":
    # Noten laden für Schnitt
    noten_df = conn.read(worksheet="noten", ttl=0)
    user_noten = noten_df[noten_df['username'] == st.session_state.user]
    
    s = (user_noten['note'] * user_noten['gewicht']).sum() / user_noten['gewicht'].sum() if not user_noten.empty else 0.0
    
    c_g, c_s = st.columns([2, 1])
    c_g.title(f"Moin, {st.session_state.user}!👋")
    c_s.markdown(f'<div class="mini-metric">Schnitt: <b>{s:.2f}</b></div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    if c1.button("✍️\n\nNote eintragen"): st.session_state.page = "Eintragen"; st.rerun()
    if c2.button("📊\n\nÜbersicht"): st.session_state.page = "Übersicht"; st.rerun()
    if c3.button("📅\n\nTermine"): st.session_state.page = "Termine"; st.rerun()

    # Kalender Events sammeln
    all_ev = []
    # 1. Klassentermine
    kt = conn.read(worksheet="termine_klasse", ttl=0)
    for _, t in kt.iterrows():
        all_ev.append({"title": f"📢 {t['event']}", "start": str(t['datum']), "color": "#ff4b4b"})
    # 2. Privattermine
    pt = conn.read(worksheet="termine_privat", ttl=0)
    user_pt = pt[pt['username'] == st.session_state.user]
    for _, t in user_pt.iterrows():
        all_ev.append({"title": f"👤 {t['event']}", "start": str(t['datum']), "color": "#27ae60"})
    
    calendar(events=all_ev, options={"locale": "de", "height": "450px"})
    if st.button("🚪 Logout"): st.session_state.logged_in = False; st.rerun()

# --- SEITE: EINTRAGEN ---
elif st.session_state.page == "Eintragen":
    back()
    f = st.selectbox("Fach", ["Mathe", "Deutsch", "Elektrotechnik", "Physik", "IT"])
    n = st.number_input("Note", 1.0, 6.0, 2.0)
    g = st.radio("Gewichtung", [1, 2])
    if st.button("Speichern"):
        df = conn.read(worksheet="noten", ttl=0)
        new_row = pd.DataFrame([{"username": st.session_state.user, "fach": f, "note": n, "gewicht": g}])
        conn.update(worksheet="noten", data=pd.concat([df, new_row], ignore_index=True))
        st.success("Gespeichert!")

# --- SEITE: TERMINE ---
elif st.session_state.page == "Termine":
    back()
    typ = st.radio("Typ", ["Klasse", "Privat"])
    ev = st.text_input("Was steht an?")
    da = st.date_input("Wann?")
    if st.button("Termin speichern"):
        ws = "termine_klasse" if typ == "Klasse" else "termine_privat"
        df = conn.read(worksheet=ws, ttl=0)
        new_ev = {"event": ev, "datum": str(da)}
        if typ == "Privat": new_ev["username"] = st.session_state.user
        conn.update(worksheet=ws, data=pd.concat([df, pd.DataFrame([new_ev])], ignore_index=True))
        st.success("Termin steht!")
