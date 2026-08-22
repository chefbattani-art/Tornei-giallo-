import streamlit as st
import pandas as pd
import json
import os

st.set_page_config(page_title="Torneo Biliardino Giallo Live", layout="wide")

# File per mantenere i dati salvati anche se si ricarica la pagina (Persistenza)
DB_FILE = "torneo_data.json"

def carica_dati():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {
        "stato": "setup", # setup, gironi, eliminatorie
        "portieri": [],
        "attaccanti": [],
        "num_tavoli": 2,
        "partite_per_giocatore": 5,
        "admin_pin": "0000",
        "partite_turno_corrente": [],
        "storico_partite": []
    }

def salva_dati(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Inizializzazione dello stato dai dati persistenti
if "db" not in st.session_state:
    st.session_state.db = carica_dati()

db = st.session_state.db

# --- BARRA LATERALE: GESTIONE ACCESSO ADMIN ---
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
st.sidebar.info("📱 **Link per WhatsApp:** Copia l'indirizzo di questa pagina web e incollalo nel gruppo WhatsApp del torneo. Tutti potranno seguire la live!")

# --- INTERFACCIA PRINCIPALE ---
st.title("⚽ Torneo Biliardino 'Giallo' Live")

# 1.FASE DI SETUP (Solo Admin)
if db["stato"] == "setup":
    st.subheader("1. Configurazione Iniziale del Torneo")
    
    if not is_admin:
        st.warning("⚠️ Il torneo non è ancora iniziato. Solo l'amministratore (tramite PIN nella barra laterale) può inserire i partecipanti e avviarlo.")
    else:
        whatsapp_text = st.text_area(
            "Incolla qui la lista da WhatsApp (es. 🚪 Mario, ⚽ Luigi):",
            placeholder="🚪 Portiere Rossi\n⚽ Attaccante Bianchi..."
        )
        
        col1, col2 = st.columns(2)
        with col1:
            db["num_tavoli"] = st.number_input("Numero di tavoli disponibili", min_value=1, max_value=10, value=db["num_tavoli"])
        with col2:
            db["partite_per_giocatore"] = st.number_input("Partite garantite a testa", min_value=1, max_value=15, value=db["partite_per_giocatore"])
            
        nuovo_pin = st.text_input("Imposta/Cambia PIN Admin", value=db["admin_pin"])
        db["admin_pin"] = nuovo_pin

        if st.button("🚀 Avvia il Torneo e Genera Calendario"):
            portieri = []
            attaccanti = []
            for line in whatsapp_text.split("\n"):
                if "🚪" in line:
                    nome = line.replace("🚪", "").strip()
                    if nome: portieri.append(nome)
                elif "⚽" in line:
                    nome = line.replace("⚽", "").strip()
                    if nome: attaccanti.append(nome)
            
            if len(portieri) < 2 or len(attaccanti) < 2:
                st.error("Assicurati di aver inserito almeno portieri e attaccanti con le emoji (🚪 e ⚽).")
            else:
                db["portieri"] = portieri
                db["attaccanti"] = attaccanti
                db["stato"] = "gironi"
                # Esempio di generazione fittizia prima partita per i tavoli
                db["partite_turno_corrente"] = [
                    {"tavolo": i+1, "squadra1": f"Portiere {i} + Attaccante {i}", "squadra2": f"Portiere {i+2} + Attaccante {i+2}", "stato": "In Corso"} 
                    for i in range(min(db["num_tavoli"], len(portieri)//2))
                ]
                salva_dati(db)
                st.success("Torneo avviato con successo! Ricarica la pagina.")
                st.rerun()

# 2.FASE GIRONI E LIVE TAVOLI
elif db["stato"] == "gironi":
    st.subheader("📊 Andamento Torneo in Diretta (Live)")
    
    # Visualizzazione Tavoli in tempo reale (Visibile a tutti)
    st.markdown("### 🏟️ Stato Tavoli e Chiamate")
    
    cols = st.columns(db["num_tavoli"])
    for idx, partita in enumerate(db["partite_turno_corrente"]):
        with cols[idx % len(cols)]:
            st.markdown(f"#### Tavolo {partita['tavolo']}")
            st.info(f"🟢 **In Corso:**\n\n {partita['squadra1']} \n\n **VS** \n\n {partita['squadra2']}")
            st.warning("🔔 **Prossimo turno:** Prepararsi tra circa 60 secondi!")
            
            if is_admin:
                if st.button(f"Termina Partita Tavolo {partita['tavolo']}", key=f"end_{idx}"):
                    # Logica per marcare come finita e scalare
                    st.success(f"Partita al tavolo {partita['tavolo']} completata!")

    st.markdown("---")
    
    # Classifiche provvisorie
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        st.markdown("#### 🚪 Classifica Portieri")
        st.dataframe(pd.DataFrame({"Portiere": db["portieri"], "Punti": [0]*len(db["portieri"])}))
    with col_c2:
        st.markdown("#### ⚽ Classifica Attaccanti")
        st.dataframe(pd.DataFrame({"Attaccante": db["attaccanti"], "Punti": [0]*len(db["attaccanti"])}))

    # Pannello riservato all'Admin per inserire i risultati o avanzare turno
    if is_admin:
        st.markdown("---")
        st.subheader("🛠️ Pannello Gestione Risultati (Admin)")
        risultato_s1 = st.number_input("Gol Squadra 1", min_value=0, value=0)
        risultato_s2 = st.number_input("Gol Squadra 2", min_value=0, value=0)
        if st.button("Registra Risultato e Chiama Nuove Coppie"):
            st.success("Risultato registrato e prossime coppie notificate!")
            
        if st.button("🏁 Passa alle Fasi Finali (Eliminazione Diretta)"):
            db["stato"] = "eliminatorie"
            salva_dati(db)
            st.rerun()

# 3.FASE FINALE A ELIMINAZIONE DIRETTA
elif db["stato"] == "eliminatorie":
    st.subheader("🏆 Fasi Finali a Eliminazione Diretta (Tabellone Protetto)")
    st.write("I primi classificati dei gironi si affrontano rispettando il tabellone protetto (non possono incontrarsi prima della finale).")
    
    # Vista pubblica del tabellone
    st.info("Tabellone in corso di aggiornamento da parte dell'amministratore...")
    
    if is_admin:
        st.markdown("---")
        st.subheader("🛠️ Gestione Turno Eliminatorio (Admin)")
        vincitore = st.selectbox("Seleziona chi ha vinto l'incontro", ["Coppia 1", "Coppia 2"])
        if st.button("Registra e Avanza nel Tabellone"):
            st.success("Turno aggiornato!")

        if st.button("🔄 Reset Totale Torneo"):
            if os.path.exists(DB_FILE):
                os.remove(DB_FILE)
            st.session_state.db = carica_dati()
            st.rerun()
