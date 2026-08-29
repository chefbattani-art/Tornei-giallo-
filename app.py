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


# --- FUNZIONE GENERAZIONE CALENDARIO CON GESTIONE EQUA DELLA TALPA ---
def genera_calendario_con_talpa(portieri, attaccanti, num_turni, num_tavoli):
  p_list = list(portieri)
  a_list = list(attaccanti)

  # Se i portieri sono dispari, aggiungiamo la talpa
  usa_talpa_p = len(p_list) % 2 != 0
  if usa_talpa_p:
    p_list.append("⏳ [RIPOSO / TALPA]")

  # Se gli attaccanti sono dispari, aggiungiamo la talpa
  usa_talpa_a = len(a_list) % 2 != 0
  if usa_talpa_a:
    a_list.append("⏳ [RIPOSO / TALPA]")

  turni_partite = []

  for t in range(1, num_turni + 1):
    # Mescoliamo casualmente per mantenere lo spirito del sorteggio "Giallo"
    # ma facciamo ruotare i turni per equità
    p_curr = list(p_list)
    a_curr = list(a_list)

    # Spostamento ciclico basato sul turno per evitare ripetizioni fisse
    offset_p = (t - 1) % len(p_curr)
    p_curr = p_curr[offset_p:] + p_curr[:offset_p]

    offset_a = (t - 1) % len(a_curr)
    a_curr = a_curr[offset_a:] + a_curr[:offset_a]

    # Bilanciamo le liste se hanno lunghezze diverse
    max_len = max(len(p_curr), len(a_curr))
    while len(p_curr) < max_len:
      p_curr.append("⏳ [RIPOSO / TALPA]")
    while len(a_curr) < max_len:
      a_curr.append("⏳ [RIPOSO / TALPA]")

    partite_turno = []
    i = 0
    match_idx = 0

    while i + 1 < len(p_curr) and i + 1 < len(a_curr):
      p1, a1 = p_curr[i], a_curr[i]
      p2, a2 = p_curr[i + 1], a_curr[i + 1]

      # Verifichiamo se la partita coinvolge una Talpa (turno di riposo)
      contiene_talpa = (
          "TALPA" in str(p1)
          or "TALPA" in str(p2)
          or "TALPA" in str(a1)
          or "TALPA" in str(a2)
      )

      match_id = f"t{t}_m{match_idx}"
      partite_turno.append({
          "id": match_id,
          "p1": p1,
          "a1": a1,
          "p2": p2,
          "a2": a2,
          "giocata": contiene_talpa,  # Se c'è la talpa, viene segnata come gestita/saltata
          "in_corso": False,
          "gol1": 0,
          "gol2": 0,
          "con_talpa": contiene_talpa,
      })
      match_idx += 1
      i += 2

    turni_partite.append({"turno": t, "partite": partite_turno})

  return turni_partite


# --- FUNZIONI DI GESTIONE AVANZAMENTO FASI ---
def avvia_quarti():
  sorted_p_list = sorted(
      db["punti_portieri"].items(),
      key=lambda x: (x[1], db["dr_portieri"].get(x[0], 0)),
      reverse=True,
  )
  sorted_a_list = sorted(
      db["punti_attaccanti"].items(),
      key=lambda x: (x[1], db["dr_attaccanti"].get(x[0], 0)),
      reverse=True,
  )

  top_p = [p[0] for p in sorted_p_list[:8]]
  top_a = [a[0] for a in sorted_a_list[:8]]

  quarti_partite = [
      {
          "id": "ef_t1_m1",
          "p1": top_p[0],
          "a1": top_a[0],
          "p2": top_p[7],
          "a2": top_a[7],
          "giocata": False,
          "in_corso": False,
          "gol1": 0,
          "gol2": 0,
          "con_talpa": False,
      },
      {
          "id": "ef_t1_m2",
          "p1": top_p[1],
          "a1": top_a[1],
          "p2": top_p[6],
          "a2": top_a[6],
          "giocata": False,
          "in_corso": False,
          "gol1": 0,
          "gol2": 0,
          "con_talpa": False,
      },
      {
          "id": "ef_t1_m3",
          "p1": top_p[2],
          "a1": top_a[2],
          "p2": top_p[5],
          "a2": top_a[5],
          "giocata": False,
          "in_corso": False,
          "gol1": 0,
          "gol2": 0,
          "con_talpa": False,
      },
      {
          "id": "ef_t1_m4",
          "p1": top_p[3],
          "a1": top_a[3],
          "p2": top_p[4],
          "a2": top_a[4],
          "giocata": False,
          "in_corso": False,
          "gol1": 0,
          "gol2": 0,
          "con_talpa": False,
      },
  ]
  db["fasi_finali"] = [
      {"turno": 1, "nome": "Quarti di Finale", "partite": quarti_partite}
  ]
  db["stato"] = "eliminatorie"
  salva_dati(db)


def genera_semifinali():
  quarti = next(
      (f for f in db.get("fasi_finali", []) if f["nome"] == "Quarti di Finale"),
      None,
  )
  if quarti:
    vincitori = []
    for m in quarti["partite"]:
      if m.get("giocata", False):
        if m["gol1"] >= m["gol2"]:
          vincitori.append({"p": m["p1"], "a": m["a1"]})
        else:
          vincitori.append({"p": m["p2"], "a": m["a2"]})
    if len(vincitori) == 4:
      q1, q2, q3, q4 = vincitori[0], vincitori[1], vincitori[2], vincitori[3]
      semifinale_partite = [
          {
              "id": "ef_t2_m1",
              "p1": q1["p"],
              "a1": q2["a"],
              "p2": q3["p"],
              "a2": q4["a"],
              "giocata": False,
              "in_corso": False,
              "gol1": 0,
              "gol2": 0,
              "con_talpa": False,
          },
          {
              "id": "ef_t2_m2",
              "p1": q2["p"],
              "a1": q1["a"],
              "p2": q4["p"],
              "a2": q3["a"],
              "giocata": False,
              "in_corso": False,
              "gol1": 0,
              "gol2": 0,
              "con_talpa": False,
          },
      ]
      db["fasi_finali"].append(
          {"turno": 2, "nome": "Semifinali", "partite": semifinale_partite}
      )
      salva_dati(db)


def genera_finali():
  semifinali = next(
      (f for f in db.get("fasi_finali", []) if f["nome"] == "Semifinali"), None
  )
  if semifinali:
    vincitori = []
    perdenti = []
    for m in semifinali["partite"]:
      if m.get("giocata", False):
        if m["gol1"] >= m["gol2"]:
          vincitori.append({"p": m["p1"], "a": m["a1"]})
          perdenti.append({"p": m["p2"], "a": m["a2"]})
        else:
          vincitori.append({"p": m["p2"], "a": m["a2"]})
          perdenti.append({"p": m["p1"], "a": m["a1"]})
    if len(vincitori) == 2:
      sf1_v, sf2_v = vincitori[0], vincitori[1]
      sf1_p, sf2_p = perdenti[0], perdenti[1]
      finali_partite = [
          {
              "id": "ef_t3_m1",
              "p1": sf1_v["p"],
              "a1": sf2_v["a"],
              "p2": sf2_v["p"],
              "a2": sf1_v["a"],
              "giocata": False,
              "in_corso": False,
              "gol1": 0,
              "gol2": 0,
              "con_talpa": False,
          },
          {
              "id": "ef_t3_m2",
              "p1": sf1_p["p"],
              "a1": sf2_p["p"],
              "p2": sf2_p["p"],
              "a2": sf1_p["p"],
              "giocata": False,
              "in_corso": False,
              "gol1": 0,
              "gol2": 0,
              "con_talpa": False,
          },
      ]
      db["fasi_finali"].append({
          "turno": 3,
          "nome": "Finali (1°-2° e 3°-4° Posto)",
          "partite": finali_partite,
      })
      salva_dati(db)


# --- BARRA LATERALE ADMIN ---
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
    if st.sidebar.button(
        "🏆 Avvia Quarti di Finale", use_container_width=True, key="sb_quarti"
    ):
      avvia_quarti()
      st.rerun()
  elif db["stato"] == "eliminatorie":
    fasi_nomi = [f["nome"] for f in db.get("fasi_finali", [])]
    if "Quarti di Finale" in fasi_nomi and "Semifinali" not in fasi_nomi:
      quarti = next(
          f for f in db["fasi_finali"] if f["nome"] == "Quarti di Finale"
      )
      if all(m.get("giocata", False) for m in quarti["partite"]):
        if st.sidebar.button(
            "🚀 Genera Semifinali", use_container_width=True, key="sb_semi"
        ):
          genera_semifinali()
          st.rerun()
    if (
        "Semifinali" in fasi_nomi
        and "Finali (1°-2° e 3°-4° Posto)" not in fasi_nomi
    ):
      semi = next(f for f in db["fasi_finali"] if f["nome"] == "Semifinali")
      if all(m.get("giocata", False) for m in semi["partite"]):
        if st.sidebar.button(
            "🏁 Genera Finali", use_container_width=True, key="sb_finali"
        ):
          genera_finali()
          st.rerun()
    if st.sidebar.button(
        "⬅️ Indietro ai Gironi", use_container_width=True, key="sb_back_gironi"
    ):
      db["stato"] = "gironi"
      salva_dati(db)
      st.rerun()

# --- CSS PERSONALIZZATO ---
st.markdown(
    """
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
        }
        .live-match-box {
            background: linear-gradient(135deg, #0f172a, #172554);
            border: 2px solid #fbbf24;
            border-radius: 14px;
            padding: 12px 16px;
            margin-bottom: 12px;
        }
        .talpa-match-box {
            background: linear-gradient(135deg, #374151, #1f2937);
            border: 2px dashed #9ca3af;
            border-radius: 14px;
            padding: 12px 16px;
            margin-bottom: 12px;
            opacity: 0.85;
        }
    </style>
""",
    unsafe_allow_html=True,
)


def pulisci_nome(testo):
  testo = testo.replace("🥅", "").replace("🚪", "").replace("⚽", "")
  testo = re.sub(r"^\d+[\.\-\)]?\s*", "", testo)
  return testo.strip()


def ricalcola_classifiche():
  p_punti = {p: 0 for p in db["portieri"]}
  p_dr = {p: 0 for p in db["portieri"]}
  a_punti = {a: 0 for a in db["attaccanti"]}
  a_dr = {a: 0 for a in db["attaccanti"]}

  for turno_obj in db["turni_partite"]:
    for m in turno_obj["partite"]:
      if m.get("giocata", False) and not m.get("con_talpa", False):
        g1 = m["gol1"]
        g2 = m["gol2"]
        diff = abs(g1 - g2)

        if g1 > g2:
          pt_s1, pt_s2 = (3, 0) if diff >= 2 else (2, 1)
        elif g2 > g1:
          pt_s1, pt_s2 = (0, 3) if diff >= 2 else (1, 2)
        else:
          pt_s1, pt_s2 = 2, 2

        if m["a1"] in a_punti:
          a_punti[m["a1"]] += pt_s1
          a_dr[m["a1"]] += g1 - g2
        if m["a2"] in a_punti:
          a_punti[m["a2"]] += pt_s2
          a_dr[m["a2"]] += g2 - g1

        if m["p1"] in p_punti:
          p_punti[m["p1"]] += pt_s1
          p_dr[m["p1"]] += g1 - g2
        if m["p2"] in p_punti:
          p_punti[m["p2"]] += pt_s2
          p_dr[m["p2"]] += g2 - g1

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
      if ruolo == "portiere" and (m["p1"] == nome or m["p2"] == nome):
        is_presente = True
      elif ruolo == "attaccante" and (m["a1"] == nome or m["a2"] == nome):
        is_presente = True

      if is_presente:
        totali += 1
        if m.get("giocata", False) and not m.get("con_talpa", False):
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
    pdf.cell(0, 8, f"Turno {t_nome}", 0, 1, "L")
    pdf.set_font("Arial", "", 10)

    for idx, m in enumerate(turno_obj["partite"]):
      tavolo_num = (idx % num_tavoli) + 1
      if m.get("con_talpa", False):
        riga = f"  - Turno di Riposo (Talpa) in questo abbinamento: {m['p1']}/{m['a1']} vs {m['p2']}/{m['a2']}"
      else:
        risultato = (
            f"{m['gol1']} - {m['gol2']}"
            if m.get("giocata", False)
            else "Da giocare"
        )
        riga = f"  - Biliardino {tavolo_num}: {m['p1']}/{m['a1']} vs {m['p2']}/{m['a2']} -> {risultato}"

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

# --- HEADER COMUNE ---
st.html(
    """
    <div style="text-align: center; margin-bottom: 14px; background: linear-gradient(135deg, #080e1e, #0b1329); padding: 20px; border-radius: 20px; border: 2px solid #00f2fe;">
        <h1 style="margin: 0; color: #00f2fe; font-size: 1.8rem; font-weight: 800;">🏆 Torneo Biliardino 'Giallo' Live</h1>
    </div>
    """
)

tutti_i_giocatori = sorted(list(set(db["portieri"] + db["attaccanti"])))

if is_admin:
  giocatore_selezionato = "Admin"
elif db["stato"] != "setup" and tutti_i_giocatori:
  giocatore_url = st.query_params.get("giocatore", "")
  giocatore_selezionato = (
      giocatore_url
      if giocatore_url in tutti_i_giocatori
      else "-- Seleziona il tuo nome --"
  )

  if giocatore_selezionato == "-- Seleziona il tuo nome --":
    st.markdown("### 🔍 Seleziona il tuo nome per accedere:")
    scelta_utente = st.selectbox(
        "Il tuo nome:", ["-- Seleziona il tuo nome --"] + tutti_i_giocatori, index=0
    )
    if scelta_utente != "-- Seleziona il tuo nome --":
      st.query_params["giocatore"] = scelta_utente
      st.rerun()
    st.stop()
  else:
    col_n1, col_n2 = st.columns([3, 1])
    with col_n1:
      st.markdown(
          f"👤 Stai visualizzando come: **{giocatore_selezionato}**",
          unsafe_allow_html=True,
      )
    with col_n2:
      if st.button("🔄 Cambia Nome", use_container_width=True):
        st.query_params.clear()
        st.rerun()
    st.markdown("---")
else:
  giocatore_selezionato = "-- Seleziona il tuo nome --"

# 1. SETUP
if db["stato"] == "setup":
  st.subheader("1. Configurazione Iniziale del Torneo")
  if not is_admin:
    st.warning("Accedi come Admin dalla barra laterale per configurare.")
  else:
    whatsapp_text = st.text_area("Incolla qui la lista da WhatsApp:")
    col1, col2 = st.columns(2)
    with col1:
      db["num_tavoli"] = st.number_input(
          "Numero di biliardini", min_value=1, max_value=10, value=db["num_tavoli"]
      )
    with col2:
      db["partite_per_giocatore"] = st.number_input(
          "Turni / Partite garantite",
          min_value=1,
          max_value=10,
          value=db["partite_per_giocatore"],
      )
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
        db["turni_partite"] = genera_calendario_con_talpa(
            portieri, attaccanti, db["partite_per_giocatore"], db["num_tavoli"]
        )
        salva_dati(db)
        st.success("Torneo avviato con successo!")
        st.rerun()

# 2. GIRONI
if db["stato"] == "gironi":
  ricalcola_classifiche()
  num_tavoli = db.get("num_tavoli", 3)

  st.markdown("### 🔥 PARTITE ATTIVE:")
  for t_obj in db["turni_partite"]:
    for idx, m in enumerate(t_obj["partite"]):
      tavolo_num = (idx % num_tavoli) + 1
      if not m.get("giocata", False):
        if m.get("con_talpa", False):
          st.html(
              f"""
                    <div class="talpa-match-box">
                        <div style="font-weight: 700; color: #9ca3af;">⏳ TURNO DI RIPOSO (TALPA IN CORSO) - Turno {t_obj['turno']}</div>
                        <div>Giocatori a riposo/fittizi in questo slot: <b>{m['p1']} / {m['a1']} vs {m['p2']} / {m['a2']}</b></div>
                    </div>
                """
          )
        else:
          st.html(
              f"""
                    <div class="live-match-box">
                        <div style="font-weight: 700; color: #fbbf24;">🏟️ BILIARDINO {tavolo_num} (Turno {t_obj['turno']})</div>
                        <div>🥅 {m['p1']} / ⚽ {m['a1']} <b>VS</b> 🥅 {m['p2']} / ⚽ {m['a2']}</div>
                    </div>
                """
          )
          if (
              is_admin
              or giocatore_selezionato in [m["p1"], m["a1"], m["p2"], m["a2"]]
          ):
            with st.expander(f"Inserisci Risultato Biliardino {tavolo_num}"):
              g1 = st.number_input(
                  "Gol Coppia 1", 0, 10, int(m.get("gol1", 0)), key=f"g1_{m['id']}"
              )
              g2 = st.number_input(
                  "Gol Coppia 2", 0, 10, int(m.get("gol2", 0)), key=f"g2_{m['id']}"
              )
              if st.button("Salva Risultato", key=f"save_{m['id']}"):
                m["gol1"] = g1
                m["gol2"] = g2
                m["giocata"] = True
                ricalcola_classifiche()
                salva_dati(db)
                st.rerun()

  st.markdown("---")
  st.markdown("### 🏆 CLASSIFICHE IN TEMPO REALE")

  sorted_p = sorted(
      db["punti_portieri"].items(),
      key=lambda x: (x[1], db["dr_portieri"].get(x[0], 0)),
      reverse=True,
  )
  for idx, (p, pt) in enumerate(sorted_p):
    gioc, tot = calcola_partite_giocate("portiere", p)
    st.write(f"{idx+1}° 🥅 {p} - Punti: {pt} - Partite: {gioc}/{tot}")

  sorted_a = sorted(
      db["punti_attaccanti"].items(),
      key=lambda x: (x[1], db["dr_attaccanti"].get(x[0], 0)),
      reverse=True,
  )
  for idx, (a, pt) in enumerate(sorted_a):
    gioc, tot = calcola_partite_giocate("attaccante", a)
    st.write(f"{idx+1}° ⚽ {a} - Punti: {pt} - Partite: {gioc}/{tot}")
