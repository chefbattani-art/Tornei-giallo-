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

# --- CSS PERSONALIZZATO: GAMING NEON (BLU, AZZURRO, ORO, VERDE) ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&display=swap');

        :root {
            color-scheme: dark;
        }

        html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stToolbar"] {
            background-color: #030712 !important;
            color: #f8fafc !important;
        }

        [class*="css"] {
            font-family: 'Outfit', sans-serif;
            color: #f8fafc;
            font-size: 1.05rem;
        }

        .block-container {
            padding-top: 1.2rem !important;
            padding-bottom: 2rem !important;
            padding-left: 1.2rem !important;
            padding-right: 1.2rem !important;
            background-color: #030712 !important;
            background-image: 
                radial-gradient(at 10% 10%, rgba(0, 242, 254, 0.12) 0px, transparent 50%),
                radial-gradient(at 90% 90%, rgba(34, 197, 94, 0.08) 0px, transparent 50%),
                radial-gradient(at 50% 50%, rgba(37, 99, 235, 0.1) 0px, transparent 60%);
        }

        div[data-testid="stExpander"] summary,
        div[data-testid="stExpander"] summary p,
        div[data-testid="stExpander"] p,
        small {
            color: #f8fafc !important;
            font-weight: 600 !important;
        }

        button[data-testid="stBaseButton-secondary"], 
        button[data-testid="stBaseButton-primary"],
        div.stButton > button {
            background: linear-gradient(135deg, #0f172a, #1e293b) !important;
            color: #38bdf8 !important;
            border: 1px solid #00f2fe !important;
            border-radius: 10px !important;
            font-weight: 700 !important;
            font-size: 1.1rem !important;
            height: 48px !important;
            box-shadow: 0 0 10px rgba(0, 242, 254, 0.2);
            transition: all 0.3s ease;
        }
        
        button[data-testid="stBaseButton-secondary"]:hover,
        div.stButton > button:hover {
            background: linear-gradient(135deg, #1e293b, #0284c7) !important;
            border-color: #fbbf24 !important;
            color: #fbbf24 !important;
            box-shadow: 0 0 15px rgba(251, 191, 36, 0.5);
        }

        input, textarea, div[data-baseweb="select"] > div {
            background-color: #0b1329 !important;
            color: #38bdf8 !important;
            border: 1px solid #00f2fe !important;
            border-radius: 8px !important;
            font-size: 1.05rem !important;
        }

        [data-testid="stExpander"] {
            background-color: #080e1e !important;
            border: 1px solid #2563eb !important;
            border-radius: 12px !important;
            box-shadow: 0 0 12px rgba(37, 99, 235, 0.2);
        }

        .ranking-card {
            background: linear-gradient(145deg, #080e1e, #030712);
            border: 2px solid #00f2fe;
            border-radius: 20px;
            padding: 20px;
            box-shadow: 0 0 25px rgba(0, 242, 254, 0.3);
            margin-bottom: 20px;
        }

        .ranking-title {
            text-align: center;
            color: #00f2fe;
            font-size: 1.4rem;
            font-weight: 700;
            margin-bottom: 16px;
            letter-spacing: 0.8px;
            text-shadow: 0 0 12px rgba(0, 242, 254, 0.6);
        }

        .player-row-green {
            background: linear-gradient(135deg, #064e3b, #022c22);
            border: 2px solid #22c55e;
            border-radius: 14px;
            padding: 12px 16px;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 0 15px rgba(34, 197, 94, 0.25);
        }

        .player-row-red {
            background: linear-gradient(135deg, #7f1d1d, #450a0a);
            border: 2px solid #ef4444;
            border-radius: 14px;
            padding: 12px 16px;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 0 15px rgba(239, 68, 68, 0.25);
        }

        .live-match-box {
            background: linear-gradient(135deg, #0f172a, #172554);
            border: 2px solid #fbbf24;
            border-radius: 14px;
            padding: 12px 16px;
            margin-bottom: 12px;
            box-shadow: 0 0 20px rgba(251, 191, 36, 0.4);
        }

        .queue-match-box {
            background: linear-gradient(135deg, #022c22, #064e3b);
            border: 1.5px solid #22c55e;
            border-radius: 12px;
            padding: 10px 14px;
            margin-bottom: 8px;
            color: #f8fafc;
            box-shadow: 0 0 15px rgba(34, 197, 94, 0.25);
        }

        .alert-active-game {
            background: linear-gradient(135deg, #450a0a, #7f1d1d);
            border: 2px solid #ef4444;
            border-radius: 14px;
            padding: 14px;
            margin-bottom: 16px;
            text-align: center;
            box-shadow: 0 0 25px rgba(239, 68, 68, 0.6);
        }
        
        .alert-queue-game {
            background: linear-gradient(135deg, #064e3b, #022c22);
            border: 2px solid #22c55e;
            border-radius: 14px;
            padding: 14px;
            margin-bottom: 16px;
            text-align: center;
            box-shadow: 0 0 25px rgba(34, 197, 94, 0.4);
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

# --- LOGO E HEADER COMUNE STILOSO NEON ---
logo_html = ""
if os.path.exists(LOGO_FILE):
    with open(LOGO_FILE, "rb") as f:
        logo_b64 = b64encode(f.read()).decode("utf-8")
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="max-width: 120px; width: 100%; height: auto; margin-bottom: 8px;" /><br>'

st.html(
    f"""
    <div style="text-align: center; margin-bottom: 14px; background: linear-gradient(135deg, #080e1e, #0b1329); padding: 20px; border-radius: 20px; box-shadow: 0 0 25px rgba(0, 242, 254, 0.25); border: 2px solid #00f2fe;">
        {logo_html}
        <h1 style="margin: 0; color: #00f2fe; font-size: 1.8rem; font-weight: 800; text-shadow: 0 0 15px rgba(0, 242, 254, 0.6);">🏆 Torneo Biliardino 'Giallo' Live</h1>
        <span style="display: inline-block; margin-top: 10px; background-color: rgba(30, 58, 138, 0.7); color: #38bdf8; padding: 6px 16px; border-radius: 20px; font-weight: 700; font-size: 0.95rem; border: 1px solid #00f2fe; box-shadow: 0 0 10px rgba(56, 189, 248, 0.3);">Regolamento Uisp 3 tocchi</span>
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
                <div style="background: #080e1e; padding: 12px 18px; border-radius: 12px; border: 1px solid #00f2fe; font-weight: 600; color: #f8fafc; font-size: 1.05rem; box-shadow: 0 0 10px rgba(0, 242, 254, 0.2);">
                    👤 Stai visualizzando come: <span style="color: #fbbf24; font-weight: 700;">{giocatore_selezionato}</span>
                </div>
            """, unsafe_allow_html=True)
        with col_n2:
            if st.button("🔄 Cambia Nome", use_container_width=True):
                st.query_params.clear()
                st.rerun()
        st.markdown("---")
else:
    giocatore_selezionato = "-- Seleziona il tuo nome --"

# --- INDIVIDUAZIONE ESATTA DELle PARTITE ATTIVE SUI BILIARDINI ---
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

# --- VERIFICA SE IL GIOCATORE HA UNA PARTITA IN CORSO SUI TAVOLI ATTIVI O IN CODA ---
partita_utente_corrente = None
tavolo_utente_corrente = None
turno_utente_corrente = None

partita_utente_in_coda = None
turno_utente_in_coda = None

if giocatore_selezionato != "-- Seleziona il tuo nome --" and not is_admin and db["stato"] == "gironi":
    # 1. Controlla se è su uno dei tavoli attivi correnti (Partita in corso effettiva)
    for b_num in range(1, num_tavoli + 1):
        for t_obj in db["turni_partite"]:
            for idx, m in enumerate(t_obj["partite"]):
                if ((idx % num_tavoli) + 1) == b_num and not m.get("giocata", False):
                    if (giocatore_selezionato == m['p1'] or giocatore_selezionato == m['a1'] or 
                        giocatore_selezionato == m['p2'] or giocatore_selezionato == m['a2']):
                        
                        # Verifica che sia la prima partita da giocare per questo tavolo
                        match_tavolo_attivo = None
                        for t_check in db["turni_partite"]:
                            for idx_c, mc in enumerate(t_check["partite"]):
                                if ((idx_c % num_tavoli) + 1) == b_num and not mc.get("giocata", False):
                                    if match_tavolo_attivo is None:
                                        match_tavolo_attivo = mc
                            if match_tavolo_attivo:
                                break
                        if match_tavolo_attivo and match_tavolo_attivo['id'] == m['id']:
                            partita_utente_corrente = m
                            tavolo_utente_corrente = b_num
                            turno_utente_corrente = t_obj['turno']
                            break
            if partita_utente_corrente:
                break
        if partita_utente_corrente:
            break

    # 2. Se NON è su un tavolo attivo, controlla se ha una partita in coda (nei turni successivi/non attivi)
    if not partita_utente_corrente:
        tavoli_occupati_ids = [m_att['id'] for m_att in partite_attive_correnti]
        for t_obj in db["turni_partite"]:
            for idx, m in enumerate(t_obj["partite"]):
                if not m.get("giocata", False) and m['id'] not in tavoli_occupati_ids:
                    if (giocatore_selezionato == m['p1'] or giocatore_selezionato == m['a1'] or 
                        giocatore_selezionato == m['p2'] or giocatore_selezionato == m['a2']):
                        partita_utente_in_coda = m
                        turno_utente_in_coda = t_obj['turno']
                        break
            if partita_utente_in_coda:
                break

# --- MOSTRA BOX IN ALTO SE IN CORSO O IN CODA ---
if partita_utente_corrente:
    st.html("""
        <div class="alert-active-game">
            <h4 style="margin: 0; color: #ffffff; font-size: 1.15rem; font-weight: 700;">🚨 ATTENZIONE: LA TUA PARTITA È IN CORSO!</h4>
            <p style="margin: 6px 0 0 0; color: #f8fafc; font-size: 1rem; font-weight: 600;">
                Inserisci qui sotto il risultato finale e conferma.
            </p>
        </div>
    """)
    
    m_up = partita_utente_corrente
    b_num_up = tavolo_utente_corrente
    turno_up = turno_utente_corrente
    match_id_up = m_up['id']

    st.html(f"""
        <div class="live-match-box">
            <div style="font-weight: 700; color: #fbbf24; margin-bottom: 8px; font-size: 0.95rem; display: flex; justify-content: space-between; text-shadow: 0 0 8px rgba(251,191,36,0.5);">
                <span>🏟️ BILIARDINO {b_num_up} (IL TUO MATCH)</span>
                <span>TURNO {turno_up}</span>
            </div>
            <div style="background-color: #030712; padding: 12px 14px; border-radius: 10px; border: 1.5px solid #00f2fe; text-align: center; box-shadow: inset 0 0 10px rgba(0,242,254,0.15);">
                <div style="font-weight: 600; font-size: 1.02rem; color: #f8fafc; margin-bottom: 4px;">
                    🥅 {m_up['p1']} / ⚽ {m_up['a1']}
                </div>
                <div style="font-weight: 800; color: #fbbf24; font-size: 1.1rem; margin: 4px 0; text-shadow: 0 0 10px rgba(251,191,36,0.6);">VS</div>
                <div style="font-weight: 600; font-size: 1.02rem; color: #f8fafc; margin-top: 4px;">
                    🥅 {m_up['p2']} / ⚽ {m_up['a2']}
                </div>
            </div>
        </div>
    """)

    with st.expander(f"⚡ Inserisci Risultato Biliardino {b_num_up}", expanded=True):
        st.markdown(f"**🥅 {m_up['p1']} / ⚽ {m_up['a1']} (Gol Coppia 1)**")
        current_g1 = int(m_up.get('gol1', 0))
        
        r1_cols = st.columns(4)
        for g_val in range(4):
            with r1_cols[g_val]:
                is_sel = (current_g1 == g_val)
                lbl = f"⭐ {g_val}" if is_sel else str(g_val)
                if st.button(lbl, key=f"top_user_g1_{match_id_up}_{g_val}", use_container_width=True):
                    m_up['gol1'] = g_val
                    salva_dati(db)
                    st.rerun()
                    
        r2_cols = st.columns(4)
        for g_val in range(4, 8):
            with r2_cols[g_val - 4]:
                is_sel = (current_g1 == g_val)
                lbl = f"⭐ {g_val}" if is_sel else str(g_val)
                if st.button(lbl, key=f"top_user_g1_{match_id_up}_{g_val}", use_container_width=True):
                    m_up['gol1'] = g_val
                    salva_dati(db)
                    st.rerun()

        st.markdown("<div style='margin: 10px 0;'></div>", unsafe_allow_html=True)
        
        st.markdown(f"**🥅 {m_up['p2']} / ⚽ {m_up['a2']} (Gol Coppia 2)**")
        current_g2 = int(m_up.get('gol2', 0))
        
        r3_cols = st.columns(4)
        for g_val in range(4):
            with r3_cols[g_val]:
                is_sel = (current_g2 == g_val)
                lbl = f"⭐ {g_val}" if is_sel else str(g_val)
                if st.button(lbl, key=f"top_user_g2_{match_id_up}_{g_val}", use_container_width=True):
                    m_up['gol2'] = g_val
                    salva_dati(db)
                    st.rerun()
                    
        r4_cols = st.columns(4)
        for g_val in range(4, 8):
            with r4_cols[g_val - 4]:
                is_sel = (current_g2 == g_val)
                lbl = f"⭐ {g_val}" if is_sel else str(g_val)
                if st.button(lbl, key=f"top_user_g2_{match_id_up}_{g_val}", use_container_width=True):
                    m_up['gol2'] = g_val
                    salva_dati(db)
                    st.rerun()

        st.markdown("<div style='margin: 14px 0;'></div>", unsafe_allow_html=True)
        if st.button("💾 Conferma e Salva Risultato Finale", key=f"top_user_save_{match_id_up}", use_container_width=True):
            m_up['giocata'] = True
            ricalcola_classifiche()
            salva_dati(db)
            st.success("Risultato salvato con successo!")
            st.rerun()
    st.markdown("---")

elif partita_utente_in_coda:
    m_coda = partita_utente_in_coda
    t_coda = turno_utente_in_coda
    st.html(f"""
        <div class="alert-queue-game">
            <h4 style="margin: 0; color: #4ade80; font-size: 1.1rem; font-weight: 700;">⏳ LA TUA PROSSIMA PARTITA È IN CODA</h4>
            <p style="margin: 4px 0 0 0; color: #f8fafc; font-size: 0.95rem; font-weight: 600;">
                Turno {t_coda} - Attendi che si liberi un biliardino.
            </p>
        </div>
        <div class="queue-match-box">
            <div style="font-size: 0.85rem; color: #4ade80; font-weight: 700; margin-bottom: 4px;">👉 IL TUO PROSSIMO MATCH (Turno {t_coda})</div>
            <div style="text-align: center; font-weight: 600; font-size: 0.98rem; color: #f8fafc;">
                <div>🥅 {m_coda['p1']} / ⚽ {m_coda['a1']}</div>
                <div style="color: #fbbf24; font-weight: 800; margin: 2px 0;">VS</div>
                <div>🥅 {m_coda['p2']} / ⚽ {m_coda['a2']}</div>
            </div>
        </div>
    """)
    st.markdown("---")

st.html(
    """
    <div style="padding: 10px; background-color: #080e1e; border-radius: 10px; text-align: center; margin-bottom: 14px; border: 1px solid #22c55e; box-shadow: 0 0 10px rgba(34, 197, 94, 0.2);">
        🔄 <a href="javascript:window.location.reload(true)" style="text-decoration: none; color: #4ade80; font-weight: 700; font-size: 0.95rem;">
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
                    <div style="font-weight: 700; color: #fbbf24; margin-bottom: 8px; font-size: 0.95rem; display: flex; justify-content: space-between; text-shadow: 0 0 8px rgba(251,191,36,0.5);">
                        <span>🏟️ BILIARDINO {b_num}</span>
                        <span>TURNO {turno_num}</span>
                    </div>
                    <div style="background-color: #030712; padding: 12px 14px; border-radius: 10px; border: 1.5px solid #00f2fe; text-align: center; box-shadow: inset 0 0 10px rgba(0,242,254,0.15);">
                        <div style="font-weight: 600; font-size: 1.02rem; color: #f8fafc; margin-bottom: 4px;">
                            🥅 {m['p1']} / ⚽ {m['a1']}
                        </div>
                        <div style="font-weight: 800; color: #fbbf24; font-size: 1.1rem; margin: 4px 0; text-shadow: 0 0 10px rgba(251,191,36,0.6);">VS</div>
                        <div style="font-weight: 600; font-size: 1.02rem; color: #f8fafc; margin-top: 4px;">
                            🥅 {m['p2']} / ⚽ {m['a2']}
                        </div>
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
                    
                    st.markdown(f"**🥅 {m['p1']} / ⚽ {m['a1']} (Gol Coppia 1)**")
                    current_g1 = int(m.get('gol1', 0))
                    
                    r1_cols = st.columns(4)
                    for g_val in range(4):
                        with r1_cols[g_val]:
                            is_sel = (current_g1 == g_val)
                            lbl = f"⭐ {g_val}" if is_sel else str(g_val)
                            if st.button(lbl, key=f"top_g1_{b_num}_{match_id}_{g_val}", use_container_width=True):
                                m['gol1'] = g_val
                                salva_dati(db)
                                st.rerun()
                                
                    r2_cols = st.columns(4)
                    for g_val in range(4, 8):
                        with r2_cols[g_val - 4]:
                            is_sel = (current_g1 == g_val)
                            lbl = f"⭐ {g_val}" if is_sel else str(g_val)
                            if st.button(lbl, key=f"top_g1_{b_num}_{match_id}_{g_val}", use_container_width=True):
                                m['gol1'] = g_val
                                salva_dati(db)
                                st.rerun()

                    st.markdown("<div style='margin: 10px 0;'></div>", unsafe_allow_html=True)
                    
                    st.markdown(f"**🥅 {m['p2']} / ⚽ {m['a2']} (Gol Coppia 2)**")
                    current_g2 = int(m.get('gol2', 0))
                    
                    r3_cols = st.columns(4)
                    for g_val in range(4):
                        with r3_cols[g_val]:
                            is_sel = (current_g2 == g_val)
                            lbl = f"⭐ {g_val}" if is_sel else str(g_val)
                            if st.button(lbl, key=f"top_g2_{b_num}_{match_id}_{g_val}", use_container_width=True):
                                m['gol2'] = g_val
                                salva_dati(db)
                                st.rerun()
                                
                    r4_cols = st.columns(4)
                    for g_val in range(4, 8):
                        with r4_cols[g_val - 4]:
                            is_sel = (current_g2 == g_val)
                            lbl = f"⭐ {g_val}" if is_sel else str(g_val)
                            if st.button(lbl, key=f"top_g2_{b_num}_{match_id}_{g_val}", use_container_width=True):
                                m['gol2'] = g_val
                                salva_dati(db)
                                st.rerun()

                    st.markdown("<div style='margin: 14px 0;'></div>", unsafe_allow_html=True)
                    if st.button("💾 Conferma e Salva Risultato Finale", key=f"top_save_{b_num}_{match_id}", use_container_width=True):
                        m['giocata'] = True
                        ricalcola_classifiche()
                        salva_dati(db)
                        st.success("Risultato salvato con successo!")
                        st.rerun()

    st.markdown("---")

    # --- PROSSIMI IN CODA (VINCOLATO ESATTAMENTE AL NUMERO DI PARTITE IN CORSO/TAVOLI ATTIVI) ---
    num_partite_in_corso = len(partite_per_tavolo)
    tavoli_occupati_ids = [val[0]['id'] for val in partite_per_tavolo.values()]
    
    partite_in_coda = []
    for t_obj in db["turni_partite"]:
        for m in t_obj["partite"]:
            if not m.get("giocata", False) and m['id'] not in tavoli_occupati_ids:
                partite_in_coda.append((t_obj['turno'], m))

    st.markdown(f"### 📢 PROSSIMI IN CODA ({min(len(partite_in_coda), num_partite_in_corso)} in attesa):")

    if partite_in_coda and num_partite_in_corso > 0:
        for turno_num, m in partite_in_coda[:num_partite_in_corso]:
            st.html(f"""
                <div class="queue-match-box">
                    <div style="font-size: 0.85rem; color: #4ade80; font-weight: 700; margin-bottom: 4px;">👉 IN CODA (Turno {turno_num})</div>
                    <div style="text-align: center; font-weight: 600; font-size: 0.98rem; color: #f8fafc;">
                        <div>🥅 {m['p1']} / ⚽ {m['a1']}</div>
                        <div style="color: #fbbf24; font-weight: 800; margin: 2px 0;">VS</div>
                        <div>🥅 {m['p2']} / ⚽ {m['a2']}</div>
                    </div>
                </div>
            """)
    else:
        st.info("Nessuna altra partita in coda.")

    st.markdown("---")

    # --- CLASSIFICHE A BLOCCHI SEPARATI ---
    st.html("<h2 style='text-align: center; color: #00f2fe; margin-bottom: 20px; font-weight: 800; text-shadow: 0 0 15px rgba(0,242,254,0.5);'>🏆 CLASSIFICHE IN TEMPO REALE 🏆</h2>")

    sorted_p = sorted(db["punti_portieri"].items(), key=lambda x: (x[1], db["dr_portieri"].get(x[0], 0)), reverse=True)
    
    html_portieri = f"""
    <div class="ranking-card">
        <div class="ranking-title">🥅 CLASSIFICA PORTIERI</div>
    """
    for idx, (p, pt) in enumerate(sorted_p):
        dr = db["dr_portieri"].get(p, 0)
        dr_str = f"+{dr}" if dr > 0 else str(dr)
        gioc, tot = calcola_partite_giocate('portiere', p)
        css_box = "player-row-green" if idx < 8 else "player-row-red"
        
        html_portieri += f"""
        <div class="{css_box}">
            <div style="font-weight: 800; font-size: 1.1rem; width: 15%;"><b>{idx+1}°</b></div>
            <div style="font-weight: 700; width: 55%; text-align: left;">🥅 {p}</div>
            <div style="font-weight: 600; width: 30%; text-align: right; font-size: 0.95rem;">
                <span style="margin-right: 8px;">PT <b>{pt}</b></span>
                <span style="margin-right: 8px;">G <b>{gioc}/{tot}</b></span>
                <span>DR <b>{dr_str}</b></span>
            </div>
        </div>
        """
    html_portieri += "</div>"
    st.html(html_portieri)

    sorted_a = sorted(db["punti_attaccanti"].items(), key=lambda x: (x[1], db["dr_attaccanti"].get(x[0], 0)), reverse=True)
    
    html_attaccanti = f"""
    <div class="ranking-card">
        <div class="ranking-title" style="color: #22c55e; text-shadow: 0 0 12px rgba(34,197,94,0.6);">⚽ CLASSIFICA ATTACCANTI</div>
    """
    for idx, (a, pt) in enumerate(sorted_a):
        dr = db["dr_attaccanti"].get(a, 0)
        dr_str = f"+{dr}" if dr > 0 else str(dr)
        gioc, tot = calcola_partite_giocate('attaccante', a)
        css_box = "player-row-green" if idx < 8 else "player-row-red"
        
        html_attaccanti += f"""
        <div class="{css_box}">
            <div style="font-weight: 800; font-size: 1.1rem; width: 15%;"><b>{idx+1}°</b></div>
            <div style="font-weight: 700; width: 55%; text-align: left;">⚽ {a}</div>
            <div style="font-weight: 600; width: 30%; text-align: right; font-size: 0.95rem;">
                <span style="margin-right: 8px;">PT <b>{pt}</b></span>
                <span style="margin-right: 8px;">G <b>{gioc}/{tot}</b></span>
                <span>DR <b>{dr_str}</b></span>
            </div>
        </div>
        """
    html_attaccanti += "</div>"
    st.html(html_attaccanti)

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
                    box_bg = "linear-gradient(135deg, #450a0a, #7f1d1d)"
                    border_color = "#ef4444"
                    text_content = f"<div style='color: #fbbf24; font-size: 1.1rem; font-weight: 700; text-shadow: 0 0 8px rgba(251,191,36,0.4); margin: 6px 0;'>Risultato: {m['gol1']} - {m['gol2']}</div>"
                    label_stato = f"Biliardino {tavolo_num} (Giocata ✅)"
                else:
                    box_bg = "linear-gradient(135deg, #022c22, #064e3b)"
                    border_color = "#22c55e"
                    text_content = "<div style='color: #fbbf24; font-size: 1.1rem; font-weight: 800; text-shadow: 0 0 8px rgba(251,191,36,0.5); margin: 6px 0;'>VS</div>"
                    label_stato = f"Biliardino {tavolo_num}"

                st.html(f"""
                    <div style="background: {box_bg}; border: 1px solid {border_color}; border-radius: 12px; padding: 14px; margin-bottom: 10px; color: white; text-align: center; box-shadow: 0 0 12px rgba(0,242,254,0.15);">
                        <div style="font-weight: 700; margin-bottom: 6px; font-size: 0.95rem; text-transform: uppercase; letter-spacing: 0.5px; color: #00f2fe;">{label_stato}</div>
                        <div style="font-size: 1rem; font-weight: 600; color: #f8fafc;">
                            🥅 {m['p1']} / ⚽ {m['a1']}
                        </div>
                        {text_content}
                        <div style="font-size: 1rem; font-weight: 600; color: #f8fafc;">
                            🥅 {m['p2']} / ⚽ {m['a2']}
                        </div>
                    </div>
                """)

                if is_admin:
                    with st.expander(f"⚙️ Modifica Risultato Biliardino {tavolo_num} (Admin)", expanded=False):
                        st.markdown(f"**🥅 {m['p1']} / ⚽ {m['a1']} (Gol Coppia 1)**")
                        curr_m1 = int(m.get('gol1', 0))
                        
                        rc1 = st.columns(4)
                        for g_val in range(4):
                            with rc1[g_val]:
                                sel_m1 = (curr_m1 == g_val)
                                lbl_m1 = f"⭐ {g_val}" if sel_m1 else str(g_val)
                                if st.button(lbl_m1, key=f"adm_g1_{match_id}_{g_val}", use_container_width=True):
                                    m['gol1'] = g_val
                                    salva_dati(db)
                                    st.rerun()
                        rc2 = st.columns(4)
                        for g_val in range(4, 8):
                            with rc2[g_val - 4]:
                                sel_m1 = (curr_m1 == g_val)
                                lbl_m1 = f"⭐ {g_val}" if sel_m1 else str(g_val)
                                if st.button(lbl_m1, key=f"adm_g1_{match_id}_{g_val}", use_container_width=True):
                                    m['gol1'] = g_val
                                    salva_dati(db)
                                    st.rerun()

                        st.markdown("<div style='margin: 8px 0;'></div>", unsafe_allow_html=True)
                        st.markdown(f"**🥅 {m['p2']} / ⚽ {m['a2']} (Gol Coppia 2)**")
                        curr_m2 = int(m.get('gol2', 0))
                        
                        rc3 = st.columns(4)
                        for g_val in range(4):
                            with rc3[g_val]:
                                sel_m2 = (curr_m2 == g_val)
                                lbl_m2 = f"⭐ {g_val}" if sel_m2 else str(g_val)
                                if st.button(lbl_m2, key=f"adm_g2_{match_id}_{g_val}", use_container_width=True):
                                    m['gol2'] = g_val
                                    salva_dati(db)
                                    st.rerun()
                        rc4 = st.columns(4)
                        for g_val in range(4, 8):
                            with rc4[g_val - 4]:
                                sel_m2 = (curr_m2 == g_val)
                                lbl_m2 = f"⭐ {g_val}" if sel_m2 else str(g_val)
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
                <h1 style="color: #00f2fe; font-size: 2.2rem; font-weight: 800; text-shadow: 0 0 20px rgba(0,242,254,0.6);">🏆 TORNEO CONCLUSO! 🏆</h1>
            </div>
        """)

        podio_html = f"""
        <div class="podium-container">
            <div class="podium-step podium-2">
                <div style="font-size: 1rem; color: #38bdf8;">🥈 2° Posto</div>
                <div style="font-size: 0.9rem; margin-top: 6px; font-weight: 600; color: #f8fafc;">🥅 {p2_1}<br>⚽ {a2_1}</div>
            </div>
            <div class="podium-step podium-1">
                <div class="trophy-icon">🏆</div>
                <div style="font-size: 1.2rem; font-weight: 800; color: #fbbf24;">1° Posto</div>
                <div style="font-size: 0.95rem; margin-top: 4px; font-weight: 700; color: #f8fafc;">🥅 {p1_1}<br>⚽ {a1_1}</div>
            </div>
            <div class="podium-step podium-3">
                <div style="font-size: 1rem; color: #22c55e;">🥉 3° Posto</div>
                <div style="font-size: 0.9rem; margin-top: 6px; font-weight: 600; color: #f8fafc;">🥅 {p3_1}<br>⚽ {a3_1}</div>
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
                        box_bg = "linear-gradient(135deg, #450a0a, #7f1d1d)"
                        border_color = "#ef4444"
                        text_content = f"<div style='color: #fbbf24; font-size: 1.1rem; font-weight: 700; text-shadow: 0 0 8px rgba(251,191,36,0.4); margin: 6px 0;'>Risultato: {m['gol1']} - {m['gol2']}</div>"
                        label_stato = f"Biliardino {tavolo_num} (Giocata ✅)"
                    else:
                        box_bg = "linear-gradient(135deg, #022c22, #064e3b)"
                        border_color = "#22c55e"
                        text_content = "<div style='color: #fbbf24; font-size: 1.1rem; font-weight: 800; text-shadow: 0 0 8px rgba(251,191,36,0.5); margin: 6px 0;'>VS</div>"
                        label_stato = f"Biliardino {tavolo_num}"

                    st.html(f"""
                        <div style="background: {box_bg}; border: 1px solid {border_color}; border-radius: 12px; padding: 14px; margin-bottom: 10px; color: white; text-align: center; box-shadow: 0 0 12px rgba(0,242,254,0.15);">
                            <div style="font-weight: 700; margin-bottom: 6px; font-size: 0.95rem; text-transform: uppercase; color: #00f2fe;">{label_stato}</div>
                            <div style="font-size: 1rem; font-weight: 600; color: #f8fafc;">
                                🥅 {m['p1']} / ⚽ {m['a1']}
                            </div>
                            {text_content}
                            <div style="font-size: 1rem; font-weight: 600; color: #f8fafc;">
                                🥅 {m['p2']} / ⚽ {m['a2']}
                            </div>
                        </div>
                    """)

                    if is_admin:
                        with st.expander(f"⚙️ Modifica Risultato Biliardino {tavolo_num} (Admin)", expanded=False):
                            st.markdown(f"**🥅 {m['p1']} / ⚽ {m['a1']} (Gol Coppia 1)**")
                            curr_ef1 = int(m.get('gol1', 0))
                            
                            rc_ef1 = st.columns(4)
                            for g_val in range(4):
                                with rc_ef1[g_val]:
                                    sel_ef1 = (curr_ef1 == g_val)
                                    lbl_ef1 = f"⭐ {g_val}" if sel_ef1 else str(g_val)
                                    if st.button(lbl_ef1, key=f"ef_adm_g1_{match_id}_{g_val}", use_container_width=True):
                                        m['gol1'] = g_val
                                        salva_dati(db)
                                        st.rerun()
                            rc_ef2 = st.columns(4)
                            for g_val in range(4, 8):
                                with rc_ef2[g_val - 4]:
                                    sel_ef1 = (curr_ef1 == g_val)
                                    lbl_ef1 = f"⭐ {g_val}" if sel_ef1 else str(g_val)
                                    if st.button(lbl_ef1, key=f"ef_adm_g1_{match_id}_{g_val}", use_container_width=True):
                                        m['gol1'] = g_val
                                        salva_dati(db)
                                        st.rerun()

                            st.markdown("<div style='margin: 8px 0;'></div>", unsafe_allow_html=True)
                            st.markdown(f"**🥅 {m['p2']} / ⚽ {m['a2']} (Gol Coppia 2)**")
                            curr_ef2 = int(m.get('gol2', 0))
                            
                            rc_ef3 = st.columns(4)
                            for g_val in range(4):
                                with rc_ef3[g_val]:
                                    sel_ef2 = (curr_ef2 == g_val)
                                    lbl_ef2 = f"⭐ {g_val}" if sel_ef2 else str(g_val)
                                    if st.button(lbl_ef2, key=f"ef_adm_g2_{match_id}_{g_val}", use_container_width=True):
                                        m['gol2'] = g_val
                                        salva_dati(db)
                                        st.rerun()
                            rc_ef4 = st.columns(4)
                            for g_val in range(4, 8):
                                with rc_ef4[g_val - 4]:
                                    sel_ef2 = (curr_ef2 == g_val)
                                    lbl_ef2 = f"⭐ {g_val}" if sel_ef2 else str(g_val)
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
