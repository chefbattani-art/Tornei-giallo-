import streamlit as st
import pandas as pd
import json
import os
import re
import random
import time

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
        "punti_attaccanti": {}
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

# Inizializza lo stato dei timer in memoria per ogni partita se non esiste
if "timers" not in st.session_state:
    st.session_state.timers = {}

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
st.sidebar.info("📱 **Link WhatsApp:** Copia l'indirizzo della pagina dal browser e incollalo nel gruppo. Tutti vedranno la live in tempo reale!")

if is_admin:
    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Ricomincia Torneo da Zero (Sidebar)"):
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
        st.session_state.db = carica_dati()
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
            db["num_tavoli"] = st.number_input("Numero di tavoli disponibili", min_value=1, max_value=10, value=db["num_tavoli"])
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
            
            if len(portieri) < 2 or len(attaccanti) < 2:
                st.error("Assicurati di inserire almeno 2 portieri (con 🥅) e 2 attaccanti (con ⚽).")
            else:
                db["portieri"] = portieri
                db["attaccanti"] = attaccanti
                db["punti_portieri"] = {p: 0 for p in portieri}
                db["punti_attaccanti"] = {a: 0 for a in attaccanti}
                db["stato"] = "gironi"
                
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

# 2. GIRONI E CALENDARIO A TURNI
elif db["stato"] == "gironi":
    st.subheader("📊 Calendario e Risultati in Diretta")
    
    if is_admin:
        st.info("💡 **Modalità Admin attiva:** Gestisci i tavoli, fai partire il timer da 60s o inserisci i risultati.")
    else:
        st.info("👀 **Modalità Spettatore:** Stai visualizzando i turni, i tavoli e i timer in tempo reale.")

    num_tavoli = db.get("num_tavoli", 2)

    for turno_obj in db["turni_partite"]:
        n_turno = turno_obj["turno"]
        st.markdown(f"""
        <div style="background-color: #1e7e34; padding: 10px; border-radius: 5px; color: white; font-weight: bold; font-size: 18px; margin-bottom: 15px;">
            🚩 Turno {n_turno}
        </div>
        """, unsafe_allow_html=True)
        
        partite = turno_obj["partite"]
        
        for idx, m in enumerate(partite):
            # Assegna un numero di tavolo ciclico (es. Tavolo 1, Tavolo 2, ecc.)
            tavolo_num = (idx % num_tavoli) + 1
            
            # Individua la coppia successiva sullo stesso tavolo (se esiste)
            prossima_partita_test = "Nessuna (Ultima del turno)"
            next_idx = idx + num_tavoli
            if next_idx < len(partite):
                nm = partite[next_idx]
                prossima_partita_test = f"🥅 {nm['p1']} / ⚽ {nm['a1']}  VS  🥅 {nm['p2']} / ⚽ {nm['a2']}"

            with st.container():
                st.markdown(f"📍 **Tavolo {tavolo_num}**", unsafe_allow_html=True)
                col_s1, col_mid, col_s2 = st.columns([4, 3, 4])
                
                with col_s1:
                    st.markdown(f"📖 **{m['p1']}**<br>⚽ **{m['a1']}**", unsafe_allow_html=True)
                
                with col_mid:
                    if not m["giocata"]:
                        st.markdown("<div style='text-align: center; color: gray; font-weight: bold;'>VS<br>(Da Giocare)</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div style='text-align: center; background-color: #e2e3e5; padding: 4px; border-radius: 5px; font-weight: bold;'>Risultato: {m['gol1']} - {m['gol2']}</div>", unsafe_allow_html=True)
                    
                    # Gestione Timer 60 secondi
                    match_id = m['id']
                    if match_id not in st.session_state.timers:
                        st.session_state.timers[match_id] = {"running": False, "start_time": 0}
                    
                    t_state = st.session_state.timers[match_id]
                    
                    if not m["giocata"]:
                        if not t_state["running"]:
                            if st.button("▶️ Avvia Partita (60s)", key=f"btn_start_{match_id}"):
                                st.session_state.timers[match_id] = {"running": True, "start_time": time.time()}
                                st.rerun()
                        else:
                            elapsed = int(time.time() - t_state["start_time"])
                            remaining = 60 - elapsed
                            
                            if remaining > 0:
                                st.markdown(f"<div style='text-align: center; color: #d9534f; font-weight: bold;'>⏳ Mancano {remaining}s</div>", unsafe_allow_html=True)
                                time.sleep(1)
                                st.rerun()
                            else:
                                # Tempo scaduto! Notifica visiva + Audio (bip HTML5)
                                st.markdown(f"""
                                <div style="background-color: #ffcccc; color: #990000; padding: 8px; border-radius: 5px; text-align: center; font-weight: bold; font-size: 14px; border: 2px solid red;">
                                    🚨 TEMPO SCADUTO (60s)!<br>
                                    Pronti al <b>Tavolo {tavolo_num}</b>:<br>
                                    {prossima_partita_test}
                                </div>
                                <audio autoplay>
                                  <source src="https://actions.google.com/sounds/v1/alarms/beep_short.ogg" type="audio/ogg">
                                </audio>
                                """, unsafe_allow_html=True)
                                
                                if st.button("⏹️ Resetta Avviso", key=f"reset_{match_id}"):
                                    st.session_state.timers[match_id]["running"] = False
                                    st.rerun()

                    if is_admin:
                        with st.expander("⚙️ Modifica Risultato"):
                            with st.form(f"form_{match_id}"):
                                rg1 = st.number_input("Gol S1", min_value=0, value=m.get('gol1', 0), key=f"rg1_{match_id}")
                                rg2 = st.number_input("Gol S2", min_value=0, value=m.get('gol2', 0), key=f"rg2_{match_id}")
                                if st.form_submit_button("Salva"):
                                    m['gol1'] = rg1
                                    m['gol2'] = rg2
                                    m['giocata'] = True
                                    # Spegni il timer se la partita viene segnata come giocata
                                    st.session_state.timers[match_id]["running"] = False
                                    ricalcola_classifiche()
                                    salva_dati(db)
                                    st.success("Salvato!")
                                    st.rerun()

                with col_s2:
                    st.markdown(f"📖 **{m['p2']}**<br>⚽ **{m['a2']}**", unsafe_allow_html=True)
                
                st.markdown("---")

    ricalcola_classifiche()

    # Classifiche
    st.markdown("### 🏆 Classifiche in Tempo Reale")
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        st.markdown("#### 🥅 Classifica Portieri")
        df_p = pd.DataFrame(list(db["punti_portieri"].items()), columns=["Portiere", "Punti"]).sort_values(by="Punti", ascending=False)
        st.dataframe(df_p, use_container_width=True, hide_index=True)
    with col_c2:
        st.markdown("#### ⚽ Classifica Attaccanti")
        df_a = pd.DataFrame(list(db["punti_attaccanti"].items()), columns=["Attaccante", "Punti"]).sort_values(by="Punti", ascending=False)
        st.dataframe(df_a, use_container_width=True, hide_index=True)

    if is_admin:
        st.markdown("---")
        if st.button("🏆 Passa alle Fasi Finali (Eliminazione Diretta)"):
            db["stato"] = "eliminatorie"
            salva_dati(db)
            st.rerun()

# 3. ELIMINATORIE
elif db["stato"] == "eliminatorie":
    st.subheader("🏆 Fasi Finali a Eliminazione Diretta")
    st.write("Tabellone in fase di configurazione...")
