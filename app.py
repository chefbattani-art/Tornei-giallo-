import streamlit as st
import pandas as pd
import json
import os
import re
import random
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh
from base64 import b64encode
from fpdf import FPDF

st.set_page_config(page_title="Torneo Biliardino 'Giallo' Live", layout="wide")

st_autorefresh(interval=5000, debounce=False, key="auto_refresh_torneo")

DB_FILE = "torneo_data.json"
LOGO_FILE = "logo_uisp.png"

def carica_dati():
    dati_default = {
        "stato": "setup",
        "portieri": [],
        "attaccanti": [],
        "num_tavoli": 3,
        "partite_per_giocatore": 6,
        "admin_pin": "0000",
        "turni_partite": [], 
        "punti_portieri": {},
        "punti_attaccanti": {},
        "dr_portieri": {},
        "dr_attaccanti": {},
        "fasi_finali": []
    }
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                dati_salvati = json.load(f)
                for k, v in dati_default.items():
                    if k not in dati_salvati:
                        dati_salvati[k] = v
                return dati_salvati
        except:
            pass
    return dati_default

def salva_dati(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

if "db" not in st.session_state:
    st.session_state.db = carica_dati()

db = st.session_state.db

# --- BARRA LATERALE PER VERIFICA ADMIN ---
st.sidebar.header("⚙️ Pannello Admin")
modalita_admin = st.sidebar.checkbox("Modalità Amministratore (PIN)")

is_admin = False
if modalita_admin:
    pin_inserito = st.sidebar.text_input("Inserisci PIN Admin", type="password")
    if pin_inserito == db["admin_pin"]:
        is_admin = True
        st.sidebar.success("Accesso Admin OK ✅")
    else:
        st.sidebar.error("PIN errato.")

# --- CSS PERSONALIZZATO (DARK MODE & SELETTORI GOL) ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&display=swap');

        :root {
            color-scheme: dark;
        }

        html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stToolbar"] {
            background-color: #090d16 !important;
            color: #ffffff !important;
        }

        [class*="css"] {
            font-family: 'Outfit', sans-serif;
            color: #ffffff;
            font-size: 1.05rem;
        }

        .block-container {
            padding-top: 1.2rem !important;
            padding-bottom: 2rem !important;
            padding-left: 1.2rem !important;
            padding-right: 1.2rem !important;
            background-color: #090d16 !important;
            background-image: 
                radial-gradient(at 0% 0%, rgba(14, 165, 233, 0.1) 0px, transparent 50%),
                radial-gradient(at 100% 100%, rgba(236, 72, 153, 0.1) 0px, transparent 50%);
        }

        div[data-testid="stExpander"] summary,
        div[data-testid="stExpander"] summary p,
        div[data-testid="stExpander"] p,
        small {
            color: #ffffff !important;
            font-weight: 600 !important;
        }

        button[data-testid="stBaseButton-secondary"], 
        button[data-testid="stBaseButton-primary"],
        div.stButton > button {
            background-color: #1f2937 !important;
            color: #ffffff !important;
            border: 1px solid #4b5563 !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
        }
        
        button[data-testid="stBaseButton-secondary"]:hover,
        div.stButton > button:hover {
            background-color: #374151 !important;
            border-color: #38bdf8 !important;
            color: #38bdf8 !important;
        }

        input, textarea, div[data-baseweb="select"] > div {
            background-color: #1f2937 !important;
            color: #ffffff !important;
            border-color: #4b5563 !important;
            font-size: 1.05rem !important;
        }

        [data-testid="stExpander"] {
            background-color: #111827 !important;
            border: 1px solid #4b5563 !important;
            border-radius: 12px !important;
        }

        .ranking-card {
            background: linear-gradient(145deg, #111827, #0f172a);
            border: 1px solid #3b82f6;
            border-radius: 20px;
            padding: 20px;
            box-shadow: 0 0 20px rgba(59, 130, 246, 0.25);
            margin-bottom: 20px;
        }

        .ranking-title {
            text-align: center;
            color: #38bdf8;
            font-size: 1.4rem;
            font-weight: 700;
            margin-bottom: 14px;
            letter-spacing: 0.5px;
            text-shadow: 0 0 10px rgba(56, 189, 248, 0.5);
        }

        table.styled-table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            font-size: 1.02rem;
            border-radius: 12px;
            overflow: hidden;
        }
        table.styled-table th {
            background: linear-gradient(135deg, #0284c7, #2563eb);
            color: #ffffff;
            text-align: center;
            padding: 12px;
            font-weight: 700;
            text-transform: uppercase;
            font-size: 0.95rem;
            letter-spacing: 0.5px;
        }
        table.styled-table td {
            padding: 10px 12px;
            text-align: center;
            border-bottom: 1px solid #1e293b;
            background-color: #111827;
            color: #ffffff !important;
            font-weight: 600;
        }
        table.styled-table tr.qualificato td {
            background-color: rgba(6, 78, 59, 0.4);
            color: #4ade80 !important;
            font-weight: 700;
        }
        table.styled-table tr.eliminato td {
            background-color: rgba(127, 29, 29, 0.3);
            color: #f87171 !important;
        }

        .live-match-box {
            background: linear-gradient(135deg, #1e1b4b, #311033);
            border: 2px solid #f59e0b;
            border-radius: 14px;
            padding: 12px 16px;
            margin-bottom: 12px;
            box-shadow: 0 0 15px rgba(245, 158, 11, 0.4);
        }

        .queue-match-box {
            background: linear-gradient(135deg, #022c22, #064e3b);
            border: 1px solid #10b981;
            border-radius: 12px;
            padding: 10px 14px;
            margin-bottom: 8px;
            color: #ffffff;
            box-shadow: 0 0 10px rgba(16, 185, 129, 0.2);
        }

        .alert-active-game {
            background: linear-gradient(135deg, #450a0a, #7f1d1d);
            border: 2px solid #ef4444;
            border-radius: 14px;
            padding: 14px;
            margin-bottom: 16px;
            text-align: center;
            box-shadow: 0 0 20px rgba(239, 68, 68, 0.6);
        }
    </style>
""", unsafe_allow_html=True)

def pulisci_nome(testo):
    testo = testo.replace("🥅", "").replace("🚪", "").replace("⚽", "")
    testo = re.sub(r'^\d+[\.\-\)]?\s*', '', testo)
    return testo.strip()

def ricalcola_classifiche():
    p_punti = {p: 0 for p in db["portieri"]}
    p_dr = {p: 0 for p in db["portieri"]}
    
    a_punti = {a: 0 for a in db["attaccanti"]}
    a_dr = {a: 0 for a in db["attaccanti"]}
    
    for turno_obj in db["turni_partite"]:
        for m in turno_obj["partite"]:
            if m.get("giocata", False):
                g1 = m["gol1"]
                g2 = m["gol2"]
                diff = abs(g1 - g2)
                
                if g1 > g2:
                    pt_s1, pt_s2 = (3, 0) if diff >= 2 else (2, 1)
                elif g2 > g1:
                    pt_s1, pt_s2 = (0, 3) if diff >= 2 else (1, 2)
                else:
                    pt_s1, pt_s2 = 2, 2
                
                p_punti[m['p1']] = p_punti.get(m['p1'], 0) + pt_s1
                p_dr[m['p1']] = p_dr.get(m['p1'], 0) + (g1 - g2)
                
                a_punti[m['a1']] = a_punti.get(m['a1'], 0) + pt_s1
                a_dr[m['a1']] = a_dr.get(m['a1'], 0) + (g1 - g2)
                
                p_punti[m['p2']] = p_punti.get(m['p2'], 0) + pt_s2
                p_dr[m['p2']] = p_dr.get(m['p2'], 0) + (g2 - g1)
                
                a_punti[m['a2']] = a_punti.get(m['a2'], 0) + pt_s2
                a_dr[m['a2']] = a_dr.get(m['a2'], 0) + (g2 - g1)
                
    db["punti_portieri"] = p_punti
    db["dr_portieri"] = p_dr
    db["punti_attaccanti"] = a_punti
    db["dr_attaccanti"] = a_dr

def calcola_partite_giocate(ruolo, nome):
    giocate = 0
    totali = 0
    for turno_obj in db["turni_partite"]:
        for m in turno_obj["partite"]:
            is_presente = False
            if ruolo == "portiere" and (m['p1'] == nome or m['p2'] == nome):
                is_presente = True
            elif ruolo == "attaccante" and (m['a1'] == nome or m['a2'] == nome):
                is_presente = True
            
            if is_presente:
                totali += 1
                if m.get("giocata", False):
                    giocate += 1
    return giocate, totali

def genera_pdf_calendario():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Torneo Biliardino 'Giallo' - Schema Partite", 0, 1, "C")
    pdf.ln(5)
    
    num_tavoli = db.get("num_tavoli", 3)
    
    for turno_obj in db["turni_partite"]:
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, f"Turno {turno_obj['turno']}", 0, 1, "L")
        pdf.set_font("Arial", "", 10)
        
        for idx, m in enumerate(turno_obj["partite"]):
            tavolo_num = (idx % num_tavoli) + 1
            risultato = f"{m['gol1']} - {m['gol2']}" if m.get("giocata", False) else "Da giocare"
            riga = f"  - Biliardino {tavolo_num}: {m['p1']}/{m['a1']} vs {m['p2']}/{m['a2']} -> {risultato}"
            riga_pulita = riga.encode('latin-1', 'ignore').decode('latin-1')
            pdf.cell(0, 6, riga_pulita, 0, 1, "L")
        pdf.ln(3)
        
    return bytes(pdf.output())

# --- OPZIONI ADMIN IN SIDEBAR ---
if is_admin:
    st.sidebar.markdown("---")
    st.sidebar.subheader("🗑️ Reset Totale")
    if st.sidebar.button("⚠️ Azzera e Ricomincia", use_container_width=True):
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.query_params.clear()
        st.sidebar.success("Torneo azzerato con successo!")
        st.rerun()

if is_admin and db["stato"] != "setup":
    st.sidebar.markdown("---")
    st.sidebar.subheader("🛠️ Correzione Parametri")
    with st.sidebar.expander("Modifica Biliardini / Turni"):
        nuovi_tavoli = st.number_input("N° Biliardini", min_value=1, max_value=10, value=db["num_tavoli"])
        nuovi_turni = st.number_input("N° Turni", min_value=1, max_value=10, value=db["partite_per_giocatore"])
        if st.button("💾 Aggiorna Parametri", use_container_width=True):
            db["num_tavoli"] = nuovi_tavoli
            db["partite_per_giocatore"] = nuovi_turni
            salva_dati(db)
            st.sidebar.success("Parametri aggiornati!")
            st.rerun()

if db["stato"] != "setup":
    st.sidebar.markdown("---")
    pdf_data = genera_pdf_calendario()
    st.sidebar.download_button(
        label="📥 Scarica PDF Calendario",
        data=pdf_data,
        file_name="schema_torneo_biliardino.pdf",
        mime="application/pdf",
        use_container_width=True
    )

st.sidebar.markdown("---")
st.sidebar.subheader("📱 Condividi Torneo")
link_torneo = st.sidebar.text_input("Link Spettatore:", value="https://2quznathuywvfxcskgfjhk.streamlit.app")

if link_torneo and link_torneo != "https://":
    import urllib.parse
    encoded_url = urllib.parse.quote(link_torneo, safe='')
    qr_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={encoded_url}"
    st.sidebar.image(qr_api_url, caption="Inquadra per aprire", use_container_width=True)

# --- LOGO E HEADER COMUNE STILOSO ---
logo_html = ""
if os.path.exists(LOGO_FILE):
    with open(LOGO_FILE, "rb") as f:
        logo_b64 = b64encode(f.read()).decode("utf-8")
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="max-width: 120px; width: 100%; height: auto; margin-bottom: 8px;" /><br>'

st.html(
    f"""
    <div style="text-align: center; margin-bottom: 14px; background: #111827; padding: 18px; border-radius: 20px; box-shadow: 0 0 20px rgba(0,0,0,0.5); border: 1px solid #374151;">
        {logo_html}
        <h1 style="margin: 0; color: #38bdf8; font-size: 1.7rem; font-weight: 700; text-shadow: 0 0 10px rgba(56,189,248,0.4);">🏆 Torneo Biliardino 'Giallo' Live</h1>
        <span style="display: inline-block; margin-top: 8px; background-color: rgba(30, 58, 138, 0.6); color: #93c5fd; padding: 5px 14px; border-radius: 20px; font-weight: 600; font-size: 0.9rem; border: 1px solid #3b82f6;">Regolamento Uisp 3 tocchi</span>
    </div>
    """
)

# --- GESTIONE SELEZIONE NOME PERSISTENTE (TRAMITE URL) ---
tutti_i_giocatori = sorted(list(set(db["portieri"] + db["attaccanti"])))

if is_admin:
    giocatore_selezionato = "Admin"
elif db["stato"] != "setup" and tutti_i_giocatori:
    giocatore_url = st.query_params.get("giocatore", "")

    if giocatore_url in tutti_i_giocatori:
        giocatore_selezionato = giocatore_url
    else:
        giocatore_selezionato = "-- Seleziona il tuo nome --"

    if giocatore_selezionato == "-- Seleziona il tuo nome --":
        st.markdown("---")
        st.markdown("### 🔍 Benvenuto! Seleziona il tuo nome per accedere al torneo:")
        scelta_utente = st.selectbox(
            "Il tuo nome:",
            ["-- Seleziona il tuo nome --"] + tutti_i_giocatori,
            index=0
        )
        if scelta_utente != "-- Seleziona il tuo nome --":
            st.query_params["giocatore"] = scelta_utente
            st.rerun()
        st.stop()  
    else:
        col_n1, col_n2 = st.columns([3, 1])
        with col_n1:
            st.markdown(f"""
                <div style="background: #111827; padding: 12px 18px; border-radius: 12px; border: 1px solid #374151; font-weight: 600; color: #ffffff; font-size: 1.05rem;">
                    👤 Stai visualizzando come: <span style="color: #38bdf8;">{giocatore_selezionato}</span>
                </div>
            """, unsafe_allow_html=True)
        with col_n2:
            if st.button("🔄 Cambia Nome", use_container_width=True):
                st.query_params.clear()
                st.rerun()
        st.markdown("---")
else:
    giocatore_selezionato = "-- Seleziona il tuo nome --"

# --- INDIVIDUAZIONE ESATTA DELLE PARTITE ATTIVE SUI BILIARDINI ---
num_tavoli = db.get("num_tavoli", 3)
partite_attive_correnti = []

if db["stato"] == "gironi":
    for b_num in range(1, num_tavoli + 1):
        match_trovata = None
        for t_obj in db["turni_partite"]:
            for idx, m in enumerate(t_obj["partite"]):
                if ((idx % num_tavoli) + 1) == b_num and not m.get("giocata", False):
                    if match_trovata is None:
                        match_trovata = m
            if match_trovata:
                break
        if match_trovata and match_trovata not in partite_attive_correnti:
            if len(partite_attive_correnti) < num_tavoli:
                partite_attive_correnti.append(match_trovata)

elif db["stato"] == "eliminatorie":
    for f_turno in db["fasi_finali"]:
        for m in f_turno["partite"]:
            if not m.get("giocata", False):
                partite_attive_correnti.append(m)

# --- VERIFICA SE IL GIOCATORE SELEZIONATO È PROPRIO IN UNA PARTITA ATTIVA SUI BILIARDINI ---
ha_partita_in_corso = False
if giocatore_selezionato != "-- Seleziona il tuo nome --" and not is_admin:
    for m in partite_attive_correnti:
        if (giocatore_selezionato == m['p1'] or 
            giocatore_selezionato == m['a1'] or 
            giocatore_selezionato == m['p2'] or 
            giocatore_selezionato == m['a2']):
            ha_partita_in_corso = True
            break

if ha_partita_in_corso:
    st.html("""
        <div class="alert-active-game">
            <h4 style="margin: 0; color: #ffffff; font-size: 1.15rem; font-weight: 700;">🚨 ATTENZIONE: HAI UNA PARTITA IN CORSO!</h4>
            <p style="margin: 6px 0 0 0; color: #ffffff; font-size: 1rem; font-weight: 600;">
                Uno dei due giocatori della coppia vincente deve inserire il risultato finale e confermare.
            </p>
        </div>
    """)

st.html(
    """
    <div style="padding: 8px; background-color: #111827; border-radius: 8px; text-align: center; margin-bottom: 12px; border: 1px solid #374151;">
        🔄 <a href="javascript:window.location.reload(true)" style="text-decoration: none; color: #38bdf8; font-weight: 600; font-size: 0.95rem;">
            Ricarica la pagina del browser per aggiornare in tempo reale
        </a>
    </div>
    """
)

# 1. SETUP
if db["stato"] == "setup":
    st.subheader("1. Configurazione Iniziale del Torneo")
    if not is_admin:
        st.warning("⚠️ Il torneo non è ancora iniziato. L'amministratore deve effettuare l'accesso con il PIN nella barra laterale.")
    else:
        whatsapp_text = st.text_area("Incolla qui la lista da WhatsApp (es. 🥅 Mario, ⚽ Luigi):")
        
        col1, col2 = st.columns(2)
        with col1:
            db["num_tavoli"] = st.number_input("Numero di biliardini disponibili", min_value=1, max_value=10, value=db["num_tavoli"])
        with col2:
            db["partite_per_giocatore"] = st.number_input("Turni / Partite garantite", min_value=1, max_value=10, value=db["partite_per_giocatore"])
            
        db["admin_pin"] = st.text_input("Cambia PIN Admin", value=db["admin_pin"])

        if st.button("🚀 Avvia il Torneo e Genera Calendario"):
            portieri = []
            attaccanti = []
            for line in whatsapp_text.split("\n"):
                if "🥅" in line or "🚪" in line:
                    nome = pulisci_nome(line)
                    if nome: portieri.append(nome)
                elif "⚽" in line:
                    nome = pulisci_nome(line)
                    if nome: attaccanti.append(nome)
            
            if len(portieri) < 8 or len(attaccanti) < 8:
                st.error("Inserisci almeno 8 portieri (🥅) e 8 attaccanti (⚽).")
            else:
                db["portieri"] = portieri
                db["attaccanti"] = attaccanti
                db["punti_portieri"] = {p: 0 for p in portieri}
                db["dr_portieri"] = {p: 0 for p in portieri}
                db["punti_attaccanti"] = {a: 0 for a in attaccanti}
                db["dr_attaccanti"] = {a: 0 for a in attaccanti}
                db["stato"] = "gironi"
                db["fasi_finali"] = []
                
                db["turni_partite"] = []
                for t in range(1, db["partite_per_giocatore"] + 1):
                    p_shuff = portieri.copy()
                    a_shuff = attaccanti.copy()
                    random.shuffle(p_shuff)
                    random.shuffle(a_shuff)
                    
                    partite_turno = []
                    i = 0
                    while i + 1 < len(p_shuff) and i + 1 < len(a_shuff):
                        match_id = f"t{t}_m{i//2}"
                        partite_turno.append({
                            "id": match_id,
                            "p1": p_shuff[i], "a1": a_shuff[i],
                            "p2": p_shuff[i+1], "a2": a_shuff[i+1],
                            "giocata": False, "in_corso": False,
                            "gol1": 0, "gol2": 0
                        })
                        i += 2
                    db["turni_partite"].append({"turno": t, "partite": partite_turno})

                salva_dati(db)
                st.success("Calendario generato!")
                st.rerun()

# 2. GIRONI
if db["stato"] == "gironi":
    ricalcola_classifiche()
    num_tavoli = db.get("num_tavoli", 3)

    # --- PARTITE IN CORSO (SUI BILIARDINI) ---
    st.markdown("### 🔥 PARTITE IN CORSO (Sui biliardini):")
    
    partite_per_tavolo = {}
    for b_num in range(1, num_tavoli + 1):
        match_trovata = None
        turno_trovato = None
        for t_obj in db["turni_partite"]:
            for idx, m in enumerate(t_obj["partite"]):
                if ((idx % num_tavoli) + 1) == b_num and not m.get("giocata", False):
                    if match_trovata is None:
                        match_trovata = m
                        turno_trovato = t_obj['turno']
            if match_trovata:
                break
        if match_trovata:
            partite_per_tavolo[b_num] = (match_trovata, turno_trovato)

    for b_num in range(1, num_tavoli + 1):
        if b_num in partite_per_tavolo:
            m, turno_num = partite_per_tavolo[b_num]
            match_id = m['id']
            
            st.html(f"""
                <div class="live-match-box">
                    <div style="font-weight: 700; color: #fbbf24; margin-bottom: 6px; font-size: 0.95rem; display: flex; justify-content: space-between;">
                        <span>🏟️ BILIARDINO {b_num}</span>
                        <span>TURNO {turno_num}</span>
                    </div>
                    <div style="background-color: #111827; padding: 10px 14px; border-radius: 10px; border: 1px solid #f59e0b; display: flex; justify-content: space-around; align-items: center; font-weight: 600; font-size: 1.05rem; color: #ffffff;">
                        <span>🥅 {m['p1']} / ⚽ {m['a1']}</span>
                        <span style="font-weight: 800; color: #ffffff; font-size: 1.2rem; text-shadow: 0 0 8px rgba(255,255,255,0.5);">VS</span>
                        <span>🥅 {m['p2']} / ⚽ {m['a2']}</span>
                    </div>
                </div>
            """)

            partecipa = (
                giocatore_selezionato == m['p1'] or 
                giocatore_selezionato == m['a1'] or 
                giocatore_selezionato == m['p2'] or 
                giocatore_selezionato == m['a2']
            )

            if partecipa or is_admin:
                titolo_box = f"⚡ Inserisci Risultato Biliardino {b_num} (Tuo Match in corso!)" if partecipa else f"⚙️ Inserisci Gol Biliardino {b_num} (Admin)"
                with st.expander(titolo_box):
                    
                    # --- NUOVA INTERFACCIA GOL GRANDE E PULSANTI AFFIANCATI ---
                    st.markdown(f"**🥅 {m['p1']} / ⚽ {m['a1']} (Gol Coppia 1)**")
                    g1_cols = st.columns(8)
                    current_g1 = int(m.get('gol1', 0))
                    for g_val in range(8):
                        with g1_cols[g_val]:
                            is_selected_1 = (current_g1 == g_val)
                            btn_label = f"✨ {g_val}" if is_selected_1 else str(g_val)
                            if st.button(btn_label, key=f"top_g1_{b_num}_{match_id}_{g_val}", use_container_width=True):
                                m['gol1'] = g_val
                                salva_dati(db)
                                st.rerun()

                    st.markdown("<div style='margin: 8px 0;'></div>", unsafe_allow_html=True)
                    st.markdown(f"**🥅 {m['p2']} / ⚽ {m['a2']} (Gol Coppia 2)**")
                    g2_cols = st.columns(8)
                    current_g2 = int(m.get('gol2', 0))
                    for g_val in range(8):
                        with g2_cols[g_val]:
                            is_selected_2 = (current_g2 == g_val)
                            btn_label = f"✨ {g_val}" if is_selected_2 else str(g_val)
                            if st.button(btn_label, key=f"top_g2_{b_num}_{match_id}_{g_val}", use_container_width=True):
                                m['gol2'] = g_val
                                salva_dati(db)
                                st.rerun()

                    st.markdown("<div style='margin: 12px 0;'></div>", unsafe_allow_html=True)
                    if st.button("💾 Conferma e Salva Risultato Finale", key=f"top_save_{b_num}_{match_id}", use_container_width=True):
                        m['giocata'] = True
                        ricalcola_classifiche()
                        salva_dati(db)
                        st.success("Risultato salvato con successo!")
                        st.rerun()

    st.markdown("---")

    # --- PROSSIMI IN CODA ---
    num_partite_in_corso = len(partite_per_tavolo)
    st.markdown(f"### 📢 PROSSIMI IN CODA ({num_partite_in_corso} in attesa):")
    
    partite_in_coda = []
    tavoli_occupati_ids = [val[0]['id'] for val in partite_per_tavolo.values()]
    
    for t_obj in db["turni_partite"]:
        for m in t_obj["partite"]:
            if not m.get("giocata", False) and m['id'] not in tavoli_occupati_ids:
                partite_in_coda.append((t_obj['turno'], m))

    if partite_in_coda and num_partite_in_corso > 0:
        for turno_num, m in partite_in_coda[:num_partite_in_corso]:
            st.html(f"""
                <div class="queue-match-box">
                    <div style="font-size: 0.85rem; color: #ffffff; font-weight: 700; margin-bottom: 4px;">👉 IN CODA (Turno {turno_num})</div>
                    <div style="display: flex; justify-content: space-around; align-items: center; font-weight: 600; font-size: 1rem; color: #ffffff;">
                        <span>🥅 {m['p1']} / ⚽ {m['a1']}</span>
                        <span style="color: #ffffff; font-weight: 800;">VS</span>
                        <span>🥅 {m['p2']} / ⚽ {m['a2']}</span>
                    </div>
                </div>
            """)
    else:
        st.info("Nessuna altra partita in coda.")

    st.markdown("---")

    # --- CLASSIFICHE IN TEMPO REALE ---
    st.html("<h2 style='text-align: center; color: #38bdf8; margin-bottom: 20px; font-weight: 700; text-shadow: 0 0 10px rgba(56,189,248,0.3);'>🏆 CLASSIFICHE IN TEMPO REALE 🏆</h2>")

    # TABELLA PORTIERI
    sorted_p = sorted(db["punti_portieri"].items(), key=lambda x: (x[1], db["dr_portieri"].get(x[0], 0)), reverse=True)
    rows_p_html = ""
    for idx, (p, pt) in enumerate(sorted_p):
        dr = db["dr_portieri"].get(p, 0)
        dr_str = f"+{dr}" if dr > 0 else str(dr)
        gioc, tot = calcola_partite_giocate('portiere', p)
        css_class = "qualificato" if idx < 8 else "eliminato"
        rows_p_html += f"""
            <tr class="{css_class}">
                <td><b>{idx+1}°</b></td>
                <td style="text-align: left; font-weight: 600;">🥅 {p}</td>
                <td><b>{pt}</b></td>
                <td>{dr_str}</td>
                <td>{gioc}/{tot}</td>
            </tr>
        """

    table_p_full = f"""
    <div class="ranking-card">
        <div class="ranking-title" style="color: #38bdf8;">🥅 CLASSIFICA PORTIERI</div>
        <table class="styled-table">
            <thead>
                <tr>
                    <th>Pos</th>
                    <th style="text-align: left;">Portiere</th>
                    <th>Punti</th>
                    <th>DR</th>
                    <th>Giocate</th>
                </tr>
            </thead>
            <tbody>
                {rows_p_html}
            </tbody>
        </table>
    </div>
    """
    st.html(table_p_full)

    # TABELLA ATTACCANTI
    sorted_a = sorted(db["punti_attaccanti"].items(), key=lambda x: (x[1], db["dr_attaccanti"].get(x[0], 0)), reverse=True)
    rows_a_html = ""
    for idx, (a, pt) in enumerate(sorted_a):
        dr = db["dr_attaccanti"].get(a, 0)
        dr_str = f"+{dr}" if dr > 0 else str(dr)
        gioc, tot = calcola_partite_giocate('attaccante', a)
        css_class = "qualificato" if idx < 8 else "eliminato"
        rows_a_html += f"""
            <tr class="{css_class}">
                <td><b>{idx+1}°</b></td>
                <td style="text-align: left; font-weight: 600;">⚽ {a}</td>
                <td><b>{pt}</b></td>
                <td>{dr_str}</td>
                <td>{gioc}/{tot}</td>
            </tr>
        """

    table_a_full = f"""
    <div class="ranking-card">
        <div class="ranking-title" style="color: #4ade80;">⚽ CLASSIFICA ATTACCANTI</div>
        <table class="styled-table">
            <thead>
                <tr>
                    <th>Pos</th>
                    <th style="text-align: left;">Attaccante</th>
                    <th>Punti</th>
                    <th>DR</th>
                    <th>Giocate</th>
                </tr>
            </thead>
            <tbody>
                {rows_a_html}
            </tbody>
        </table>
    </div>
    """
    st.html(table_a_full)

    st.markdown("---")

    # --- LISTA COMPLETA TURNI (ARCHIVIO) ---
    st.markdown("### 📅 Partite dei Turni (Archivio)")

    for turno_obj in db["turni_partite"]:
        turno_num = turno_obj['turno']
        tutte_giocate = all(m.get("giocata", False) for m in turno_obj["partite"])
        alcuna_giocata = any(m.get("giocata", False) for m in turno_obj["partite"])
        in_corso = alcuna_giocata and not tutte_giocate

        if tutte_giocate:
            header_text = f"Turno {turno_num} (Completato ✅)"
            espanso_default = False
        elif in_corso:
            header_text = f"Turno {turno_num} (In corso ⏳)"
            espanso_default = True
        else:
            header_text = f"Turno {turno_num} (Da giocare ⏳)"
            espanso_default = False

        with st.expander(header_text, expanded=espanso_default):
            for idx, m in enumerate(turno_obj["partite"]):
                tavolo_num = (idx % num_tavoli) + 1
                match_id = m['id']
                
                if m["giocata"]:
                    box_bg = "linear-gradient(135deg, #7f1d1d, #450a0a)"
                    border_color = "#ef4444"
                    text_content = f"<span style='color: #ffffff; font-size: 1.15rem; font-weight: 700;'>Risultato: {m['gol1']} - {m['gol2']}</span>"
                    label_stato = f"Biliardino {tavolo_num} (Giocata ✅)"
                else:
                    box_bg = "linear-gradient(135deg, #064e3b, #022c22)"
                    border_color = "#10b981"
                    text_content = "<span style='color: #ffffff; font-size: 1.25rem; font-weight: 800;'>VS</span>"
                    label_stato = f"Biliardino {tavolo_num}"

                st.html(f"""
                    <div style="background: {box_bg}; border: 1px solid {border_color}; border-radius: 12px; padding: 14px; margin-bottom: 10px; color: white; text-align: center; box-shadow: 0 0 10px rgba(0,0,0,0.3);">
                        <div style="font-weight: 700; margin-bottom: 6px; font-size: 0.95rem; text-transform: uppercase; letter-spacing: 0.5px;">{label_stato}</div>
                        <div style="margin-bottom: 6px; font-size: 1.05rem; font-weight: 600; color: #ffffff;">
                            🥅 {m['p1']} &nbsp;&nbsp;&nbsp; ⚽ {m['a1']}
                        </div>
                        <div style="margin: 6px 0;">{text_content}</div>
                        <div style="margin-top: 6px; font-size: 1.05rem; font-weight: 600; color: #ffffff;">
                            🥅 {m['p2']} &nbsp;&nbsp;&nbsp; ⚽ {m['a2']}
                        </div>
                    </div>
                """)

                if is_admin:
                    with st.expander(f"⚙️ Modifica Risultato Biliardino {tavolo_num} (Admin)", expanded=False):
                        st.markdown(f"**🥅 {m['p1']} / ⚽ {m['a1']} (Gol Coppia 1)**")
                        cols_m1 = st.columns(8)
                        curr_m1 = int(m.get('gol1', 0))
                        for g_val in range(8):
                            with cols_m1[g_val]:
                                sel_m1 = (curr_m1 == g_val)
                                lbl_m1 = f"✨ {g_val}" if sel_m1 else str(g_val)
                                if st.button(lbl_m1, key=f"adm_g1_{match_id}_{g_val}", use_container_width=True):
                                    m['gol1'] = g_val
                                    salva_dati(db)
                                    st.rerun()

                        st.markdown("<div style='margin: 8px 0;'></div>", unsafe_allow_html=True)
                        st.markdown(f"**🥅 {m['p2']} / ⚽ {m['a2']} (Gol Coppia 2)**")
                        cols_m2 = st.columns(8)
                        curr_m2 = int(m.get('gol2', 0))
                        for g_val in range(8):
                            with cols_m2[g_val]:
                                sel_m2 = (curr_m2 == g_val)
                                lbl_m2 = f"✨ {g_val}" if sel_m2 else str(g_val)
                                if st.button(lbl_m2, key=f"adm_g2_{match_id}_{g_val}", use_container_width=True):
                                    m['gol2'] = g_val
                                    salva_dati(db)
                                    st.rerun()

                        st.markdown("<div style='margin: 10px 0;'></div>", unsafe_allow_html=True)
                        if st.button(f"💾 Salva Modifica", key=f"save_{match_id}", use_container_width=True):
                            m['giocata'] = True
                            ricalcola_classifiche()
                            salva_dati(db)
                            st.success("Salvato!")
                            st.rerun()

    st.markdown("---")

    # --- SEZIONE IN FONDO: LE PARTITE PERSONALI DEL GIOCATORE LOGGATO ---
    if giocatore_selezionato != "-- Seleziona il tuo nome --":
        partite_filtrate = []
        for t_obj in db["turni_partite"]:
            for idx, m in enumerate(t_obj["partite"]):
                if m['p1'] == giocatore_selezionato or m['a1'] == giocatore_selezionato or m['p2'] == giocatore_selezionato or m['a2'] == giocatore_selezionato:
                    tavolo_num = (idx % num_tavoli) + 1
                    partite_filtrate.append({"turno": t_obj["turno"], "tavolo": tavolo_num, "m": m})

        if partite_filtrate:
            st.html(f"""
                <div style="background: linear-gradient(135deg, #1e1b4b, #311033); border: 2px solid #f59e0b; border-radius: 16px; padding: 18px; margin-bottom: 16px; box-shadow: 0 0 15px rgba(245, 158, 11, 0.3);">
                    <h4 style="margin: 0 0 12px 0; color: #fbbf24; font-size: 1.15rem; font-weight: 700;">🔥 LE PARTITE DI {giocatore_selezionato.upper()}:</h4>
            """)
            for item in partite_filtrate:
                m = item["m"]
                if m.get("giocata", False):
                    center_txt = f"<span style='color: #ffffff; font-weight: 700;'>Risultato: {m['gol1']} - {m['gol2']} (Giocata ✅)</span>"
                else:
                    center_txt = f"<span style='color: #ffffff; font-weight: 700;'>⏳ Biliardino {item['tavolo']} (Da giocare)</span>"

                st.html(f"""
                    <div style="background-color: #111827; border: 1px solid #f59e0b; border-radius: 10px; padding: 12px 14px; margin-bottom: 10px; box-shadow: 0 0 8px rgba(245,158,11,0.2);">
                        <div style="font-size: 0.85rem; color: #ffffff; font-weight: 700; margin-bottom: 4px;">TURNO {item['turno']} • BILIARDINO {item['tavolo']}</div>
                        <div style="display: flex; justify-content: space-around; align-items: center; font-weight: 600; font-size: 1.05rem; color: #ffffff;">
                            <span>🥅 {m['p1']} / ⚽ {m['a1']}</span>
                            <span style="font-weight: 800; color: #ffffff;">VS</span>
                            <span>🥅 {m['p2']} / ⚽ {m['a2']}</span>
                        </div>
                        <div style="text-align: center; margin-top: 8px; font-size: 0.95rem;">{center_txt}</div>
                    </div>
                """)
            st.html('</div>')

    if is_admin:
        st.markdown("---")
        if st.button("🏆 Avvia Fase Eliminazione Diretta (Quarti)", use_container_width=True):
            sorted_p_list = sorted(db["punti_portieri"].items(), key=lambda x: (x[1], db["dr_portieri"].get(x[0], 0)), reverse=True)
            sorted_a_list = sorted(db["punti_attaccanti"].items(), key=lambda x: (x[1], db["dr_attaccanti"].get(x[0], 0)), reverse=True)
            
            top_p = [p[0] for p in sorted_p_list[:8]]
            top_a = [a[0] for a in sorted_a_list[:8]]
            
            quarti_partite = [
                {"id": "ef_t1_m1", "p1": top_p[0], "a1": top_a[0], "p2": top_p[7], "a2": top_a[7], "giocata": False, "in_corso": False, "gol1": 0, "gol2": 0},
                {"id": "ef_t1_m2", "p1": top_p[1], "a1": top_a[1], "p2": top_p[6], "a2": top_a[6], "giocata": False, "in_corso": False, "gol1": 0, "gol2": 0},
                {"id": "ef_t1_m3", "p1": top_p[2], "a1": top_a[2], "p2": top_p[5], "a2": top_a[5], "giocata": False, "in_corso": False, "gol1": 0, "gol2": 0},
                {"id": "ef_t1_m4", "p1": top_p[3], "a1": top_a[3], "p2": top_p[4], "a2": top_a[4], "giocata": False, "in_corso": False, "gol1": 0, "gol2": 0}
            ]
            db["fasi_finali"] = [{"turno": 1, "nome": "Quarti di Finale", "partite": quarti_partite}]
            db["stato"] = "eliminatorie"
            salva_dati(db)
            st.rerun()

# 3. ELIMINATORIE
if db["stato"] == "eliminatorie":
    num_tavoli = db.get("num_tavoli", 3)
    fasi = db["fasi_finali"]
    
    finito_tutto = False
    p1_1, a1_1, p2_1, a2_1, p3_1, a3_1 = "", "", "", "", "", ""
    
    for f_turno in fasi:
        if f_turno['nome'] == "Finali (1°-2° e 3°-4° Posto)":
            fin_partite = f_turno["partite"]
            if len(fin_partite) >= 2 and fin_partite[0].get("giocata", False) and fin_partite[1].get("giocata", False):
                finito_tutto = True
                m1, m2 = fin_partite[0], fin_partite[1]
                if m1["gol1"] >= m1["gol2"]:
                    p1_1, a1_1 = m1["p1"], m1["a1"]
                    p2_1, a2_1 = m1["p2"], m1["a2"]
                else:
                    p1_1, a1_1 = m1["p2"], m1["a2"]
                    p2_1, a2_1 = m1["p1"], m1["a1"]
                if m2["gol1"] >= m2["gol2"]:
                    p3_1, a3_1 = m2["p1"], m2["a1"]
                else:
                    p3_1, a3_1 = m2["p2"], m2["a2"]

    if finito_tutto:
        st.html("""
            <div style="text-align: center; margin-top: 10px; margin-bottom: 20px;">
                <h1 style="color: #38bdf8; font-size: 2.2rem; font-weight: 800; text-shadow: 0 0 15px rgba(56,189,248,0.5);">🏆 TORNEO CONCLUSO! 🏆</h1>
            </div>
        """)

        podio_html = f"""
        <div class="podium-container">
            <div class="podium-step podium-2">
                <div style="font-size: 1rem;">🥈 2° Posto</div>
                <div style="font-size: 0.9rem; margin-top: 6px; font-weight: 600;">🥅 {p2_1}<br>⚽ {a2_1}</div>
            </div>
            <div class="podium-step podium-1">
                <div class="trophy-icon">🏆</div>
                <div style="font-size: 1.2rem; font-weight: 800;">1° Posto</div>
                <div style="font-size: 0.95rem; margin-top: 4px; font-weight: 700;">🥅 {p1_1}<br>⚽ {a1_1}</div>
            </div>
            <div class="podium-step podium-3">
                <div style="font-size: 1rem;">🥉 3° Posto</div>
                <div style="font-size: 0.9rem; margin-top: 6px; font-weight: 600;">🥅 {p3_1}<br>⚽ {a3_1}</div>
            </div>
        </div>
        """
        st.html(podio_html)
        st.markdown("---")
        
        col_f1, col_f2, col_f3 = st.columns([1, 2, 1])
        with col_f2:
            pdf_data = genera_pdf_calendario()
            st.download_button(
                label="📥 Scarica Riepilogo PDF",
                data=pdf_data,
                file_name="riepilogo_finale_torneo.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            if is_admin:
                if st.button("⬅️ Torna alla gestione", use_container_width=True):
                    fin_partite[0]["giocata"] = False
                    salva_dati(db)
                    st.rerun()
    else:
        st.subheader("🏆 Fase a Eliminazione Diretta")
        
        for f_turno in fasi:
            tutti_giocati = True
            alcuna_giocata_ef = any(m.get("giocata", False) for m in f_turno["partite"])
            vincitori_turno = []
            perdenti_turno = []
            
            for idx, m in enumerate(f_turno["partite"]):
                if m.get("giocata", False):
                    if m["gol1"] >= m["gol2"]:
                        vincitori_turno.append({"p": m["p1"], "a": m["a1"]})
                        perdenti_turno.append({"p": m["p2"], "a": m["a2"]})
                    else:
                        vincitori_turno.append({"p": m["p2"], "a": m["a2"]})
                        perdenti_turno.append({"p": m["p1"], "a": m["a1"]})
                else:
                    tutti_giocati = False

            ef_chiuse = tutti_giocati
            ef_in_corso = alcuna_giocata_ef and not tutti_giocati
            
            if ef_chiuse:
                ef_header = f"🔥 {f_turno['nome']} (Completato ✅)"
            elif ef_in_corso:
                ef_header = f"🔥 {f_turno['nome']} (In corso ⏳)"
            else:
                ef_header = f"🔥 {f_turno['nome']} (Da giocare ⏳)"

            with st.expander(ef_header, expanded=ef_in_corso):
                for idx, m in enumerate(f_turno["partite"]):
                    tavolo_num = (idx % num_tavoli) + 1
                    match_id = m['id']

                    if m["giocata"]:
                        box_bg = "linear-gradient(135deg, #7f1d1d, #450a0a)"
                        border_color = "#ef4444"
                        text_content = f"<span style='color: #ffffff; font-size: 1.15rem; font-weight: 700;'>Risultato: {m['gol1']} - {m['gol2']}</span>"
                        label_stato = f"Biliardino {tavolo_num} (Giocata ✅)"
                    else:
                        box_bg = "linear-gradient(135deg, #064e3b, #022c22)"
                        border_color = "#10b981"
                        text_content = "<span style='color: #ffffff; font-size: 1.25rem; font-weight: 800;'>VS</span>"
                        label_stato = f"Biliardino {tavolo_num}"

                    st.html(f"""
                        <div style="background: {box_bg}; border: 1px solid {border_color}; border-radius: 12px; padding: 14px; margin-bottom: 10px; color: white; text-align: center; box-shadow: 0 0 10px rgba(0,0,0,0.3);">
                            <div style="font-weight: 700; margin-bottom: 6px; font-size: 0.95rem; text-transform: uppercase;">{label_stato}</div>
                            <div style="margin-bottom: 6px; font-size: 1.05rem; font-weight: 600; color: #ffffff;">
                                🥅 {m['p1']} &nbsp;&nbsp;&nbsp; ⚽ {m['a1']}
                            </div>
                            <div style="margin: 6px 0;">{text_content}</div>
                            <div style="margin-top: 6px; font-size: 1.05rem; font-weight: 600; color: #ffffff;">
                                🥅 {m['p2']} &nbsp;&nbsp;&nbsp; ⚽ {m['a2']}
                            </div>
                        </div>
                    """)

                    if is_admin:
                        with st.expander(f"⚙️ Modifica Risultato Biliardino {tavolo_num} (Admin)", expanded=False):
                            st.markdown(f"**🥅 {m['p1']} / ⚽ {m['a1']} (Gol Coppia 1)**")
                            cols_ef1 = st.columns(8)
                            curr_ef1 = int(m.get('gol1', 0))
                            for g_val in range(8):
                                with cols_ef1[g_val]:
                                    sel_ef1 = (curr_ef1 == g_val)
                                    lbl_ef1 = f"✨ {g_val}" if sel_ef1 else str(g_val)
                                    if st.button(lbl_ef1, key=f"ef_adm_g1_{match_id}_{g_val}", use_container_width=True):
                                        m['gol1'] = g_val
                                        salva_dati(db)
                                        st.rerun()

                            st.markdown("<div style='margin: 8px 0;'></div>", unsafe_allow_html=True)
                            st.markdown(f"**🥅 {m['p2']} / ⚽ {m['a2']} (Gol Coppia 2)**")
                            cols_ef2 = st.columns(8)
                            curr_ef2 = int(m.get('gol2', 0))
                            for g_val in range(8):
                                with cols_ef2[g_val]:
                                    sel_ef2 = (curr_ef2 == g_val)
                                    lbl_ef2 = f"✨ {g_val}" if sel_ef2 else str(g_val)
                                    if st.button(lbl_ef2, key=f"ef_adm_g2_{match_id}_{g_val}", use_container_width=True):
                                        m['gol2'] = g_val
                                        salva_dati(db)
                                        st.rerun()

                            st.markdown("<div style='margin: 10px 0;'></div>", unsafe_allow_html=True)
                            if st.button("💾 Salva Modifica", key=f"ef_save_{match_id}", use_container_width=True):
                                m['giocata'] = True
                                salva_dati(db)
                                st.rerun()

            if tutti_giocati and is_admin:
                if f_turno['nome'] == "Quarti di Finale" and len(vincitori_turno) == 4 and not any(f['nome'] == "Semifinali" for f in fasi):
                    if st.button("🚀 Genera Semifinali", use_container_width=True):
                        q1, q2, q3, q4 = vincitori_turno[0], vincitori_turno[1], vincitori_turno[2], vincitori_turno[3]
                        semifinale_partite = [
                            {"id": "ef_t2_m1", "p1": q1["p"], "a1": q2["a"], "p2": q3["p"], "a2": q4["a"], "giocata": False, "in_corso": False, "gol1": 0, "gol2": 0},
                            {"id": "ef_t2_m2", "p1": q2["p"], "a1": q1["a"], "p2": q4["p"], "a2": q3["a"], "giocata": False, "in_corso": False, "gol1": 0, "gol2": 0}
                        ]
                        db["fasi_finali"].append({"turno": 2, "nome": "Semifinali", "partite": semifinale_partite})
                        salva_dati(db)
                        st.rerun()
                elif f_turno['nome'] == "Semifinali" and len(vincitori_turno) == 2 and not any(f['nome'] == "Finali (1°-2° e 3°-4° Posto)" for f in fasi):
                    if st.button("🏁 Genera Finali", use_container_width=True):
                        sf1_v, sf2_v = vincitori_turno[0], vincitori_turno[1]
                        sf1_p, sf2_p = perdenti_turno[0], perdenti_turno[1]
                        finali_partite = [
                            {"id": "ef_t3_m1", "p1": sf1_v["p"], "a1": sf2_v["a"], "p2": sf2_v["p"], "a2": sf1_v["a"], "giocata": False, "in_corso": False, "gol1": 0, "gol2": 0},
                            {"id": "ef_t3_m2", "p1": sf1_p["p"], "a1": sf2_p["p"], "p2": sf2_p["p"], "a2": sf1_p["p"], "giocata": False, "in_corso": False, "gol1": 0, "gol2": 0}
                        ]
                        db["fasi_finali"].append({"turno": 3, "nome": "Finali (1°-2° e 3°-4° Posto)", "partite": finali_partite})
                        salva_dati(db)
                        st.rerun()

        if is_admin:
            if st.button("⬅️ Indietro ai Gironi", use_container_width=True):
                db["stato"] = "gironi"
                salva_dati(db)
                st.rerun()
