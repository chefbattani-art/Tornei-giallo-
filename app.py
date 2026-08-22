import streamlit as st
import pandas as pd
import json
import os
import re
import random
from streamlit_autorefresh import st_autorefresh

# Aggiornamento automatico ogni 5 secondi per tutti
st_autorefresh(interval=5000, debounce=False, key="auto_refresh_torneo")

st.set_page_config(page_title="Torneo Biliardino Giallo Live", layout="wide")

DB_FILE = "torneo_data.json"

def carica_dati():
    dati_default = {
        "stato": "setup",
        "portieri": [],
        "attaccanti": [],
        "num_tavoli": 2,
        "partite_per_giocatore": 5,
        "admin_pin": "0000",
        "turni_partite": [], 
        "storico_partite": [],
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

# --- BARRA LATERALE ADMIN ---
st.sidebar.header("⚙️ Pannello di Controllo")
modalita_admin = st.sidebar.checkbox("Modalità Amministratore (Inserisci PIN)")

is_admin = False
if modalita_admin:
    pin_inserito = st.sidebar.text_input("Inserisci PIN Admin", type="password")
    if pin_inserito == db["admin_pin"]:
        is_admin = True
        st.sidebar.success("Accesso Admin Autorizzato ✅")
    else:
        st.sidebar.error("PIN errato. Vista solo lettura (Pubblica).")

st.sidebar.markdown("---")
st.sidebar.info("📱 **Link WhatsApp:** Copia l'indirizzo della pagina dal browser e incollalo nel gruppo. La pagina si aggiornerà automaticamente ogni 5 secondi per tutti!")

# --- INTERFACCIA PRINCIPALE ---
st.title("⚽ Torneo Biliardino 'Giallo' Live")

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
elif db["stato"] == "gironi":
    st.subheader("📊 Classifiche e Calendario in Diretta (Gironi)")
    ricalcola_classifiche()

    st.markdown("### 🏆 Classifiche in Tempo Reale")
    col_c1, col_c2 = st.columns(2)

    with col_c1:
        st.markdown("#### 🥅 Classifica Portieri")
        sorted_p = sorted(db["punti_portieri"].items(), key=lambda x: x[1], reverse=True)
        data_p = [{"Pos": f"{idx+1}°", "Portiere": f"🥅 {p}", "Punti": pt, "Giocate": f"{calcola_partite_giocate('portiere', p)[0]}/{calcola_partite_giocate('portiere', p)[1]}"} for idx, (p, pt) in enumerate(sorted_p)]
        st.dataframe(pd.DataFrame(data_p), hide_index=True, use_container_width=True)

    with col_c2:
        st.markdown("#### ⚽ Classifica Attaccanti")
        sorted_a = sorted(db["punti_attaccanti"].items(), key=lambda x: x[1], reverse=True)
        data_a = [{"Pos": f"{idx+1}°", "Attaccante": f"⚽ {a}", "Punti": pt, "Giocate": f"{calcola_partite_giocate('attaccante', a)[0]}/{calcola_partite_giocate('attaccante', a)[1]}"} for idx, (a, pt) in enumerate(sorted_a)]
        st.dataframe(pd.DataFrame(data_a), hide_index=True, use_container_width=True)

    st.markdown("---")
    st.markdown("### 📅 Calendario Partite")
    num_tavoli = db.get("num_tavoli", 2)

    for turno_obj in db["turni_partite"]:
        st.markdown(f"### 🚩 Turno {turno_obj['turno']}")
        for idx, m in enumerate(turno_obj["partite"]):
            tavolo_num = (idx % num_tavoli) + 1
            match_id = m['id']

            st.markdown(f"**📍 Biliardino {tavolo_num}**")
            col_s1, col_mid, col_s2 = st.columns([4, 2.5, 4], gap="small")
            
            with col_s1:
                st.info(f"🥅 **{m['p1']}**\n\n⚽ **{m['a1']}**")
            
            with col_mid:
                if m["giocata"]:
                    st.error(f"🛑 **{m['gol1']} - {m['gol2']}**")
                elif m.get("in_corso", False):
                    st.warning("🔥 **In Corso**")
                else:
                    st.write("**VS**")
                    if is_admin:
                        if st.button("▶️ Avvia", key=f"btn_avvia_{match_id}", use_container_width=True):
                            m["in_corso"] = True
                            salva_dati(db)
                            st.rerun()

            with col_s2:
                st.info(f"🥅 **{m['p2']}**\n\n⚽ **{m['a2']}**")
            
            if is_admin:
                with st.expander("⚙️ Gestisci Risultato"):
                    rg1 = st.radio("Gol S1", list(range(8)), index=int(m.get('gol1', 0)), horizontal=True, key=f"rg1_{match_id}")
                    rg2 = st.radio("Gol S2", list(range(8)), index=int(m.get('gol2', 0)), horizontal=True, key=f"rg2_{match_id}")
                    if st.button("💾 Salva", key=f"save_{match_id}", use_container_width=True):
                        m['gol1'] = rg1
                        m['gol2'] = rg2
                        m['giocata'] = True
                        m['in_corso'] = False
                        ricalcola_classifiche()
                        salva_dati(db)
                        st.success("Salvato!")
                        st.rerun()
            st.markdown("---")

    if is_admin:
        if st.button("🏆 Genera Fasi Finali (8 Portieri & 8 Attaccanti)", use_container_width=True):
            top_p = [p[0] for p in sorted(db["punti_portieri"].items(), key=lambda x: x[1], reverse=True)[:8]]
            top_a = [a[0] for a in sorted(db["punti_attaccanti"].items(), key=lambda x: x[1], reverse=True)[:8]]
            
            turno1_partite = [
                {"id": "ef_t1_m1", "p1": top_p[0], "a1": top_a[0], "p2": top_p[7], "a2": top_a[7], "giocata": False, "in_corso": False, "gol1": 0, "gol2": 0},
                {"id": "ef_t1_m2", "p1": top_p[1], "a1": top_a[1], "p2": top_p[6], "a2": top_a[6], "giocata": False, "in_corso": False, "gol1": 0, "gol2": 0},
                {"id": "ef_t1_m3", "p1": top_p[2], "a1": top_a[2], "p2": top_p[5], "a2": top_a[5], "giocata": False, "in_corso": False, "gol1": 0, "gol2": 0},
                {"id": "ef_t1_m4", "p1": top_p[3], "a1": top_a[3], "p2": top_p[4], "a2": top_a[4], "giocata": False, "in_corso": False, "gol1": 0, "gol2": 0}
            ]
            db["fasi_finali"] = [{"turno": 1, "nome": "Quarti di Finale", "partite": turno1_partite}]
            db["stato"] = "eliminatorie"
            salva_dati(db)
            st.rerun()

# 3. ELIMINATORIE
elif db["stato"] == "eliminatorie":
    st.subheader("🏆 Fasi Finali a Eliminazione Diretta")
    num_tavoli = db.get("num_tavoli", 2)
    
    for f_turno in db["fasi_finali"]:
        st.markdown(f"### 🔥 {f_turno['nome']} (Turno {f_turno['turno']})")
        turno_completato = True
        
        for idx, m in enumerate(f_turno["partite"]):
            tavolo_num = (idx % num_tavoli) + 1
            match_id = m['id']
            if not m["giocata"]: turno_completato = False

            st.markdown(f"**📍 Biliardino {tavolo_num}**")
            col_s1, col_mid, col_s2 = st.columns([4, 2.5, 4], gap="small")
            
            with col_s1:
                st.info(f"🥅 **{m['p1']}**\n\n⚽ **{m['a1']}**")
            
            with col_mid:
                if m["giocata"]:
                    st.error(f"🛑 **{m['gol1']} - {m['gol2']}**")
                elif m.get("in_corso", False):
                    st.warning("🔥 **In Corso**")
                else:
                    st.write("**VS**")
                    if is_admin:
                        if st.button("▶️ Avvia", key=f"ef_btn_{match_id}", use_container_width=True):
                            m["in_corso"] = True
                            salva_dati(db)
                            st.rerun()
                
                if is_admin:
                    with st.expander("⚙️ Gestisci Risultato"):
                        rg1 = st.radio("Gol S1", list(range(8)), index=int(m.get('gol1', 0)), horizontal=True, key=f"ef_rg1_{match_id}")
                        rg2 = st.radio("Gol S2", list(range(8)), index=int(m.test if 'gol2' in m else 0), horizontal=True, key=f"ef_rg2_{match_id}")
                        if st.button("💾 Salva", key=f"ef_save_{match_id}", use_container_width=True):
                            m['gol1'] = rg1
                            m['gol2'] = rg2
                            m['giocata'] = True
                            m['in_corso'] = False
                            salva_dati(db)
                            st.success("Salvato!")
                            st.rerun()

            with col_s2:
                st.info(f"🥅 **{m['p2']}**\n\n⚽ **{m['a2']}**")
            st.markdown("---")
