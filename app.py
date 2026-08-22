import streamlit as st
import pandas as pd
import json
import os
import re
import random
from streamlit_autorefresh import st_autorefresh

# Imposta il refresh automatico ogni 10 secondi (10000 millisecondi)
st_autorefresh(interval=10000, key="auto_refresh_torneo")

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

if "partite_avviate" not in st.session_state:
    st.session_state.partite_avviate = {}

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
st.sidebar.info("📱 **Link WhatsApp:** Copia l'indirizzo della pagina dal browser e incollalo nel gruppo. La pagina si aggiornerà automaticamente ogni 10 secondi per tutti!")

if is_admin:
    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Ricomincia Torneo da Zero (Sidebar)"):
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
        st.session_state.db = carica_dati()
        st.session_state.partite_avviate = {}
        st.rerun()

# --- INTERFACCIA PRINCIPALE ---
st.title("⚽ Torneo Biliardino 'Giallo' Live")

if is_admin and db["stato"] != "setup":
    col_reset1, col_reset2 = st.columns([3, 1])
    with col_reset2:
        if st.button("🗑️ Ricomincia Torneo", type="primary"):
            if os.path.exists(DB_FILE):
                os.remove(DB_FILE)
            st.session_state.db = carica_dati()
            st.session_state.partite_avviate = {}
            st.rerun()

# 1. SETUP
if db["stato"] == "setup":
    st.subheader("1. Configurazione Iniziale del Torneo")
    
    if not is_admin:
        st.warning("⚠️ Il torneo non è ancora iniziato. L'amministratore deve effettuare l'accesso con il PIN nella barra laterale per inserire i partecipanti.")
    else:
        whatsapp_text = st.text_area(
            "Incolla qui la lista da WhatsApp (es. 🥅 Mario, ⚽ Luigi):",
            placeholder="🥅 1. Rossi\n⚽ 2. Bianchi..."
        )
        
        col1, col2 = st.columns(2)
        with col1:
            db["num_tavoli"] = st.number_input("Numero di biliardini disponibili", min_value=1, max_value=10, value=db["num_tavoli"])
        with col2:
            db["partite_per_giocatore"] = st.number_input("Turni / Partite garantite", min_value=1, max_value=10, value=db["partite_per_giocatore"])
            
        nuovo_pin = st.text_input("Cambia PIN Admin", value=db["admin_pin"])
        db["admin_pin"] = nuovo_pin

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
                st.error("Per fare le fasi finali con 8 portieri e 8 attaccanti, devi inserire almeno 8 portieri (con 🥅) e 8 attaccanti (con ⚽).")
            else:
                db["portieri"] = portieri
                db["attaccanti"] = attaccanti
                db["punti_portieri"] = {p: 0 for p in portieri}
                db["punti_attaccanti"] = {a: 0 for a in attaccanti}
                db["stato"] = "gironi"
                db["fasi_finali"] = []
                
                db["turni_partite"] = []
                num_turni = db["partite_per_giocatore"]
                for t in range(1, num_turni + 1):
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
                            "giocata": False,
                            "gol1": 0, "gol2": 0
                        })
                        i += 2
                    db["turni_partite"].append({"turno": t, "partite": partite_turno})

                salva_dati(db)
                st.success("Calendario generato con successo!")
                st.rerun()

# 2. GIRONI
elif db["stato"] == "gironi":
    st.subheader("📊 Classifiche e Calendario in Diretta (Gironi)")
    
    if is_admin:
        st.info("💡 **Modalità Admin attiva:** Avvia le partite o inserisci i risultati quando si concludono.")
    else:
        st.info("👀 **Modalità Spettatore:** La pagina si aggiorna automaticamente ogni 10 secondi.")

    ricalcola_classifiche()

    # --- CLASSIFICHE IN CIMA (Con Tabelle native Streamlit) ---
    st.markdown("### 🏆 Classifiche in Tempo Reale")

    col_c1, col_c2 = st.columns(2)

    with col_c1:
        st.markdown("#### 🥅 Classifica Portieri")
        sorted_p = sorted(db["punti_portieri"].items(), key=lambda x: x[1], reverse=True)
        data_p = []
        for idx, (p, pt) in enumerate(sorted_p):
            giocate, totali = calcola_partite_giocate("portiere", p)
            data_p.append({
                "Pos": f"{idx+1}°",
                "Portiere": f"🥅 {p}",
                "Punti": pt,
                "Giocate": f"{giocate}/{totali}"
            })
        st.dataframe(pd.DataFrame(data_p), hide_index=True, use_container_width=True)

    with col_c2:
        st.markdown("#### ⚽ Classifica Attaccanti")
        sorted_a = sorted(db["punti_attaccanti"].items(), key=lambda x: x[1], reverse=True)
        data_a = []
        for idx, (a, pt) in enumerate(sorted_a):
            giocate, totali = calcola_partite_giocate("attaccante", a)
            data_a.append({
                "Pos": f"{idx+1}°",
                "Attaccante": f"⚽ {a}",
                "Punti": pt,
                "Giocate": f"{giocate}/{totali}"
            })
        st.dataframe(pd.DataFrame(data_a), hide_index=True, use_container_width=True)

    st.markdown("---")
    st.markdown("### 📅 Calendario Partite")

    num_tavoli = db.get("num_tavoli", 2)

    for turno_obj in db["turni_partite"]:
        n_turno = turno_obj["turno"]
        st.markdown(f"### 🚩 Turno {n_turno}")
        
        partite = turno_obj["partite"]
        
        for idx, m in enumerate(partite):
            tavolo_num = (idx % num_tavoli) + 1
            match_id = m['id']
            is_avviata = st.session_state.partite_avviate.get(match_id, False)

            st.markdown(f"**📍 Biliardino {tavolo_num}**")
            col_s1, col_mid, col_s2 = st.columns([4, 2.5, 4], gap="small")
            
            with col_s1:
                st.info(f"🥅 **{m['p1']}**\n\n⚽ **{m['a1']}**")
            
            with col_mid:
                if m["giocata"]:
                    st.error(f"🛑 **{m['gol1']} - {m['gol2']}**")
                elif is_avviata:
                    st.warning("🔥 **In Corso**")
                else:
                    st.write("**VS**")
                    if is_admin:
                        if st.button("▶️ Avvia", key=f"btn_avvia_{match_id}", use_container_width=True):
                            st.session_state.partite_avviate[match_id] = True
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
                        st.session_state.partite_avviate[match_id] = False
                        ricalcola_classifiche()
                        salva_dati(db)
                        st.success("Salvato!")
                        st.rerun()
            
            st.markdown("---")

    if is_admin:
        if st.button("🏆 Genera Fasi Finali (8 Portieri & 8 Attaccanti)", use_container_width=True):
            df_p_sorted = sorted(db["punti_portieri"].items(), key=lambda x: x[1], reverse=True)
            df_a_sorted = sorted(db["punti_attaccanti"].items(), key=lambda x: x[1], reverse=True)
            
            top_p = [p[0] for p in df_p_sorted[:8]]
            top_a = [a[0] for a in df_a_sorted[:8]]
            
            turno1_partite = [
                {"id": "ef_t1_m1", "p1": top_p[0], "a1": top_a[0], "p2": top_p[7], "a2": top_a[7], "giocata": False, "gol1": 0, "gol2": 0},
                {"id": "ef_t1_m2", "p1": top_p[1], "a1": top_a[1], "p2": top_p[6], "a2": top_a[6], "giocata": False, "gol1": 0, "gol2": 0},
                {"id": "ef_t1_m3", "p1": top_p[2], "a1": top_a[2], "p2": top_p[5], "a2": top_a[5], "giocata": False, "gol1": 0, "gol2": 0},
                {"id": "ef_t1_m4", "p1": top_p[3], "a1": top_a[3], "p2": top_p[4], "a2": top_a[4], "giocata": False, "gol1": 0, "gol2": 0}
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
        t_num = f_turno["turno"]
        t_nome = f_turno["nome"]
        
        st.markdown(f"### 🔥 {t_nome} (Turno {t_num})")
        
        partite = f_turno["partite"]
        turno_completato = True
        
        for idx, m in enumerate(partite):
            tavolo_num = (idx % num_tavoli) + 1
            match_id = m['id']
            is_avviata = st.session_state.partite_avviate.get(match_id, False)
            
            if not m["giocata"]:
                turno_completato = False

            st.markdown(f"**📍 Biliardino {tavolo_num}**")
            col_s1, col_mid, col_s2 = st.columns([4, 2.5, 4], gap="small")
            
            with col_s1:
                st.info(f"🥅 **{m['p1']}**\n\n⚽ **{m['a1']}**")
            
            with col_mid:
                if m["giocata"]:
                    st.error(f"🛑 **{m['gol1']} - {m['gol2']}**")
                elif is_avviata:
                    st.warning("🔥 **In Corso**")
                else:
                    st.write("**VS**")
                    if is_admin:
                        if st.button("▶️ Avvia", key=f"ef_btn_{match_id}", use_container_width=True):
                            st.session_state.partite_avviate[match_id] = True
                            st.rerun()
                
                if is_admin:
                    with st.expander("⚙️ Gestisci Risultato"):
                        rg1 = st.radio("Gol S1", list(range(8)), index=int(m.get('gol1', 0)), horizontal=True, key=f"ef_rg1_{match_id}")
                        rg2 = st.radio("Gol S2", list(range(8)), index=int(m.get('gol2', 0)), horizontal=True, key=f"ef_rg2_{match_id}")
                        if st.button("💾 Salva", key=f"ef_save_{match_id}", use_container_width=True):
                            m['gol1'] = rg1
                            m['gol2'] = rg2
                            m['giocata'] = True
                            st.session_state.partite_avviate[match_id] = False
                            salva_dati(db)
                            st.success("Salvato!")
                            st.rerun()

            with col_s2:
                st.info(f"🥅 **{m['p2']}**\n\n⚽ **{m['a2']}**")
            
            st.markdown("---")
        
        if turno_completato and is_admin:
            già_presente_successivo = any(f["turno"] == t_num + 1 for f in db["fasi_finali"])
            if not già_presente_successivo:
                vincitori_p = []
                vincitori_a = []
                
                for m in partite:
                    if m["gol1"] > m["gol2"]:
                        p_vincente, a_vincente = m["p1"], m["a1"]
                    else:
                        p_vincente, a_vincente = m["p2"], m["a2"]
                    vincitori_p.append(p_vincente)
                    vincitori_a.append(a_vincente)
                
                if len(vincitori_p) > 1:
                    nuovo_nome = "Semifinale" if len(vincitori_p) == 4 else ("Finale" if len(vincitori_p) == 2 else f"Turno {t_num+1}")
                    
                    random.shuffle(vincitori_p)
                    random.shuffle(vincitori_a)
                        
                    nuove_partite = []
                    for i in range(0, len(vincitori_p), 2):
                        if i + 1 < len(vincitori_p):
                            nuove_partite.append({
                                "id": f"ef_t{t_num+1}_m{i//2}",
                                "p1": vincitori_p[i], "a1": vincitori_a[i],
                                "p2": vincitori_p[i+1], "a2": vincitori_a[i+1],
                                "giocata": False, "gol1": 0, "gol2": 0
                            })
                    
                    if nuove_partite:
                        db["fasi_finali"].append({
                            "turno": t_num + 1,
                            "nome": nuovo_nome,
                            "partite": nuove_partite
                        })
                        salva_dati(db)
                        st.success(f"Generato il turno successivo: {nuovo_nome}!")
                        st.rerun()
                elif len(vincitori_p) == 1:
                    st.success(f"🏆 Torneo Conclusi! Coppia Campione: 🥅 {vincitori_p[0]} e ⚽ {vincitori_a[0]}")
