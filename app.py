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

# CSS personalizzato per compattare gli spazi e guadagnare schermo
st.markdown("""
    <style>
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
            padding-left: 1.5rem;
            padding-right: 1.5rem;
        }
        h1 { margin-bottom: 0px; font-size: 1.8rem; }
        h3 { margin-top: 0.5rem; margin-bottom: 0.5rem; font-size: 1.3rem; }
        h4 { margin-top: 0.3rem; margin-bottom: 0.3rem; font-size: 1.1rem; }
        .stMarkdown { margin-bottom: 0px !important; }
        hr { margin: 0.8rem 0px !important; }
    </style>
""", unsafe_allow_html=True)

DB_FILE = "torneo_data.json"
LOGO_FILE = "logo_uisp.png"
REGOLAMENTO_FILE = "regolamento_uisp.pdf"

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
    p_att = {a: 0 for a in db["attaccanti"]}
    
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
                p_att[m['a1']] = p_att.get(m['a1'], 0) + pt_s1
                p_punti[m['p2']] = p_punti.get(m['p2'], 0) + pt_s2
                p_att[m['a2']] = p_att.get(m['a2'], 0) + pt_s2
                
    db["punti_portieri"] = p_punti
    db["punti_attaccanti"] = p_att

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
    st.sidebar.subheader("📄 Aggiorna Regolamento")
    file_regolamento_caricato = st.sidebar.file_uploader("Carica nuovo PDF Regolamento", type=["pdf"])
    if file_regolamento_caricato is not None:
        with open(REGOLAMENTO_FILE, "wb") as f:
            f.write(file_regolamento_caricato.getbuffer())
        st.sidebar.success("Regolamento aggiornato con successo!")

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

st.sidebar.markdown("---")
st.sidebar.info("📱 **WhatsApp:** Copia l'indirizzo della pagina dal browser e incollalo nel gruppo.")

# --- INTERFACCIA PRINCIPALE ---
logo_html = ""
if os.path.exists(LOGO_FILE):
    with open(LOGO_FILE, "rb") as f:
        logo_b64 = b64encode(f.read()).decode("utf-8")
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="max-width: 240px; width: 100%; height: auto; margin-bottom: 10px;" /><br>'

regolamento_link_html = '📜 Regolamento Ufficiale UISP 2026-2027 (Non caricato)'
if os.path.exists(REGOLAMENTO_FILE):
    with open(REGOLAMENTO_FILE, "rb") as f:
        reg_b64 = b64encode(f.read()).decode("utf-8")
    regolamento_link_html = f'<a href="data:application/pdf;base64,{reg_b64}" target="_blank" style="color: #0d47a1; text-decoration: underline;">📜 Regolamento Tecnico Nazionale UISP 2026-2027 (Clicca per leggere)</a>'

st.markdown(
    f"""
    <div style="text-align: center; margin-bottom: 15px;">
        {logo_html}
        <div style="padding: 10px; background-color: #e3f2fd; border: 2px solid #90caf9; border-radius: 8px;">
            <h2 style="margin: 0; color: #1565c0;">🏆 Torneo Biliardino 'Giallo' Live</h2>
            <p style="margin: 5px 0 0 0; font-size: 1.1rem; font-weight: bold;">{regolamento_link_html}</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div style="padding: 6px; background-color: #f0f2f6; border-radius: 6px; text-align: center; margin-bottom: 10px;">
        🔄 <a href="javascript:window.location.reload(true)" style="text-decoration: none; color: #262730; font-weight: bold; font-size: 13px;">
            Ricarica la pagina del browser per aggiornare l'andamento in tempo reale
        </a>
    </div>
    """,
    unsafe_allow_html=True
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
                db["punti_attaccanti"] = {a: 0 for a in attaccanti}
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

    partite_in_corso = []
    partite_in_coda = []

    for turno_obj in db["turni_partite"]:
        for idx, m in enumerate(turno_obj["partite"]):
            tavolo_num = (idx % num_tavoli) + 1
            if not m["giocata"]:
                info_m = {"turno": turno_obj["turno"], "tavolo": tavolo_num, "m": m}
                if m.get("in_corso", False):
                    partite_in_corso.append(info_m)
                else:
                    partite_in_coda.append(info_m)

    partite_in_corso = partite_in_corso[:num_tavoli]

    # 1. SEZIONE PARTITE IN CORSO (SFONDO GIALLO)
    if partite_in_corso:
        st.markdown(
            """
            <div style="padding: 10px; background-color: #fffde7; border: 2px solid #ffd54f; border-radius: 6px; margin-bottom: 10px;">
                <h4 style="margin: 0; color: #f57f17;">🔥 PARTITE IN CORSO (Sui biliardini):</h4>
            </div>
            """,
            unsafe_allow_html=True
        )
        for item in partite_in_corso:
            m = item["m"]
            match_id = m['id']
            
            st.markdown(f"""
                <div style="padding: 8px; background-color: #fffde7; border: 1px solid #ffe082; border-radius: 6px; margin-bottom: 8px;">
                    <b>📍 Biliardino {item['tavolo']} (Turno {item['turno']})</b><br>
                    🥅 {m['p1']} &nbsp;&nbsp;|&nbsp;&nbsp; ⚽ {m['a1']}<br>
                    🥅 {m['p2']} &nbsp;&nbsp;|&nbsp;&nbsp; ⚽ {m['a2']}
                </div>
            """, unsafe_allow_html=True)
            
            if is_admin:
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("⏹️ Ferma", key=f"stop_{match_id}", use_container_width=True):
                        m["in_corso"] = False
                        salva_dati(db)
                        st.rerun()
                with col_btn2:
                    with st.expander("⚙️ Gestisci Risultato"):
                        rg1 = st.radio("Gol S1", list(range(8)), index=int(m.get('gol1', 0)), horizontal=True, key=f"rg1_{match_id}")
                        rg2 = st.radio("Gol S2", list(range(8)), index=int(m.get('gol2', 0)), horizontal=True, key=f"rg2_{match_id}")
                        if st.button("💾 Salva Risultato", key=f"save_{match_id}", use_container_width=True):
                            m['gol1'] = rg1
                            m['gol2'] = rg2
                            m['giocata'] = True
                            m['in_corso'] = False
                            ricalcola_classifiche()
                            salva_dati(db)
                            st.rerun()
            st.markdown("---")

    # 2. SEZIONE PARTITE IN CODA (SFONDO VERDE)
    if partite_in_coda:
        st.markdown(
            """
            <div style="padding: 10px; background-color: #e8f5e9; border: 2px solid #81c784; border-radius: 6px; margin-bottom: 10px;">
                <h4 style="margin: 0; color: #2e7d32;">📢 PROSSIMI IN CODA (Preparatevi):</h4>
            </div>
            """,
            unsafe_allow_html=True
        )
        for item in partite_in_coda[:num_tavoli]:
            m = item["m"]
            match_id = m['id']
            
            st.markdown(f"""
                <div style="padding: 8px; background-color: #e8f5e9; border: 1px solid #c8e6c9; border-radius: 6px; margin-bottom: 8px;">
                    <b>👉 In Coda (Turno {item['turno']})</b><br>
                    🥅 {m['p1']} &nbsp;&nbsp;|&nbsp;&nbsp; ⚽ {m['a1']}<br>
                    🥅 {m['p2']} &nbsp;&nbsp;|&nbsp;&nbsp; ⚽ {m['a2']}
                </div>
            """, unsafe_allow_html=True)
            
            if is_admin:
                if st.button("▶️ Avvia Partita", key=f"start_{match_id}", use_container_width=True):
                    m["in_corso"] = True
                    salva_dati(db)
                    st.rerun()
            st.markdown("---")

    # 3. CLASSIFICHE IN TEMPO REALE
    st.markdown("### 🏆 Classifiche in Tempo Reale")
    col_c1, col_c2 = st.columns(2)

    with col_c1:
        st.markdown("#### 🥅 Portieri (Top 8)")
        sorted_p = sorted(db["punti_portieri"].items(), key=lambda x: x[1], reverse=True)
        data_p = []
        for idx, (p, pt) in enumerate(sorted_p):
            gioc, tot = calcola_partite_giocate('portiere', p)
            data_p.append({"Pos": f"{idx+1}°", "Portiere": f"🥅 {p}", "Punti": pt, "Giocate": f"{gioc}/{tot}"})
        
        df_p = pd.DataFrame(data_p)
        def colora_top8(row):
            return ['background-color: #e6f2e6' if row.name < 8 else 'background-color: #f9f9f9' for _ in row]
        st.dataframe(df_p.style.apply(colora_top8, axis=1), hide_index=True, use_container_width=True, height=220)

    with col_c2:
        st.markdown("#### ⚽ Attaccanti (Top 8)")
        sorted_a = sorted(db["punti_attaccanti"].items(), key=lambda x: x[1], reverse=True)
        data_a = []
        for idx, (a, pt) in enumerate(sorted_a):
            gioc, tot = calcola_partite_giocate('attaccante', a)
            data_a.append({"Pos": f"{idx+1}°", "Attaccante": f"⚽ {a}", "Punti": pt, "Giocate": f"{gioc}/{tot}"})
            
        df_a = pd.DataFrame(data_a)
        def colora_top8_a(row):
            return ['background-color: #e6f2e6' if row.name < 8 else 'background-color: #f9f9f9' for _ in row]
        st.dataframe(df_a.style.apply(colora_top8_a, axis=1), hide_index=True, use_container_width=True, height=220)

    st.markdown("---")

    # 4. LISTA COMPLETA TURNI E PARTITE
    st.markdown("### 📅 Lista Completa Turni")

    for turno_obj in db["turni_partite"]:
        with st.expander(f"🚩 Turno {turno_obj['turno']} (Clicca per aprire/chiudere)"):
            for idx, m in enumerate(turno_obj["partite"]):
                tavolo_num = (idx % num_tavoli) + 1
                match_id = m['id']
                
                st.markdown(f"**📍 Tavolo {tavolo_num}**")
                st.markdown(f"🥅 {m['p1']} &nbsp;&nbsp;|&nbsp;&nbsp; ⚽ {m['a1']}")
                st.markdown(f"🥅 {m['p2']} &nbsp;&nbsp;|&nbsp;&nbsp; ⚽ {m['a2']}")
                
                if m["giocata"]:
                    st.markdown(f"""
                        <div style="padding: 4px; background-color: #ffebee; border-radius: 4px; text-align: center; margin-top: 4px; margin-bottom: 4px;">
                            🛑 <b>{m['gol1']} - {m['gol2']}</b> (✅ Giocata)
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                        <div style="padding: 4px; background-color: #f1f8e9; border-radius: 4px; text-align: center; margin-top: 4px; margin-bottom: 4px;">
                            ⏳ <b>Da giocare</b>
                        </div>
                    """, unsafe_allow_html=True)

                if is_admin:
                    with st.expander(f"⚙️ Gestisci Risultato (Tavolo {tavolo_num})", key=f"exp_{match_id}"):
                        rg1 = st.radio("Gol S1", list(range(8)), index=int(m.get('gol1', 0)), horizontal=True, key=f"list_rg1_{match_id}")
                        rg2 = st.radio("Gol S2", list(range(8)), index=int(m.get('gol2', 0)), horizontal=True, key=f"list_rg2_{match_id}")
                        if st.button("💾 Salva Risultato", key=f"list_save_{match_id}", use_container_width=True):
                            m['gol1'] = rg1
                            m['gol2'] = rg2
                            m['giocata'] = True
                            m['in_corso'] = False
                            ricalcola_classifiche()
                            salva_dati(db)
                            st.rerun()
                st.markdown("---")

    if is_admin:
        st.markdown("---")
        if st.button("🏆 Avvia Fase Eliminazione Diretta (Quarti)", use_container_width=True):
            top_p = [p[0] for p in sorted(db["punti_portieri"].items(), key=lambda x: x[1], reverse=True)[:8]]
            top_a = [a[0] for a in sorted(db["punti_attaccanti"].items(), key=lambda x: x[1], reverse=True)[:8]]
            
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
    st.subheader("🏆 Fase a Eliminazione Diretta")
    num_tavoli = db.get("num_tavoli", 3)
    fasi = db["fasi_finali"]
    
    for f_idx, f_turno in enumerate(fasi):
        st.markdown(f"### 🔥 {f_turno['nome']}")
        
        tutti_giocati = True
        vincitori_turno = []
        perdenti_turno = []
        
        for idx, m in enumerate(f_turno["partite"]):
            tavolo_num = (idx % num_tavoli) + 1
            match_id = m['id']

            if m.get("giocata", False):
                if m["gol1"] >= m["gol2"]:
                    vincitori_turno.append({"p": m["p1"], "a": m["a1"]})
                    perdenti_turno.append({"p": m["p2"], "a": m["a2"]})
                else:
                    vincitori_turno.append({"p": m["p2"], "a": m["a2"]})
                    perdenti_turno.append({"p": m["p1"], "a": m["a1"]})
            else:
                tutti_giocati = False

            st.markdown(f"**📍 Biliardino {tavolo_num}**")
            st.markdown(f"🥅 **{m['p1']}** &nbsp;&nbsp;|&nbsp;&nbsp; ⚽ **{m['a1']}**")
            st.markdown(f"🥅 **{m['p2']}** &nbsp;&nbsp;|&nbsp;&nbsp; ⚽ **{m['a2']}**")
            
            if m["giocata"]:
                st.markdown(f"""
                    <div style="padding: 4px; background-color: #ffebee; border-radius: 4px; text-align: center; margin-top: 4px; margin-bottom: 4px;">
                        🛑 <b>{m['gol1']} - {m['gol2']}</b> (✅ Giocata)
                    </div>
                """, unsafe_allow_html=True)
            elif m.get("in_corso", False):
                st.markdown(f"""
                    <div style="padding: 4px; background-color: #fffde7; border-radius: 4px; text-align: center; margin-top: 4px; margin-bottom: 4px;">
                        🔥 <b>In Corso</b>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div style="padding: 4px; background-color: #f1f8e9; border-radius: 4px; text-align: center; margin-top: 4px; margin-bottom: 4px;">
                        ⏳ <b>Da giocare</b>
                    </div>
                """, unsafe_allow_html=True)

            if is_admin:
                col_a1, col_a2 = st.columns(2)
                with col_a1:
                    if not m.get("in_corso", False) and not m["giocata"]:
                        if st.button("▶️ Avvia", key=f"ef_btn_{match_id}", use_container_width=True):
                            m["in_corso"] = True
                            salva_dati(db)
                            st.rerun()
                with col_a2:
                    if m.get("in_corso", False):
                        if st.button("⏹️ Ferma", key=f"ef_stop_{match_id}", use_container_width=True):
                            m["in_corso"] = False
                            salva_dati(db)
                            st.rerun()
                
                with st.expander("⚙️ Gestisci Risultato"):
                    rg1 = st.radio("Gol S1", list(range(8)), index=int(m.get('gol1', 0)), horizontal=True, key=f"ef_rg1_{match_id}")
                    rg2 = st.radio("Gol S2", list(range(8)), index=int(m.get('gol2', 0)), horizontal=True, key=f"ef_rg2_{match_id}")
                    if st.button("💾 Salva Risultato", key=f"ef_save_{match_id}", use_container_width=True):
                        m['gol1'] = rg1
                        m['gol2'] = rg2
                        m['giocata'] = True
                        m['in_corso'] = False
                        salva_dati(db)
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
        if st.button("⬅️ Indietro", use_container_width=True):
            db["stato"] = "gironi"
            salva_dati(db)
            st.rerun()
