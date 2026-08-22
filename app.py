import streamlit as st
import pandas as pd
import json
import os
from io import BytesIO

st.set_page_config(page_title="Torneo Biliardino Giallo Live", layout="wide")

DB_FILE = "torneo_data.json"

def carica_dati():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {
        "stato": "setup",
        "portieri": [],
        "attaccanti": [],
        "num_tavoli": 2,
        "partite_per_giocatore": 5,
        "admin_pin": "0000",
        "tavoli_attivi": {}, 
        "coda_partite": [],  
        "storico_partite": []
    }

def salva_dati(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

if "db" not in st.session_state:
    st.session_state.db = carica_dati()

db = st.session_state.db

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
    if st.sidebar.button("🔄 Ricomincia Torneo da Zero"):
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
        st.session_state.db = carica_dati()
        st.rerun()

# --- INTERFACCIA PRINCIPALE ---
st.title("⚽ Torneo Biliardino 'Giallo' Live")

# 1. SETUP
if db["stato"] == "setup":
    st.subheader("1. Configurazione Iniziale del Torneo")
    
    if not is_admin:
        st.warning("⚠️ Il torneo non è ancora iniziato. L'amministratore deve effettuare l'accesso con il PIN nella barra laterale per inserire i partecipanti.")
    else:
        whatsapp_text = st.text_area(
            "Incolla qui la lista da WhatsApp (es. 🥅 Mario, ⚽ Luigi):",
            placeholder="🥅 Nome Portiere\n⚽ Nome Attaccante..."
        )
        
        col1, col2 = st.columns(2)
        with col1:
            db["num_tavoli"] = st.number_input("Numero di tavoli disponibili", min_value=1, max_value=10, value=db["num_tavoli"])
        with col2:
            db["partite_per_giocatore"] = st.number_input("Partite garantite a testa", min_value=1, max_value=15, value=db["partite_per_giocatore"])
            
        nuovo_pin = st.text_input("Cambia PIN Admin", value=db["admin_pin"])
        db["admin_pin"] = nuovo_pin

        if st.button("🚀 Avvia il Torneo e Genera Calendario"):
            portieri = []
            attaccanti = []
            for line in whatsapp_text.split("\n"):
                if "🥅" in line or "🚪" in line:
                    nome = line.replace("🥅", "").replace("🚪", "").strip()
                    if nome: portieri.append(nome)
                elif "⚽" in line:
                    nome = line.replace("⚽", "").strip()
                    if nome: attaccanti.append(nome)
            
            if len(portieri) < 2 or len(attaccanti) < 2:
                st.error("Assicurati di inserire almeno 2 portieri (con 🥅) e 2 attaccanti (con ⚽).")
            else:
                db["portieri"] = portieri
                db["attaccanti"] = attaccanti
                db["stato"] = "gironi"
                
                # Generazione coppie reali con i nomi inseriti
                db["coda_partite"] = [
                    {
                        "squadra1": f"🥅 {portieri[0]} + ⚽ {attaccanti[0]}", 
                        "squadra2": f"🥅 {portieri[1]} + ⚽ {attaccanti[1]}"
                    }
                ]
                if len(portieri) > 2 and len(attaccanti) > 2:
                    db["coda_partite"].append({
                        "squadra1": f"🥅 {portieri[2]} + ⚽ {attaccanti[2]}", 
                        "squadra2": f"🥅 {portieri[min(3, len(portieri)-1)]} + ⚽ {attaccanti[min(3, len(attaccanti)-1)]}"
                    })
                
                db["tavoli_attivi"] = {}
                for i in range(1, db["num_tavoli"] + 1):
                    if db["coda_partite"]:
                        match = db["coda_partite"].pop(0)
                        db["tavoli_attivi"][str(i)] = match

                salva_dati(db)
                st.success("Torneo avviato con successo!")
                st.rerun()

# 2. GIRONI E TAVOLI IN LIVE
elif db["stato"] == "gironi":
    st.subheader("📊 Andamento Torneo in Diretta")
    
    st.markdown("### 🏟️ Stato Tavoli e Chiamate Attive")
    cols = st.columns(db["num_tavoli"])
    
    for i in range(1, db["num_tavoli"] + 1):
        tavolo_str = str(i)
        with cols[(i - 1) % len(cols)]:
            st.markdown(f"#### Tavolo {i}")
            if tavolo_str in db["tavoli_attivi"]:
                match = db["tavoli_attivi"][tavolo_str]
                st.info(f"🟢 **In Corso:**\n\n**{match['squadra1']}**\n\n*VS*\n\n**{match['squadra2']}**")
                
                if is_admin:
                    with st.form(key=f"form_tavolo_{i}"):
                        st.write("Inserisci Risultato:")
                        g1 = st.number_input("Gol Squadra 1", min_value=0, value=0, key=f"g1_{i}")
                        g2 = st.number_input("Gol Squadra 2", min_value=0, value=0, key=f"g2_{i}")
                        
                        submit = st.form_submit_button("🏁 Termina e Chiama Prossima")
                        if submit:
                            db["storico_partite"].append({"tavolo": i, "s1": match['squadra1'], "s2": match['squadra2'], "ris": f"{g1}-{g2}"})
                            
                            if db["coda_partite"]:
                                nuova_partita = db["coda_partite"].pop(0)
                                db["tavoli_attivi"][tavolo_str] = nuova_partita
                            else:
                                del db["tavoli_attivi"][tavolo_str]
                                
                            salva_dati(db)
                            st.success(f"Risultato registrato per il Tavolo {i}!")
                            st.rerun()
            else:
                st.success("✅ Tavolo Libero / In attesa.")

    st.markdown("---")
    
    st.markdown("### ⏳ Prossime Partite in Coda (Prepararsi ad andare al tavolo)")
    if db["coda_partite"]:
        for idx, m in enumerate(db["coda_partite"][:5]):
            st.warning(f"🔔 **In arrivo:** {m['squadra1']} **VS** {m['squadra2']} — *Preparatevi a breve!*")
    else:
        st.info("Nessuna altra partita in coda al momento.")

    st.markdown("---")
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        st.markdown("#### 🥅 Classifica Portieri")
        st.dataframe(pd.DataFrame({"Portiere": db["portieri"], "Punti": [0]*len(db["portieri"])}), use_container_width=True)
    with col_c2:
        st.markdown("#### ⚽ Classifica Attaccanti")
        st.dataframe(pd.DataFrame({"Attaccante": db["attaccanti"], "Punti": [0]*len(db["attaccanti"])}), use_container_width=True)

    # Pulsante Download Report in Testo/PDF
    st.markdown("---")
    report_text = "REPORT TORNEO BILIARDINO GIALLO\n\nPORTIERI:\n" + "\n".join(db["portieri"]) + "\n\nATTACCANTI:\n" + "\n".join(db["attaccanti"])
    st.download_button(
        label="📥 Scarica Riepilogo Torneo in PDF/File",
        data=report_text,
        file_name="riepilogo_torneo.txt",
        mime="text/plain"
    )

    if is_admin:
        st.markdown("---")
        if st.button("🏆 Passa alle Fasi Finali (Eliminazione Diretta)"):
            db["stato"] = "eliminatorie"
            salva_dati(db)
            st.rerun()

# 3. ELIMINATORIE
elif db["stato"] == "eliminatorie":
    st.subheader("🏆 Fasi Finali a Eliminazione Diretta")
    st.write("Tabellone protetto in corso...")
