import streamlit as st
import pandas as pd
import json
import os
import re
import random
from streamlit_autorefresh import st_autorefresh
from base64 import b64encode
from fpdf import FPDF

st_autorefresh(interval=5000, debounce=False, key="auto_refresh_torneo")

st.set_page_config(page_title="Torneo Biliardino 'Giallo' Live", layout="wide")

st.markdown("""
    <style>
        .block-container {
            padding-top: 0.5rem;
            padding-bottom: 0.5rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        h1 { margin-bottom: 0px; font-size: 1.6rem; }
        h3 { margin-top: 0rem; margin-bottom: 0rem; font-size: 1.2rem; }
        h4 { margin-top: 0rem; margin-bottom: 0rem; font-size: 1.0rem; }
        .stMarkdown { margin-bottom: 0px !important; }
        hr { margin: 0.4rem 0px !important; }
        
        .ranking-box {
            border: 2px solid #90caf9;
            border-radius: 8px;
            padding: 6px;
            background-color: #ffffff;
            margin-bottom: 4px;
            margin-top: 2px;
        }
        
        .ranking-box table {
            width: 100% !important;
            table-layout: fixed !important;
            margin: 0 auto;
        }
        .ranking-box th, .ranking-box td {
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            padding: 3px 2px !important;
            font-size: 0.85rem;
        }
        .ranking-box th:nth-child(1), .ranking-box td:nth-child(1) { width: 10% !important; text-align: center !important; }
        .ranking-box th:nth-child(2), .ranking-box td:nth-child(2) { width: 42% !important; text-align: left !important; }
        .ranking-box th:nth-child(3), .ranking-box td:nth-child(3) { width: 16% !important; text-align: center !important; }
        .ranking-box th:nth-child(4), .ranking-box td:nth-child(4) { width: 16% !important; text-align: center !important; }
        .ranking-box th:nth-child(5), .ranking-box td:nth-child(5) { width: 16% !important; text-align: center !important; }

        .container-yellow {
            border: 3px solid #f57f17;
            border-radius: 8px;
            padding: 10px;
            background-color: #ffe082;
            margin-bottom: 10px;
        }
        .container-green {
            border: 2px solid #81c784;
            border-radius: 8px;
            padding: 10px;
            background-color: #e8f5e9;
            margin-bottom: 10px;
        }
        
        .match-card-box {
            border: 3px solid #ffa726;
            border-radius: 10px;
            padding: 12px;
            background-color: #fffdf5;
            margin-bottom: 15px;
            box-shadow: 0px 3px 6px rgba(0,0,0,0.08);
        }

        .sub-card-lightgreen {
            padding: 8px;
            background-color: #f1f8e9;
            border: 1px solid #c8e6c9;
            border-radius: 6px;
            margin-bottom: 6px;
        }

        @keyframes riseUp {
            0% { transform: translateY(50px); opacity: 0; }
            100% { transform: translateY(0); opacity: 1; }
        }
        @keyframes floatTrophy {
            0% { transform: translateY(0px); }
            50% { transform: translateY(-8px); }
            100% { transform: translateY(0px); }
        }
        .podium-container {
            display: flex;
            justify-content: center;
            align-items: flex-end;
            gap: 12px;
            margin: 20px 0;
            animation: riseUp 0.8s ease-out;
        }
        .podium-step {
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            border-radius: 8px 8px 0 0;
            padding: 10px;
            font-weight: bold;
            box-shadow: 0px 4px 10px rgba(0,0,0,0.15);
        }
        .podium-1 {
            background: linear-gradient(135deg, #ffd700, #ffaa00);
            color: #3e2723;
            width: 35%;
            height: 170px;
            border: 2px solid #ff8f00;
        }
        .podium-2 {
            background: linear-gradient(135deg, #e0e0e0, #b0bec5);
            color: #263238;
            width: 30%;
            height: 135px;
            border: 2px solid #90a4ae;
        }
        .podium-3 {
            background: linear-gradient(135deg, #ffccbc, #d7ccc8);
            color: #4e342e;
            width: 30%;
            height: 110px;
            border: 2px solid #bcaaa4;
        }
        .trophy-icon {
            font-size: 2.2rem;
            animation: floatTrophy 2s ease-in-out infinite;
            margin-bottom: 4px;
        }
    </style>
""", unsafe_allow_html=True)

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
            riga = f"  - Tavolo {tavolo_num}: [Portiere: {m['p1']} | Attaccante: {m['a1']}] VS [Portiere: {m['p2']} | Attaccante: {m['a2']}] -> {risultato}"
            riga_pulita = riga.encode('latin-1', 'ignore').decode('latin-1')
            pdf.cell(0, 6, riga_pulita, 0, 1, "L")
        pdf.ln(3)
        
    if db.get("fasi_finali"):
        pdf.ln(5)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Fasi Finali", 0, 1, "C")
        for f_turno in db["fasi_finali"]:
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 8, f"{f_turno['nome']}", 0, 1, "L")
            pdf.set_font("Arial", "", 10)
            for idx, m in enumerate(f_turno["partite"]):
                tavolo_num = (idx % num_tavoli) + 1
                risultato = f"{m['gol1']} - {m['gol2']}" if m.get("giocata", False) else "Da giocare"
                riga = f"  - Tavolo {tavolo_num}: [P: {m['p1']} | A: {m['a1']}] VS [P: {m['p2']} | A: {m['a2']}] -> {risultato}"
                riga_pulita = riga.encode('latin-1', 'ignore').decode('latin-1')
                pdf.cell(0, 6, riga_pulita, 0, 1, "L")
            pdf.ln(3)
            
    return bytes(pdf.output())

# --- BARRA LATERALE ---
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

if is_admin:
    st.sidebar.markdown("---")
    st.sidebar.subheader("🗑️ Reset Totale")
    if st.sidebar.button("⚠️ Azzera e Ricomincia", use_container_width=True):
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.sidebar.success("Torneo azzerato con successo!")
        st.rerun()

if is_admin and db["stato"] != "setup":
    st.sidebar.markdown("---")
    st.sidebar.subheader("🛠️ Correzione Parametri")
    with st.sidebar.expander("Modifica Tavoli / Turni"):
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

# --- LINK SPETTATORE & QR CODE IN SIDEBAR ---
st.sidebar.markdown("---")
st.sidebar.subheader("📱 Condividi Torneo")
link_torneo = st.sidebar.text_input("Link Spettatore (Copia qui):", value="https://2quznathuywvfxcskgfjhk.streamlit.app")

if link_torneo and link_torneo != "https://":
    import urllib.parse
    encoded_url = urllib.parse.quote(link_torneo, safe='')
    qr_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=180x180&data={encoded_url}"
    st.sidebar.image(qr_api_url, caption="Inquadra per aprire il torneo", use_container_width=True)

st.sidebar.info("💡 **Suggerimento:** Copia il link sopra per condividerlo o fallo scansionare ai giocatori.")

# --- INTERFACCIA PRINCIPALE ---
logo_html = ""
if os.path.exists(LOGO_FILE):
    with open(LOGO_FILE, "rb") as f:
        logo_b64 = b64encode(f.read()).decode("utf-8")
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="max-width: 220px; width: 100%; height: auto; margin-bottom: 5px;" /><br>'

st.html(
    f"""
    <div style="text-align: center; margin-bottom: 5px;">
        {logo_html}
        <div style="padding: 6px; background-color: #e3f2fd; border: 2px solid #90caf9; border-radius: 8px;">
            <h2 style="margin: 0; color: #1565c0; font-size: 1.3rem;">🏆 Torneo Biliardino 'Giallo' Live</h2>
            <p style="margin: 2px 0 0 0; color: #0d47a1; font-weight: bold; font-size: 12px;">Regolamento Uisp 3 tocchi</p>
        </div>
    </div>
    """
)

st.html(
    """
    <div style="padding: 3px; background-color: #f0f2f6; border-radius: 6px; text-align: center; margin-bottom: 5px;">
        🔄 <a href="javascript:window.location.reload(true)" style="text-decoration: none; color: #262730; font-weight: bold; font-size: 11px;">
            Ricarica la pagina del browser per aggiornare l'andamento in tempo reale
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
                st.error("Inserisci almeno 8 portieri (🥅) e 8 attaccanti (⚽) per poter fare i quarti di finale.")
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
                    db["turni_partite"].append({"turno": t, "chiuso": True, "partite": partite_turno})

                salva_dati(db)
                st.success("Calendario generato!")
                st.rerun()

# 2. GIRONI
if db["stato"] == "gironi":
    ricalcola_classifiche()
    num_tavoli = db.get("num_tavoli", 3)

    # --- AGGIORNAMENTO STATO TURNO IN TEMPO REALE ---
    for turno_obj in db["turni_partite"]:
        tutte_giocate = all(m.get("giocata", False) for m in turno_obj["partite"])
        almeno_una_iniziata = any(m.get("in_corso", False) or m.get("giocata", False) for m in turno_obj["partite"])
        
        if tutte_giocate:
            turno_obj["chiuso"] = True
        elif almeno_una_iniziata:
            turno_obj["chiuso"] = False

    salva_dati(db)

    tutte_attive = []
    for turno_obj in db["turni_partite"]:
        for m in turno_obj["partite"]:
            if not m["giocata"]:
                tutte_attive.append({"turno": turno_obj["turno"], "m": m})

    partite_in_corso = [item for item in tutte_attive if item["m"].get("in_corso", False)]
    rimanenti = [item for item in tutte_attive if not item["m"].get("in_corso", False)]

    if not partite_in_corso and rimanenti:
        partite_in_corso = rimanenti[:num_tavoli]
        rimanenti = rimanenti[num_tavoli:]

    num_da_mostrare = len(partite_in_corso)
    partite_in_coda = rimanenti[:num_da_mostrare]

    # --- ASSEGNAZIONE PROGRESSIVA DEI BILIARDINI DA 1 A num_tavoli ---
    partite_in_corso_con_tavolo = []
    for idx, item in enumerate(partite_in_corso):
        tavolo_num = (idx % num_tavoli) + 1
        partite_in_corso_con_tavolo.append({"tavolo": tavolo_num, "turno": item["turno"], "m": item["m"]})

    partite_in_corso_con_tavolo = sorted(partite_in_corso_con_tavolo, key=lambda x: x["tavolo"])

    if partite_in_corso_con_tavolo:
        st.html('<div class="container-yellow"><h4 style="margin: 0 0 6px 0; color: #b71c1c;">🔥 PARTITE IN CORSO (Sui biliardini):</h4>')
        for item in partite_in_corso_con_tavolo:
            m = item["m"]
            match_id = m['id']
            squadra1_nome = f"{m['p1']} & {m['a1']}"
            squadra2_nome = f"{m['p2']} & {m['a2']}"
            
            st.html(f"""
                <div class="match-card-box">
                    <div style="font-weight: bold; color: #b71c1c; margin-bottom: 6px; font-size: 1.05rem;">
                        🏟️ Biliardino {item['tavolo']} (Turno {item['turno']})
                    </div>
                    <div style="text-align: center; font-size: 1.15rem; font-weight: bold; color: #1a237e; background-color: #e8eaf6; padding: 8px; border-radius: 6px; width: 100%; margin-bottom: 10px;">
                        {squadra1_nome} <span style="color: #d32f2f; font-size: 0.95rem; font-weight: normal;">vs</span> {squadra2_nome}
                    </div>
            """)
            
            # BLOCCO: SE LA PARTITA NON È GIOCATA SI POSSONO INSERIRE I GOL, ALTRIMENTI SPARISCONO I COMANDI
            if not m.get("giocata", False):
                st.html(f"""
                    <div style="text-align: center; width: 100%; font-weight: bold; font-size: 1.05rem; color: #2c3e50; background-color: #fcf8e3; padding: 6px; border-radius: 5px; margin-top: 8px; margin-bottom: 4px;">
                        ⚽ Gol: {squadra1_nome}
                    </div>
                """)
                g1_input = st.radio("Gol S1", list(range(8)), index=min(int(m.get('gol1', 0)), 7), horizontal=True, key=f"live_g1_{match_id}", label_visibility="collapsed")
                
                st.html(f"""
                    <div style="text-align: center; width: 100%; font-weight: bold; font-size: 1.05rem; color: #2c3e50; background-color: #fcf8e3; padding: 6px; border-radius: 5px; margin-top: 12px; margin-bottom: 4px;">
                        ⚽ Gol: {squadra2_nome}
                    </div>
                """)
                g2_input = st.radio("Gol S2", list(range(8)), index=min(int(m.get('gol2', 0)), 7), horizontal=True, key=f"live_g2_{match_id}", label_visibility="collapsed")
                
                st.html("<div style='margin-top: 10px;'></div>")
                if st.button(f"💾 Registra e Libera Tavolo {item['tavolo']}", key=f"live_save_{match_id}", use_container_width=True):
                    m['gol1'] = g1_input
                    m['gol2'] = g2_input
                    m['giocata'] = True
                    m['in_corso'] = False
                    
                    for t_obj in db["turni_partite"]:
                        if t_obj["turno"] == item["turno"]:
                            if all(pt.get("giocata", False) for pt in t_obj["partite"]):
                                t_obj["chiuso"] = True

                    ricalcola_classifiche()
                    salva_dati(db)
                    st.success(f"Risultato salvato! Il biliardino {item['tavolo']} è ora libero.")
                    st.rerun()
            else:
                st.info("✅ Partita già conclusa e salvata. Risultato blindato.")

            st.html('</div>')
        st.html('</div>')

    if partite_in_coda:
        html_coda = '<div class="container-green"><h4 style="margin: 0 0 4px 0; color: #2e7d32;">📢 PROSSIMI IN CODA (Preparatevi):</h4>'
        for item in partite_in_coda:
            m = item["m"]
            html_coda += f"""
                <div class="sub-card-lightgreen">
                    <b>👉 In Coda (Turno {item['turno']})</b><br>
                    🥅 {m['p1']} &nbsp;&nbsp;|&nbsp;&nbsp; ⚽ {m['a1']}<br>
                    🥅 {m['p2']} &nbsp;&nbsp;|&nbsp;&nbsp; ⚽ {m['a2']}
                </div>
            """
        html_coda += '</div>'
        st.html(html_coda)

    st.markdown("---")

    st.html("<h3 style='text-align: center; margin: 0 0 4px 0;'>🏆 Classifiche in Tempo Reale</h3>")
    col_c1, col_c2 = st.columns(2)

    def colora_posizioni(row):
        if row.name < 8:
            return ['background-color: #e6f2e6' for _ in row]
        else:
            return ['background-color: #fde8e8' for _ in row]

    with col_c1:
        st.html("<h4 style='text-align: center; margin: 0 0 2px 0;'>🥅 Portieri</h4>")
        sorted_p = sorted(db["punti_portieri"].items(), key=lambda x: (x[1], db["dr_portieri"].get(x[0], 0)), reverse=True)
        data_p = []
        for idx, (p, pt) in enumerate(sorted_p):
            dr = db["dr_portieri"].get(p, 0)
            dr_str = f"+{dr}" if dr > 0 else str(dr)
            gioc, tot = calcola_partite_giocate('portiere', p)
            data_p.append({"Pos": f"{idx+1}°", "Portiere": f"🥅 {p}", "Punti": pt, "DR": dr_str, "Giocate": f"{gioc}/{tot}"})
        df_p = pd.DataFrame(data_p)
        
        html_table_p = df_p.style.apply(colora_posizioni, axis=1).hide(axis="index").to_html()
        st.html(f"""
            <div class="ranking-box">
                {html_table_p}
            </div>
        """)

    with col_c2:
        st.html("<h4 style='text-align: center; margin: 0 0 2px 0;'>⚽ Attaccanti</h4>")
        sorted_a = sorted(db["punti_attaccanti"].items(), key=lambda x: (x[1], db["dr_attaccanti"].get(x[0], 0)), reverse=True)
        data_a = []
        for idx, (a, pt) in enumerate(sorted_a):
            dr = db["dr_attaccanti"].get(a, 0)
            dr_str = f"+{dr}" if dr > 0 else str(dr)
            gioc, tot = calcola_partite_giocate('attaccante', a)
            data_a.append({"Pos": f"{idx+1}°", "Attaccante": f"⚽ {a}", "Punti": pt, "DR": dr_str, "Giocate": f"{gioc}/{tot}"})
        df_a = pd.DataFrame(data_a)
        
        html_table_a = df_a.style.apply(colora_posizioni, axis=1).hide(axis="index").to_html()
        st.html(f"""
            <div class="ranking-box">
                {html_table_a}
            </div>
        """)

    st.markdown("---")

    st.markdown("### 📅 Lista Completa Turni")

    for turno_obj in db["turni_partite"]:
        turno_num = turno_obj['turno']
        is_chiuso = turno_obj.get("chiuso", True)
        
        tutte_giocate = all(m.get("giocata", False) for m in turno_obj["partite"])
        almeno_una_iniziata = any(m.get("in_corso", False) or m.get("giocata", False) for m in turno_obj["partite"])

        if tutte_giocate:
            header_bg = "#b0bec5"
            header_border = "#78909c"
            header_text = f"TURNO {turno_num} (Completato ✅)"
        elif almeno_una_iniziata:
            header_bg = "#ffd700"
            header_border = "#ffb300"
            header_text = f"TURNO {turno_num} (In corso 🔥)"
        else:
            header_bg = "#e0f7fa"
            header_border = "#b2ebf2"
            header_text = f"TURNO {turno_num} (Da iniziare ⏳)"

        st.html(
            f"""
            <div style="padding: 5px; background-color: {header_bg}; border: 2px solid {header_border}; border-radius: 6px; text-align: center; margin-top: 6px; margin-bottom: 6px;">
                <h3 style="margin: 0; color: #3e2723; font-size: 1.1rem;">{header_text}</h3>
            </div>
            """
        )

        if is_chiuso and is_admin:
            if st.button(f"🔓 Riapri Turno {turno_num} per modifiche", key=f"riapri_t_{turno_num}", use_container_width=True):
                turno_obj["chiuso"] = False
                salva_dati(db)
                st.success(f"Turno {turno_num} riaperto!")
                st.rerun()

        with st.expander(f"👁️ Visualizza partite Turno {turno_num}", expanded=not is_chiuso):
            for idx, m in enumerate(turno_obj["partite"]):
                tavolo_num = (idx % num_tavoli) + 1
                match_id = m['id']
                squadra1_nome = f"{m['p1']} & {m['a1']}"
                squadra2_nome = f"{m['p2']} & {m['a2']}"
                
                edit_flag_key = f"edit_mode_{match_id}"
                if edit_flag_key not in st.session_state:
                    st.session_state[edit_flag_key] = False

                if m["giocata"]:
                    bg_color = "#ffebee"
                    stato_testo = f"🛑 <b>{m['gol1']} - {m['gol2']}</b> (✅ Giocata)"
                elif m.get("in_corso", False):
                    bg_color = "#d4edda"
                    stato_testo = "🔥 <b>PARTITA IN CORSO</b>"
                else:
                    bg_color = "#f1f8e9"
                    stato_testo = "⏳ <b>Da giocare</b>"

                st.html(f"""
                    <div style="padding: 6px; background-color: {bg_color}; border: 1px solid #c8e6c9; border-radius: 6px; margin-bottom: 6px;">
                        <b>📍 Tavolo {tavolo_num}</b><br>
                        🥅 {m['p1']} &nbsp;&nbsp;|&nbsp;&nbsp; ⚽ {m['a1']}<br>
                        🥅 {m['p2']} &nbsp;&nbsp;|&nbsp;&nbsp; ⚽ {m['a2']}<br>
                        <div style="text-align: center; margin-top: 2px; font-size: 12px;">
                            {stato_testo}
                        </div>
                    </div>
                """)

                col_l1, col_l2 = st.columns(2)
                with col_l1:
                    if is_admin and not m["giocata"]:
                        if m.get("in_corso", False):
                            if st.button("⏹️ Ferma", key=f"list_stop_{match_id}", use_container_width=True):
                                m["in_corso"] = False
                                salva_dati(db)
                                st.rerun()
                        else:
                            if st.button("▶️ Avvia", key=f"list_start_{match_id}", use_container_width=True):
                                m["in_corso"] = True
                                turno_obj["chiuso"] = False
                                salva_dati(db)
                                st.rerun()
                with col_l2:
                    if is_admin:
                        with st.expander("⚙️ Gestisci Risultato (Admin)", expanded=st.session_state[edit_flag_key]):
                            st.html(f"""
                                <div style="text-align: center; width: 100%; font-weight: bold; font-size: 1.0rem; color: #2c3e50; background-color: #fcf8e3; padding: 5px; border-radius: 4px; margin-top: 4px; margin-bottom: 2px;">
                                    ⚽ Gol: {squadra1_nome}
                                </div>
                            """)
                            rg1 = st.radio("Gol S1", list(range(8)), index=min(int(m.get('gol1', 0)), 7), horizontal=True, key=f"list_rg1_{match_id}", label_visibility="collapsed")
                            
                            st.html(f"""
                                <div style="text-align: center; width: 100%; font-weight: bold; font-size: 1.0rem; color: #2c3e50; background-color: #fcf8e3; padding: 5px; border-radius: 4px; margin-top: 8px; margin-bottom: 2px;">
                                    ⚽ Gol: {squadra2_nome}
                                </div>
                            """)
                            rg2 = st.radio("Gol S2", list(range(8)), index=min(int(m.get('gol2', 0)), 7), horizontal=True, key=f"list_rg2_{match_id}", label_visibility="collapsed")
                            
                            st.html("<div style='margin-top: 8px;'></div>")
                            if st.button("💾 Salva Risultato (Admin)", key=f"list_save_{match_id}", use_container_width=True):
                                m['gol1'] = rg1
                                m['gol2'] = rg2
                                m['giocata'] = True
                                m['in_corso'] = False
                                
                                if all(pt.get("giocata", False) for pt in turno_obj["partite"]):
                                    turno_obj["chiuso"] = True

                                ricalcola_classifiche()
                                salva_dati(db)
                                st.session_state[edit_flag_key] = False
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
            <div style="text-align: center; margin-top: 10px; margin-bottom: 15px;">
                <h1 style="color: #d32f2f; font-size: 2rem;">🏆 TORNEO CONCLUSO! 🏆</h1>
                <p style="font-size: 1.1rem; color: #424242; margin-top: 5px;">Ecco i vincitori ufficiali della competizione</p>
            </div>
        """)

        podio_html = f"""
        <div class="podium-container">
            <!-- 2° POSTO -->
            <div class="podium-step podium-2">
                <div style="font-size: 1.2rem;">🥈 2° Posto</div>
                <div style="font-size: 0.9rem; margin-top: 8px;">🥅 {p2_1}<br>⚽ {a2_1}</div>
            </div>
            <!-- 1° POSTO -->
            <div class="podium-step podium-1">
                <div class="trophy-icon">🏆</div>
                <div style="font-size: 1.4rem; font-weight: bold;">1° Posto</div>
                <div style="font-size: 1.0rem; margin-top: 4px;">🥅 {p1_1}<br>⚽ {a1_1}</div>
            </div>
            <!-- 3° POSTO -->
            <div class="podium-step podium-3">
                <div style="font-size: 1.2rem;">🥉 3° Posto</div>
                <div style="font-size: 0.9rem; margin-top: 8px;">🥅 {p3_1}<br>⚽ {a3_1}</div>
            </div>
        </div>
        """
        st.html(podio_html)
        
        st.markdown("---")
        
        col_f1, col_f2, col_f3 = st.columns([1, 2, 1])
        with col_f2:
            pdf_data = genera_pdf_calendario()
            st.download_button(
                label="📥 Scarica Riepilogo Finale in PDF",
                data=pdf_data,
                file_name="riepilogo_finale_torneo.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            if is_admin:
                if st.button("⬅️ Torna alla gestione eliminatorie", use_container_width=True):
                    fin_partite[0]["giocata"] = False
                    salva_dati(db)
                    st.rerun()
                    
    else:
        st.subheader("🏆 Fase a Eliminazione Diretta")
        
        for f_idx, f_turno in enumerate(fasi):
            st.markdown(f"### 🔥 {f_turno['nome']}")
            
            tutti_giocati = True
            vincitori_turno = []
            perdenti_turno = []
            
            for idx, m in enumerate(f_turno["partite"]):
                tavolo_num = (idx % num_tavoli) + 1
                match_id = m['id']
                squadra1_nome = f"{m['p1']} & {m['a1']}"
                squadra2_nome = f"{m['p2']} & {m['a2']}"
                
                edit_flag_key = f"ef_edit_mode_{match_id}"
                if edit_flag_key not in st.session_state:
                    st.session_state[edit_flag_key] = False

                if m.get("giocata", False):
                    if m["gol1"] >= m["gol2"]:
                        vincitori_turno.append({"p": m["p1"], "a": m["a1"]})
                        perdenti_turno.append({"p": m["p2"], "a": m["a2"]})
                    else:
                        vincitori_turno.append({"p": m["p2"], "a": m["a2"]})
                        perdenti_turno.append({"p": m["p1"], "a": m["a1"]})
                else:
                    tutti_giocati = False

                if m["giocata"]:
                    bg_color = "#ffebee"
                    stato_testo = f"🛑 <b>{m['gol1']} - {m['gol2']}</b> (✅ Giocata)"
                elif m.get("in_corso", False):
                    bg_color = "#d4edda"
                    stato_testo = "🔥 <b>PARTITA IN CORSO</b>"
                else:
                    bg_color = "#f1f8e9"
                    stato_testo = "⏳ <b>Da giocare</b>"

                st.html(f"""
                    <div style="padding: 6px; background-color: {bg_color}; border: 1px solid #c8e6c9; border-radius: 6px; margin-bottom: 6px;">
                        <b>📍 Biliardino {tavolo_num}</b><br>
                        🥅 <b>{m['p1']}</b> &nbsp;&nbsp;|&nbsp;&nbsp; ⚽ <b>{m['a1']}</b><br>
                        🥅 <b>{m['p2']}</b> &nbsp;&nbsp;|&nbsp;&nbsp; ⚽ <b>{m['a2']}</b><br>
                        <div style="text-align: center; margin-top: 2px; font-size: 12px;">
                            {stato_testo}
                        </div>
                    </div>
                """)

                col_a1, col_a2 = st.columns(2)
                with col_a1:
                    if is_admin and not m.get("in_corso", False) and not m["giocata"]:
                        if st.button("▶️ Avvia", key=f"ef_btn_{match_id}", use_container_width=True):
                            m["in_corso"] = True
                            salva_dati(db)
                            st.rerun()
                with col_a2:
                    if is_admin and m.get("in_corso", False):
                        if st.button("⏹️ Ferma", key=f"ef_stop_{match_id}", use_container_width=True):
                            m["in_corso"] = False
                            salva_dati(db)
                            st.rerun()
                
                if is_admin:
                    with st.expander("⚙️ Gestisci Risultato (Admin)", expanded=st.session_state[edit_flag_key]):
                        st.html(f"""
                            <div style="text-align: center; width: 100%; font-weight: bold; font-size: 1.0rem; color: #2c3e50; background-color: #fcf8e3; padding: 5px; border-radius: 4px; margin-top: 4px; margin-bottom: 2px;">
                                ⚽ Gol: {squadra1_nome}
                            </div>
                        """)
                        rg1 = st.radio("Gol S1", list(range(8)), index=min(int(m.get('gol1', 0)), 7), horizontal=True, key=f"ef_rg1_{match_id}", label_visibility="collapsed")
                        
                        st.html(f"""
                            <div style="text-align: center; width: 100%; font-weight: bold; font-size: 1.0rem; color: #2c3e50; background-color: #fcf8e3; padding: 5px; border-radius: 4px; margin-top: 8px; margin-bottom: 2px;">
                                ⚽ Gol: {squadra2_nome}
                            </div>
                        """)
                        rg2 = st.radio("Gol S2", list(range(8)), index=min(int(m.get('gol2', 0)), 7), horizontal=True, key=f"ef_rg2_{match_id}", label_visibility="collapsed")
                        
                        st.html("<div style='margin-top: 8px;'></div>")
                        if st.button("💾 Salva Risultato (Admin)", key=f"ef_save_{match_id}", use_container_width=True):
                            m['gol1'] = rg1
                            m['gol2'] = rg2
                            m['giocata'] = True
                            m['in_corso'] = False
                            salva_dati(db)
                            st.session_state[edit_flag_key] = False
                            st.rerun()

                st.markdown("---")

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
                            {"id": "ef_t3_m2", "p1": sf1_p["p"], "a1": sf2_p["a"], "p2": sf2_p["p"], "a2": sf1_p["a"], "giocata": False, "in_corso": False, "gol1": 0, "gol2": 0}
                        ]
                        db["fasi_finali"].append({"turno": 3, "nome": "Finali (1°-2° e 3°-4° Posto)", "partite": finali_partite})
                        salva_dati(db)
                        st.rerun()

        if is_admin:
            if st.button("⬅️ Indietro ai Gironi", use_container_width=True):
                db["stato"] = "gironi"
                salva_dati(db)
                st.rerun()
