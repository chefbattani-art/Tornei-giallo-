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

# --- CSS PERSONALIZZATO PER LE CARD ORIZZONTALI ---
st.markdown("""
    <style>
        .match-row-green {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background-color: #e8f5e9;
            border: 1px solid #c8e6c9;
            border-radius: 8px;
            padding: 10px 15px;
            margin-bottom: 8px;
            font-size: 0.95rem;
        }
        .match-row-yellow {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background-color: #fffde7;
            border: 1px solid #ffe082;
            border-radius: 8px;
            padding: 10px 15px;
            margin-bottom: 8px;
            font-size: 0.95rem;
        }
        .match-row-white {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 10px 15px;
            margin-bottom: 8px;
            font-size: 0.95rem;
        }
        .team-left {
            text-align: left;
            width: 38%;
            font-weight: 500;
        }
        .team-right {
            text-align: right;
            width: 38%;
            font-weight: 500;
        }
        .match-center {
            text-align: center;
            width: 24%;
            font-weight: bold;
        }
        .ranking-box {
            border: 1px solid #90caf9;
            border-radius: 8px;
            padding: 10px;
            background-color: #ffffff;
            margin-bottom: 10px;
        }
        .container-yellow {
            border: 2px solid #f57f17;
            border-radius: 8px;
            padding: 10px;
            background-color: #ffe082;
            margin-bottom: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# Stili podio e animazioni
st.markdown("""
    <style>
        @keyframes riseUp {
            0% { transform: translateY(30px); opacity: 0; }
            100% { transform: translateY(0); opacity: 1; }
        }
        @keyframes floatTrophy {
            0% { transform: translateY(0px); }
            50% { transform: translateY(-5px); }
            100% { transform: translateY(0px); }
        }
        .podium-container {
            display: flex;
            justify-content: center;
            align-items: flex-end;
            gap: 8px;
            margin: 10px 0;
            animation: riseUp 0.8s ease-out;
        }
        .podium-step {
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            border-radius: 6px 6px 0 0;
            padding: 6px;
            font-weight: bold;
            box-shadow: 0px 2px 6px rgba(0,0,0,0.15);
        }
        .podium-1 {
            background: linear-gradient(135deg, #ffd700, #ffaa00);
            color: #3e2723;
            width: 35%;
            height: 140px;
            border: 2px solid #ff8f00;
        }
        .podium-2 {
            background: linear-gradient(135deg, #e0e0e0, #b0bec5);
            color: #263238;
            width: 30%;
            height: 110px;
            border: 2px solid #90a4ae;
        }
        .podium-3 {
            background: linear-gradient(135deg, #ffccbc, #d7ccc8);
            color: #4e342e;
            width: 30%;
            height: 90px;
            border: 2px solid #bcaaa4;
        }
        .trophy-icon {
            font-size: 1.8rem;
            animation: floatTrophy 2s ease-in-out infinite;
            margin-bottom: 2px;
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

# --- INTERFACCIA PRINCIPALE ---
logo_html = ""
if os.path.exists(LOGO_FILE):
    with open(LOGO_FILE, "rb") as f:
        logo_b64 = b64encode(f.read()).decode("utf-8")
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="max-width: 140px; width: 100%; height: auto; margin-bottom: 2px;" /><br>'

st.html(
    f"""
    <div style="text-align: center; margin-bottom: 2px;">
        {logo_html}
        <div style="padding: 6px; background-color: #e3f2fd; border: 1px solid #90caf9; border-radius: 6px;">
            <h2 style="margin: 0; color: #1565c0; font-size: 1.2rem;">🏆 Torneo Biliardino 'Giallo' Live</h2>
            <p style="margin: 2px 0 0 0; color: #0d47a1; font-weight: bold; font-size: 11px;">Regolamento Uisp 3 tocchi</p>
        </div>
    </div>
    """
)

# SELETTORE RAPIDO GIOCATORE (PER OSPITI)
if db["stato"] != "setup" and not is_admin:
    tutti_i_giocatori = sorted(list(set(db["portieri"] + db["attaccanti"])))
    giocatore_selezionato = st.selectbox(
        "🔍 SELEZIONA IL TUO NOME PER TROVARE SUBITO LA TUA PARTITA:",
        ["-- Seleziona il tuo nome --"] + tutti_i_giocatori
    )
    st.markdown("---")
else:
    giocatore_selezionato = "-- Seleziona il tuo nome --"

st.html(
    """
    <div style="padding: 4px; background-color: #f0f2f6; border-radius: 4px; text-align: center; margin-bottom: 6px;">
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

    # SE L'UTENTE HA SELEZIONATO IL PROPRIO NOME
    if not is_admin and giocatore_selezionato != "-- Seleziona il tuo nome --":
        partite_filtrate = []
        for t_obj in db["turni_partite"]:
            for idx, m in enumerate(t_obj["partite"]):
                if m['p1'] == giocatore_selezionato or m['a1'] == giocatore_selezionato or m['p2'] == giocatore_selezionato or m['a2'] == giocatore_selezionato:
                    tavolo_num = (idx % num_tavoli) + 1
                    partite_filtrate.append({"turno": t_obj["turno"], "tavolo": tavolo_num, "m": m})

        if partite_filtrate:
            st.html('<div class="container-yellow"><h4 style="margin: 0 0 4px 0; color: #b71c1c;">🔥 LE TUE PARTITE:</h4>')
            for item in partite_filtrate:
                m = item["m"]
                if m.get("giocata", False):
                    center_txt = f"<b>{m['gol1']} - {m['gol2']}</b>"
                elif m.get("in_corso", False):
                    center_txt = f"🔥 In corso (Biliardino {item['tavolo']})"
                else:
                    center_txt = f"⏳ Biliardino {item['tavolo']}"

                st.html(f"""
                    <div style="background-color: #ffffff; border: 1px solid #ffa726; border-radius: 6px; padding: 8px; margin-bottom: 6px;">
                        <div style="font-size: 0.8rem; color: #d32f2f; font-weight: bold; margin-bottom: 2px;">Turno {item['turno']} | Biliardino {item['tavolo']}</div>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div style="width: 45%;">🥅 {m['p1']} &amp; ⚽ {m['a1']}</div>
                            <div style="width: 10%; text-align: center; font-weight: bold;">VS</div>
                            <div style="width: 45%; text-align: right;">🥅 {m['p2']} &amp; ⚽ {m['a2']}</div>
                        </div>
                        <div style="text-align: center; margin-top: 4px; font-weight: bold; color: #333;">{center_txt}</div>
                    </div>
                """)
            st.html('</div>')
        else:
            st.info(f"Nessuna partita trovata per {giocatore_selezionato}.")
        st.markdown("---")

    # CLASSIFICHE IN TEMPO REALE
    st.html("<h3 style='text-align: center; margin: 0 0 6px 0;'>🏆 Classifiche in Tempo Reale</h3>")
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
        st.html(f'<div class="ranking-box">{html_table_p}</div>')

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
        st.html(f'<div class="ranking-box">{html_table_a}</div>')

    st.markdown("---")

    # --- LISTA COMPLETA TURNI DENTRO FINESTRE ESPANDIBILI ---
    st.markdown("### 📅 Partite dei Turni")

    for turno_obj in db["turni_partite"]:
        turno_num = turno_obj['turno']
        
        tutte_giocate = all(m.get("giocata", False) for m in turno_obj["partite"])
        almeno_una_iniziata = any(m.get("in_corso", False) for m in turno_obj["partite"])

        # Determina l'etichetta e lo stato di apertura della finestra (expander)
        if tutte_giocate:
            header_text = f"Turno {turno_num} (Completato ✅)"
            espanso_default = False  # Chiuso quando completato
        elif almeno_una_iniziata:
            header_text = f"Turno {turno_num} (In corso 🔥)"
            espanso_default = True   # Aperto automaticamente quando in corso
        else:
            header_text = f"Turno {turno_num} (Chiuso ⏳)"
            espanso_default = False  # Chiuso se deve ancora iniziare

        # Finestra a tendina (expander) per il turno
        with st.expander(header_text, expanded=espanso_default):
            for idx, m in enumerate(turno_obj["partite"]):
                tavolo_num = (idx % num_tavoli) + 1
                match_id = m['id']
                
                if m["giocata"]:
                    row_class = "match-row-green"
                    center_content = f"<b>{m['gol1']} - {m['gol2']}</b>"
                elif m.get("in_corso", False):
                    row_class = "match-row-yellow"
                    center_content = f"🔥 In corso (Biliardino {tavolo_num})"
                else:
                    row_class = "match-row-white"
                    center_content = "VS"

                team1_str = f"🥅 {m['p1']} &amp; ⚽ {m['a1']}"
                team2_str = f"🥅 {m['p2']} &amp; ⚽ {m['a2']}"

                st.html(f"""
                    <div class="{row_class}">
                        <div class="team-left">{team1_str}</div>
                        <div class="match-center">{center_content}</div>
                        <div class="team-right">{team2_str}</div>
                    </div>
                """)

                # Sezione Admin per avviare/fermare o modificare il risultato
                if is_admin:
                    col_adm1, col_adm2 = st.columns(2)
                    with col_adm1:
                        if not m["giocata"]:
                            if m.get("in_corso", False):
                                if st.button(f"⏹️ Ferma Biliardino {tavolo_num}", key=f"stop_{match_id}", use_container_width=True):
                                    m["in_corso"] = False
                                    salva_dati(db)
                                    st.rerun()
                            else:
                                if st.button(f"▶️ Avvia Biliardino {tavolo_num}", key=f"start_{match_id}", use_container_width=True):
                                    m["in_corso"] = True
                                    salva_dati(db)
                                    st.rerun()
                    with col_adm2:
                        with st.expander(f"⚙️ Modifica Risultato Biliardino {tavolo_num}", expanded=False):
                            rg1 = st.radio("Gol S1", list(range(8)), index=min(int(m.get('gol1', 0)), 7), horizontal=True, key=f"rg1_{match_id}")
                            rg2 = st.radio("Gol S2", list(range(8)), index=min(int(m.get('gol2', 0)), 7), horizontal=True, key=f"rg2_{match_id}")
                            if st.button(f"💾 Salva Risultato", key=f"save_{match_id}", use_container_width=True):
                                m['gol1'] = rg1
                                m['gol2'] = rg2
                                m['giocata'] = True
                                m['in_corso'] = False
                                ricalcola_classifiche()
                                salva_dati(db)
                                st.success("Salvato!")
                                st.rerun()

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
                <h1 style="color: #d32f2f; font-size: 1.8rem;">🏆 TORNEO CONCLUSO! 🏆</h1>
            </div>
        """)

        podio_html = f"""
        <div class="podium-container">
            <div class="podium-step podium-2">
                <div style="font-size: 1.0rem;">🥈 2° Posto</div>
                <div style="font-size: 0.8rem; margin-top: 4px;">🥅 {p2_1}<br>⚽ {a2_1}</div>
            </div>
            <div class="podium-step podium-1">
                <div class="trophy-icon">🏆</div>
                <div style="font-size: 1.2rem; font-weight: bold;">1° Posto</div>
                <div style="font-size: 0.85rem; margin-top: 2px;">🥅 {p1_1}<br>⚽ {a1_1}</div>
            </div>
            <div class="podium-step podium-3">
                <div style="font-size: 1.0rem;">🥉 3° Posto</div>
                <div style="font-size: 0.8rem; margin-top: 4px;">🥅 {p3_1}<br>⚽ {a3_1}</div>
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

            # Espander per le fasi finali
            almeno_una_ef_corso = any(m.get("in_corso", False) for m in f_turno["partite"])
            ef_chiuse = tutti_giocati
            
            if ef_chiuse:
                ef_header = f"🔥 {f_turno['nome']} (Completato ✅)"
                ef_exp = False
            elif almeno_una_ef_corso:
                ef_header = f"🔥 {f_turno['nome']} (In corso 🔥)"
                ef_exp = True
            else:
                ef_header = f"🔥 {f_turno['nome']} (Chiuso ⏳)"
                ef_exp = False

            with st.expander(ef_header, expanded=ef_exp):
                for idx, m in enumerate(f_turno["partite"]):
                    tavolo_num = (idx % num_tavoli) + 1
                    match_id = m['id']

                    if m["giocata"]:
                        row_class = "match-row-green"
                        center_content = f"<b>{m['gol1']} - {m['gol2']}</b>"
                    elif m.get("in_corso", False):
                        row_class = "match-row-yellow"
                        center_content = f"🔥 In corso (Biliardino {tavolo_num})"
                    else:
                        row_class = "match-row-white"
                        center_content = "VS"

                    st.html(f"""
                        <div class="{row_class}">
                            <div class="team-left">🥅 {m['p1']} &amp; ⚽ {m['a1']}</div>
                            <div class="match-center">{center_content}</div>
                            <div class="team-right">🥅 {m['p2']} &amp; ⚽ {m['a2']}</div>
                        </div>
                    """)

                    if is_admin:
                        col_ea1, col_ea2 = st.columns(2)
                        with col_ea1:
                            if not m["giocata"]:
                                if m.get("in_corso", False):
                                    if st.button(f"⏹️ Ferma Biliardino {tavolo_num}", key=f"ef_stop_{match_id}", use_container_width=True):
                                        m["in_corso"] = False
                                        salva_dati(db)
                                        st.rerun()
                                else:
                                    if st.button(f"▶️ Avvia Biliardino {tavolo_num}", key=f"ef_start_{match_id}", use_container_width=True):
                                        m["in_corso"] = True
                                        salva_dati(db)
                                        st.rerun()
                        with col_ea2:
                            with st.expander(f"⚙️ Risultato Biliardino {tavolo_num}", expanded=False):
                                rg1 = st.radio("Gol S1", list(range(8)), index=min(int(m.get('gol1', 0)), 7), horizontal=True, key=f"ef_rg1_{match_id}")
                                rg2 = st.radio("Gol S2", list(range(8)), index=min(int(m.get('gol2', 0)), 7), horizontal=True, key=f"ef_rg2_{match_id}")
                                if st.button("💾 Salva", key=f"ef_save_{match_id}", use_container_width=True):
                                    m['gol1'] = rg1
                                    m['gol2'] = rg2
                                    m['giocata'] = True
                                    m['in_corso'] = False
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
                            {"id": "ef_t3_m2", "p1": sf1_p["p"], "a1": sf2_p["a"], "p2": sf2_p["p"], "a2": sf1_p["p"], "giocata": False, "in_corso": False, "gol1": 0, "gol2": 0}
                        ]
                        db["fasi_finali"].append({"turno": 3, "nome": "Finali (1°-2° e 3°-4° Posto)", "partite": finali_partite})
                        salva_dati(db)
                        st.rerun()

        if is_admin:
            if st.button("⬅️ Indietro ai Gironi", use_container_width=True):
                db["stato"] = "gironi"
                salva_dati(db)
                st.rerun()
