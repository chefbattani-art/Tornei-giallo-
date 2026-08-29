from base64 import b64encode
from datetime import datetime, timedelta
from fpdf import FPDF
import json
import os
import random
import re
import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Torneo Biliardino 'Giallo' Live", layout="wide")

st_autorefresh(interval=5000, debounce=False, key="auto_refresh_torneo")

DB_FILE = "torneo_data.json"


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
      "fasi_finali": [],
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


def genera_calendario_corretto(portieri, attaccanti, num_turni, num_tavoli):
  p_list = list(portieri)
  a_list = list(attaccanti)

  turni_partite = []
  attaccanti_che_hanno_riposato_per_turno = {}
  
  compagni_precedenti = set()
  avversari_precedenti = set()

  for t in range(1, num_turni + 1):
    p_curr = list(p_list)
    a_curr = list(a_list)

    offset_p = (t - 1) % len(p_curr)
    p_curr = p_curr[offset_p:] + p_curr[:offset_p]

    idx_riposo_a = (t - 1) % len(a_curr)
    attaccante_in_riposo = a_curr.pop(idx_riposo_a)
    attaccanti_che_hanno_riposato_per_turno[t] = attaccante_in_riposo

    miglior_partite = []
    min_penalita = 999999

    for _ in range(300):
      a_temp = list(a_curr)
      random.shuffle(a_temp)
      
      partite_tentative = []
      penalita_tentativo = 0

      i = 0
      while i < len(p_curr) and i < len(a_temp):
        p1 = p_curr[i]
        a1 = a_temp[i]

        if i + 1 < len(p_curr) and i + 1 < len(a_temp):
          p2 = p_curr[i + 1]
          a2 = a_temp[i + 1]
        else:
          p2 = p_curr[(i + 1) % len(p_curr)]
          a2 = a_temp[(i + 1) % len(a_temp)]

        squadra_1 = tuple(sorted([p1, a1]))
        squadra_2 = tuple(sorted([p2, a2]))

        if squadra_1 in compagni_precedenti or squadra_2 in compagni_precedenti:
          penalita_tentativo += 10

        giocatori_s1 = [p1, a1]
        giocatori_s2 = [p2, a2]
        
        scontri_singoli = []
        for g_a in giocatori_s1:
          for g_b in giocatori_s2:
            coppia_avversaria = tuple(sorted([g_a, g_b]))
            if coppia_avversaria in avversari_precedenti:
              penalita_tentativo += 5
            scontri_singoli.append(coppia_avversaria)

        partite_tentative.append({
            "p1": p1, "a1": a1, "p2": p2, "a2": a2,
            "compagni": [squadra_1, squadra_2],
            "avversari": scontri_singoli
        })
        i += 2

      if penalita_tentativo < min_penalita:
        min_penalita = penalita_tentativo
        miglior_partite = partite_tentative
        if min_penalita == 0:
          break

    partite_turno = []
    for match_idx, m_data in enumerate(miglior_partite):
      for comp in m_data["compagni"]:
        compagni_precedenti.add(comp)
      for avv in m_data["avversari"]:
        avversari_precedenti.add(avv)

      match_id = f"t{t}_m{match_idx}"
      partite_turno.append({
          "id": match_id,
          "p1": m_data["p1"],
          "a1": m_data["a1"],
          "p2": m_data["p2"],
          "a2": m_data["a2"],
          "giocata": False,
          "in_corso": False,
          "gol1": 0,
          "gol2": 0,
      })

    partite_turno.append({
        "id": f"t{t}_riposo_a",
        "p1": "",
        "a1": attaccante_in_riposo,
        "p2": "",
        "a2": "",
        "giocata": True,
        "in_corso": False,
        "gol1": 0,
        "gol2": 0,
        "è_riposo_attaccante": True,
    })

    turni_partite.append({"turno": t, "partite": partite_turno})

  attaccanti_da_recuperare = list(attaccanti_che_hanno_riposato_per_turno.values())
  if len(attaccanti_da_recuperare) > 0:
    random.shuffle(attaccanti_da_recuperare)
    portieri_jolly = list(portieri)
    random.shuffle(portieri_jolly)

    turno_num = num_turni + 1
    partite_turno_extra = []
    match_idx = 0
    p_index = 0

    for i in range(0, len(attaccanti_da_recuperare), 2):
      if i + 1 < len(attaccanti_da_recuperare):
        a1 = attaccanti_da_recuperare[i]
        a2 = attaccanti_da_recuperare[i + 1]

        pj1 = portieri_jolly[p_index % len(portieri_jolly)]
        pj2 = portieri_jolly[(p_index + 1) % len(portieri_jolly)]
        p_index += 2

        match_id = f"t{turno_num}_m{match_idx}"
        partite_turno_extra.append({
            "id": match_id,
            "p1": f"{pj1} (Jolly)",
            "a1": a1,
            "p2": f"{pj2} (Jolly)",
            "a2": a2,
            "giocata": False,
            "in_corso": False,
            "gol1": 0,
            "gol2": 0,
            "è_extra_recupero": True,
        })
        match_idx += 1

    if len(attaccanti_da_recuperare) % 2 != 0:
      a_singolo = attaccanti_da_recuperare[-1]
      pj1 = portieri_jolly[p_index % len(portieri_jolly)]
      pj2 = portieri_jolly[(p_index + 1) % len(portieri_jolly)]
      match_id = f"t{turno_num}_m{match_idx}"
      partite_turno_extra.append({
          "id": match_id,
          "p1": f"{pj1} (Jolly)",
          "a1": a_singolo,
          "p2": f"{pj2} (Jolly)",
          "a2": "RIPOSO",
          "giocata": True,
          "in_corso": False,
          "gol1": 0,
          "gol2": 0,
          "è_extra_recupero": True,
      })

    if partite_turno_extra:
      turni_partite.append({"turno": turno_num, "partite": partite_turno_extra})

  return turni_partite


def avvia_quarti():
  sorted_p_list = sorted(db["punti_portieri"].items(), key=lambda x: (x[1], db["dr_portieri"].get(x[0], 0)), reverse=True)
  sorted_a_list = sorted(db["punti_attaccanti"].items(), key=lambda x: (x[1], db["dr_attaccanti"].get(x[0], 0)), reverse=True)

  top_p = [p[0] for p in sorted_p_list[:8]]
  top_a = [a[0] for a in sorted_a_list[:8]]

  quarti_partite = [
      {"id": "ef_t1_m1", "p1": top_p[0], "a1": top_a[0], "p2": top_p[7], "a2": top_a[7], "giocata": False, "in_corso": False, "gol1": 0, "gol2": 0},
      {"id": "ef_t1_m2", "p1": top_p[1], "a1": top_a[1], "p2": top_p[6], "a2": top_a[6], "giocata": False, "in_corso": False, "gol1": 0, "gol2": 0},
      {"id": "ef_t1_m3", "p1": top_p[2], "a1": top_a[2], "p2": top_p[5], "a2": top_a[5], "giocata": False, "in_corso": False, "gol1": 0, "gol2": 0},
      {"id": "ef_t1_m4", "p1": top_p[3], "a1": top_a[3], "p2": top_p[4], "a2": top_a[4], "giocata": False, "in_corso": False, "gol1": 0, "gol2": 0},
  ]
  db["fasi_finali"] = [{"turno": 1, "nome": "Quarti di Finale", "partite": quarti_partite}]
  db["stato"] = "eliminatorie"
  salva_dati(db)


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

if is_admin and db["stato"] != "setup":
  st.sidebar.markdown("---")
  st.sidebar.subheader("🕹️ Avanzamento Fasi")
  if db["stato"] == "gironi":
    if st.sidebar.button("🏆 Avvia Quarti di Finale", use_container_width=True, key="sb_quarti"):
      avvia_quarti()
      st.rerun()
  elif db["stato"] == "eliminatorie":
    if st.sidebar.button("⬅️ Indietro ai Gironi", use_container_width=True, key="sb_back_gironi"):
      db["stato"] = "gironi"
      salva_dati(db)
      st.rerun()

st.markdown("""
    <div style="text-align: center; margin-bottom: 14px; background: linear-gradient(135deg, #080e1e, #0b1329); padding: 20px; border-radius: 20px; border: 2px solid #00f2fe;">
        <h1 style="margin: 0; color: #00f2fe; font-size: 1.8rem; font-weight: 800;">🏆 Torneo Biliardino 'Giallo' Live</h1>
    </div>
""", unsafe_allow_html=True)

tutti_i_giocatori = sorted(list(set(db["portieri"] + db["attaccanti"])))

def pulisci_nome(testo):
  testo = testo.replace("🥅", "").replace("🚪", "").replace("⚽", "").replace("⏳", "").replace("[RIPOSO]", "").replace("(Jolly)", "")
  return testo.strip()


def ricalcola_classifiche():
  p_punti = {p: 0 for p in db["portieri"]}
  p_dr = {p: 0 for p in db["portieri"]}
  a_punti = {a: 0 for a in db["attaccanti"]}
  a_dr = {a: 0 for a in db["attaccanti"]}

  for turno_obj in db["turni_partite"]:
    for m in turno_obj["partite"]:
      if m.get("giocata", False) and not m.get("è_riposo_attaccante", False):
        g1 = m["gol1"]
        g2 = m["gol2"]
        diff = abs(g1 - g2)

        if g1 > g2:
          pt_s1, pt_s2 = (3, 0) if diff >= 2 else (2, 1)
        elif g2 > g1:
          pt_s1, pt_s2 = (0, 3) if diff >= 2 else (1, 2)
        else:
          pt_s1, pt_s2 = 2, 2

        is_extra = m.get("è_extra_recupero", False)

        if m["a1"] in a_punti:
          a_punti[m["a1"]] += pt_s1
          a_dr[m["a1"]] += g1 - g2
        if m["a2"] in a_punti:
          a_punti[m["a2"]] += pt_s2
          a_dr[m["a2"]] += g2 - g1

        if not is_extra:
          p1_pulito = pulisci_nome(m["p1"])
          p2_pulito = pulisci_nome(m["p2"])
          if p1_pulito in p_punti:
            p_punti[p1_pulito] += pt_s1
            p_dr[p1_pulito] += g1 - g2
          if p2_pulito in p_punti:
            p_punti[p2_pulito] += pt_s2
            p_dr[p2_pulito] += g2 - g1

  db["punti_portieri"] = p_punti
  db["dr_portieri"] = p_dr
  db["punti_attaccanti"] = a_punti
  db["dr_attaccanti"] = a_dr


def calcola_partite_giocate(ruolo, nome):
  giocate = 0
  totali = 0
  for turno_obj in db["turni_partite"]:
    for m in turno_obj["partite"]:
      if m.get("è_riposo_attaccante", False):
        if ruolo == "attaccante" and m["a1"] == nome:
          totali += 1
        continue

      is_presente = False
      if ruolo == "portiere":
        p1_pulito = pulisci_nome(m["p1"])
        p2_pulito = pulisci_nome(m["p2"])
        if (p1_pulito == nome or p2_pulito == nome) and not m.get("è_extra_recupero", False):
          is_presente = True
      elif ruolo == "attaccante":
        if m["a1"] == nome or m["a2"] == nome:
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
    t_nome = turno_obj["turno"]
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, f"Turno {t_nome}" + (" (Turno Extra Recupero Attaccanti)" if t_nome > db.get("partite_per_giocatore", 6) else ""), 0, 1, "L")
    pdf.set_font("Arial", "", 10)

    for idx, m in enumerate(turno_obj["partite"]):
      if m.get("è_riposo_attaccante", False):
        riga = f"  - Riposa ATT: {m['a1']}"
      else:
        tavolo_num = (idx % num_tavoli) + 1
        risultato = f"{m['gol1']} - {m['gol2']}" if m.get("giocata", False) else "Da giocare"
        riga = f"  - Biliardino {tavolo_num}: {m['p1']} e {m['a1']} vs {m['p2']} e {m['a2']} -> {risultato}"

      riga_pulita = riga.encode("latin-1", "ignore").decode("latin-1")
      pdf.cell(0, 6, riga_pulita, 0, 1, "L")
    pdf.ln(3)

  return bytes(pdf.output())


if is_admin:
  st.sidebar.markdown("---")
  if st.sidebar.button("⚠️ Azzera e Ricomincia", use_container_width=True):
    if os.path.exists(DB_FILE):
      os.remove(DB_FILE)
    for key in list(st.session_state.keys()):
      del st.session_state[key]
    st.query_params.clear()
    st.rerun()

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&display=swap');
        html { scroll-behavior: smooth; }
        [data-testid="stAppViewContainer"] { overflow-anchor: none; }
        :root { color-scheme: dark; }
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
        }
        button[data-testid="stBaseButton-secondary"], div.stButton > button {
            background: linear-gradient(135deg, #0f172a, #1e293b) !important;
            color: #38bdf8 !important;
            border: 1px solid #00f2fe !important;
            border-radius: 10px !important;
            font-weight: 700 !important;
            font-size: 1.1rem !important;
            height: 48px !important;
        }
        .live-match-box {
            background: linear-gradient(135deg, #0f172a, #172554);
            border: 2px solid #fbbf24;
            border-radius: 14px;
            padding: 14px 16px;
            margin-bottom: 12px;
            text-align: center;
        }
        .extra-match-box {
            background: linear-gradient(135deg, #1e1b4b, #311042);
            border: 2px solid #a855f7;
            border-radius: 14px;
            padding: 14px 16px;
            margin-bottom: 12px;
            text-align: center;
        }
        .talpa-match-box {
            background: linear-gradient(135deg, #374151, #1f2937);
            border: 2px dashed #9ca3af;
            border-radius: 14px;
            padding: 12px 16px;
            margin-bottom: 12px;
            opacity: 0.9;
            text-align: center;
        }
        .team-section {
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid #334155;
            padding: 10px;
            border-radius: 8px;
            margin-bottom: 6px;
            text-align: center;
        }
    </style>
""", unsafe_allow_html=True)

# 1. SETUP
if db["stato"] == "setup":
  st.subheader("1. Configurazione Iniziale del Torneo")
  if not is_admin:
    st.warning("Accedi come Admin dalla barra laterale per configurare.")
  else:
    whatsapp_text = st.text_area("Incolla qui la lista da WhatsApp:")
    col1, col2 = st.columns(2)
    with col1:
      db["num_tavoli"] = st.number_input("Numero di biliardini", min_value=1, max_value=10, value=db["num_tavoli"])
    with col2:
      db["partite_per_giocatore"] = st.number_input("Turni / Partite garantite", min_value=1, max_value=10, value=db["partite_per_giocatore"])
    db["admin_pin"] = st.text_input("PIN Admin", value=db["admin_pin"])

    if st.button("🚀 Avvia il Torneo e Genera Calendario"):
      portieri, attaccanti = [], []
      for line in whatsapp_text.split("\n"):
        if "🥅" in line or "🚪" in line:
          n = pulisci_nome(line)
          if n:
            portieri.append(n)
        elif "⚽" in line:
          n = pulisci_nome(line)
          if n:
            attaccanti.append(n)

      if len(portieri) < 2 or len(attaccanti) < 2:
        st.error("Inserisci almeno 2 portieri e 2 attaccanti.")
      else:
        db["portieri"] = portieri
        db["attaccanti"] = attaccanti
        db["punti_portieri"] = {p: 0 for p in portieri}
        db["dr_portieri"] = {p: 0 for p in portieri}
        db["punti_attaccanti"] = {a: 0 for a in attaccanti}
        db["dr_attaccanti"] = {a: 0 for a in attaccanti}
        db["stato"] = "gironi"
        db["turni_partite"] = genera_calendario_corretto(portieri, attaccanti, db["partite_per_giocatore"], db["num_tavoli"])
        salva_dati(db)
        st.success("Torneo avviato con successo!")
        st.rerun()

# 2. GIRONI
if db["stato"] == "gironi":
  ricalcola_classifiche()
  num_tavoli = db.get("num_tavoli", 3)

  if db["turni_partite"]:
    pdf_bytes = genera_pdf_calendario()
    st.download_button(
        label="📥 Scarica Calendario PDF",
        data=pdf_bytes,
        file_name="calendario_torneo.pdf",
        mime="application/pdf",
        use_container_width=True,
    )
    st.markdown("---")

  st.markdown("### 🔥 PARTITE E TURNI:")
  for t_obj in db["turni_partite"]:
    is_extra = t_obj["turno"] > db.get("partite_per_giocatore", 6)
    titolo_turno = f"📌 Turno {t_obj['turno']} (Turno Extra Recupero Attaccanti)" if is_extra else f"📌 Turno {t_obj['turno']}"
    st.markdown(f"#### {titolo_turno}")

    for idx, m in enumerate(t_obj["partite"]):
      if m.get("è_riposo_attaccante", False):
        st.markdown(f"""
            <div class="talpa-match-box">
                <div style="font-weight: 700; color: #9ca3af;">⏳ RIPOSO ATTACCANTE</div>
                <div><b>Riposa ATT: {m['a1']}</b></div>
            </div>
        """, unsafe_allow_html=True)
      elif m.get("è_extra_recupero", False):
        tavolo_num = (idx % num_tavoli) + 1
        testo_risultato = "⏳ <b>Da giocare</b>"
        if m.get("giocata", False):
          testo_risultato = f"✅ Risultato: <b>{m['gol1']} - {m['gol2']}</b>"

        st.markdown(f"""
            <div class="extra-match-box">
                <div style="font-weight: 700; color: #a855f7; margin-bottom: 4px;">🔄 RECUPERO ATTACCANTI (Tavolo {tavolo_num})</div>
                <div style="font-size: 1.15rem; font-weight: 700; color: #f8fafc; margin: 6px 0;">
                    {m['p1']} e {m['a1']} <span style="color:#a855f7; font-weight:400;">VS</span> {m['p2']} e {m['a2']}
                </div>
                <div style="font-size:0.85rem; color:#d8b4fe; margin-bottom: 6px;">(Portieri Jolly - Non prendono punti)</div>
                <div style="font-size: 1.05rem;">{testo_risultato}</div>
            </div>
        """, unsafe_allow_html=True)
        
        exp_key_open = f"exp_open_rec_{m['id']}"
        if exp_key_open not in st.session_state:
          st.session_state[exp_key_open] = False

        with st.expander(f"⚙️ Inserisci Risultato Tavolo {tavolo_num} (Turno {t_obj['turno']})", expanded=st.session_state[exp_key_open]):
          with st.form(key=f"form_rec_{m['id']}"):
            st.write("Inserisci i goal assegnati a ciascuna squadra:")
            
            curr_g1 = int(m.get("gol1", 0))
            curr_g2 = int(m.get("gol2", 0))
            
            st.markdown(f'<div class="team-section"><b>🥅 Coppia 1: {m["p1"]} & {m["a1"]}</b></div>', unsafe_allow_html=True)
            col_g1_1, col_g1_2 = st.columns(2)
            with col_g1_1:
                g1_sup = st.radio("C1_s", [0, 1, 2, 3], index=curr_g1 if curr_g1 <= 3 else 0, horizontal=True, key=f"r_rec_g1_s_{m['id']}", label_visibility="collapsed")
            with col_g1_2:
                g1_inf = st.radio("C1_i", [4, 5, 6, 7], index=(curr_g1 - 4) if curr_g1 >= 4 else 0, horizontal=True, key=f"r_rec_g1_i_{m['id']}", label_visibility="collapsed")
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(f'<div class="team-section"><b>🥅 Coppia 2: {m["p2"]} & {m["a2"]}</b></div>', unsafe_allow_html=True)
            col_g2_1, col_g2_2 = st.columns(2)
            with col_g2_1:
                g2_sup = st.radio("C2_s", [0, 1, 2, 3], index=curr_g2 if curr_g2 <= 3 else 0, horizontal=True, key=f"r_rec_g2_s_{m['id']}", label_visibility="collapsed")
            with col_g2_2:
                g2_inf = st.radio("C2_i", [4, 5, 6, 7], index=(curr_g2 - 4) if curr_g2 >= 4 else 0, horizontal=True, key=f"r_rec_g2_i_{m['id']}", label_visibility="collapsed")
            
            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button("Salva Risultato", use_container_width=True)
            if submitted:
              r_s1 = st.session_state.get(f"r_rec_g1_s_{m['id']}", 0)
              r_i1 = st.session_state.get(f"r_rec_g1_i_{m['id']}", 4)
              m["gol1"] = r_i1 if curr_g1 >= 4 else r_s1
              
              r_s2 = st.session_state.get(f"r_rec_g2_s_{m['id']}", 0)
              r_i2 = st.session_state.get(f"r_rec_g2_i_{m['id']}", 4)
              m["gol2"] = r_i2 if curr_g2 >= 4 else r_s2
              
              m["giocata"] = True
              ricalcola_classifiche()
              salva_dati(db)
              st.session_state[exp_key_open] = False
              st.rerun()
      else:
        tavolo_num = (idx % num_tavoli) + 1
        testo_risultato = "⏳ <b>Da giocare</b>"
        if m.get("giocata", False):
          testo_risultato = f"✅ Risultato: <b>{m['gol1']} - {m['gol2']}</b>"

        st.markdown(f"""
            <div class="live-match-box">
                <div style="font-weight: 700; color: #fbbf24; margin-bottom: 4px;">🏟️ BILIARDINO {tavolo_num}</div>
                <div style="font-size: 1.2rem; font-weight: 700; color: #f8fafc; margin: 6px 0;">
                    {m['p1']} e {m['a1']} <span style="color:#fbbf24; font-weight:400;">VS</span> {m['p2']} e {m['a2']}
                </div>
                <div style="font-size: 1.1rem; margin-top: 8px;">{testo_risultato}</div>
            </div>
        """, unsafe_allow_html=True)
        
        exp_key_open = f"exp_open_{m['id']}"
        if exp_key_open not in st.session_state:
          st.session_state[exp_key_open] = False

        with st.expander(f"⚙️ Inserisci Risultato Biliardino {tavolo_num} (Turno {t_obj['turno']})", expanded=st.session_state[exp_key_open]):
          with st.form(key=f"form_{m['id']}"):
            st.write("Inserisci i goal assegnati a ciascuna squadra:")
            
            curr_g1 = int(m.get("gol1", 0))
            curr_g2 = int(m.get("gol2", 0))
            
            st.markdown(f'<div class="team-section"><b>🥅 Coppia 1: {m["p1"]} & {m["a1"]}</b></div>', unsafe_allow_html=True)
            col_g1_1, col_g1_2 = st.columns(2)
            with col_g1_1:
                g1_sup = st.radio("C1_s", [0, 1, 2, 3], index=curr_g1 if curr_g1 <= 3 else 0, horizontal=True, key=f"r_g1_s_{m['id']}", label_visibility="collapsed")
            with col_g1_2:
                g1_inf = st.radio("C1_i", [4, 5, 6, 7], index=(curr_g1 - 4) if curr_g1 >= 4 else 0, horizontal=True, key=f"r_g1_i_{m['id']}", label_visibility="collapsed")
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(f'<div class="team-section"><b>🥅 Coppia 2: {m["p2"]} & {m["a2"]}</b></div>', unsafe_allow_html=True)
            col_g2_1, col_g2_2 = st.columns(2)
            with col_g2_1:
                g2_sup = st.radio("C2_s", [0, 1, 2, 3], index=curr_g2 if curr_g2 <= 3 else 0, horizontal=True, key=f"r_g2_s_{m['id']}", label_visibility="collapsed")
            with col_g2_2:
                g2_inf = st.radio("C2_i", [4, 5, 6, 7], index=(curr_g2 - 4) if curr_g2 >= 4 else 0, horizontal=True, key=f"r_g2_i_{m['id']}", label_visibility="collapsed")
            
            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button("Salva Risultato", use_container_width=True)
            if submitted:
              r_s1 = st.session_state.get(f"r_g1_s_{m['id']}", 0)
              r_i1 = st.session_state.get(f"r_g1_i_{m['id']}", 4)
              m["gol1"] = r_i1 if curr_g1 >= 4 else r_s1
              
              r_s2 = st.session_state.get(f"r_g2_s_{m['id']}", 0)
              r_i2 = st.session_state.get(f"r_g2_i_{m['id']}", 4)
              m["gol2"] = r_i2 if curr_g2 >= 4 else r_s2
              
              m["giocata"] = True
              ricalcola_classifiche()
              salva_dati(db)
              st.session_state[exp_key_open] = False
              st.rerun()

  st.markdown("---")
  st.markdown("### 🏆 CLASSIFICHE IN TEMPO REALE")

  sorted_p = sorted(db["punti_portieri"].items(), key=lambda x: (x[1], db["dr_portieri"].get(x[0], 0)), reverse=True)
  for idx, (p, pt) in enumerate(sorted_p):
    gioc, tot = calcola_partite_giocate("portiere", p)
    st.write(f"{idx+1}° 🥅 {p} - Punti: {pt} - Partite: {gioc}")

  sorted_a = sorted(db["punti_attaccanti"].items(), key=lambda x: (x[1], db["dr_attaccanti"].get(x[0], 0)), reverse=True)
  for idx, (a, pt) in enumerate(sorted_a):
    gioc, tot = calcola_partite_giocate("attaccante", a)
    st.write(f"{idx+1}° ⚽ {a} - Punti: {pt} - Partite: {gioc}")
