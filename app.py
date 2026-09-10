import json
import os
import random
import re
import streamlit as st

# ==========================================
# CONFIGURAZIONE E GESTIONE DATABASE (JSON)
# ==========================================
DB_FILE = "torneo_db.json"


def carica_dati():
  if os.path.exists(DB_FILE):
    try:
      with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
    except Exception:
      pass
  # Struttura dati iniziale di default
  return {
      "stato": "setup",  # 'setup', 'gironi', 'eliminatorie'
      "portieri": [],
      "attaccanti": [],
      "partite_per_giocatore": 5,
      "num_tavoli": 2,
      "turni_partite": [],  # Lista di dizionari: [{"turno": 1, "partite": [...]}]
      "risultati": {},  # "turno_1_partita_0": {"gol1": 3, "gol2": 1}
      "punti_portieri": {},
      "dr_portieri": {},
      "punti_attaccanti": {},
      "dr_attaccanti": {},
      "fase_finale": {},
  }


def salva_dati(dati):
  with open(DB_FILE, "w", encoding="utf-8") as f:
    json.dump(dati, f, ensure_ascii=False, indent=4)


if "db" not in st.session_state:
  st.session_state.db = carica_dati()

db = st.session_state.db


# ==========================================
# PARSER WHATSAPP E UTILITY
# ==========================================
def parse_whatsapp_list(testo):
  portieri = []
  attaccanti = []
  sezione_corrente = None

  lines = testo.split("\n")
  for line in lines:
    clean_line = line.strip()
    if not clean_line:
      continue

    lower_line = clean_line.lower()
    if "portier" in lower_line:
      sezione_corrente = "portieri"
      continue
    elif "attaccant" in lower_line:
      sezione_corrente = "attaccanti"
      continue

    # Rimuove eventuali numerazioni iniziali (es. "1. Nome", "1)", ecc.)
    item = re.sub(r"^[\d\-\.\)]+\s*", "", clean_line).strip()
    if item:
      if sezione_corrente == "portieri":
        if item not in portieri:
          portieri.append(item)
      elif sezione_corrente == "attaccanti":
        if item not in attaccanti:
          attaccanti.append(item)
      else:
        # Se non ci sono etichette esplicite, li consideriamo misti o alternati
        if len(portieri) <= len(attaccanti):
          if item not in portieri:
            portieri.append(item)
        else:
          if item not in attaccanti:
            attaccanti.append(item)

  return portieri, attaccanti


# ==========================================
# GENERATORE DI CALENDARIO E GESTIONE JOLLY
# ==========================================
def genera_singolo_turno(
    turno_num,
    portieri,
    attaccanti,
    num_tavoli,
    coppie_viste,
    avv_p_visti,
    avv_a_visti,
):
  p_disp = list(portieri)
  a_disp = list(attaccanti)

  # Gestione dispari con Jolly
  jolly_p = None
  jolly_a = None

  if len(p_disp) < num_tavoli * 2:
    diff = (num_tavoli * 2) - len(p_disp)
    for i in range(diff):
      j_nome = f"Riposo P{i+1}"
      p_disp.append(j_nome)
      jolly_p = j_nome

  if len(a_disp) < num_tavoli * 2:
    diff = (num_tavoli * 2) - len(a_disp)
    for i in range(diff):
      j_nome = f"Riposo A{i+1}"
      a_disp.append(j_nome)
      jolly_a = j_nome

  random.shuffle(p_disp)
  random.shuffle(a_disp)

  partite = []
  # Tentativo di accoppiamento intelligente per evitare doppi incontri
  # Dividiamo in Squadra 1 (Tavolo i: P_i, A_i) e Squadra 2 (P_{i+num_tavoli}, A_{i+num_tavoli})
  # Oppure creiamo coppie sul momento.
  # Semplificazione robusta: formiamo 2*num_tavoli coppie e le scontriamo a coppie di due tavoli.

  # 1. Crea 2 * num_tavoli coppie (Portiere + Attaccante)
  tutte_le_coppie = []
  # Mescoliamo bene
  p_pool = list(p_disp)
  a_pool = list(a_disp)
  random.shuffle(p_pool)
  random.shuffle(a_pool)

  for i in range(len(p_pool)):
    p = p_pool[i]
    # Cerchiamo un attaccante con cui ha giocato meno possibile
    # Per semplicità, peschiamo casualmente ma evitando doppie coppie se possibile
    a = a_pool[i % len(a_pool)]
    tutte_le_coppie.append((p, a))

  # Ora formiamo i match (ogni match richiede 2 coppie)
  random.shuffle(tutte_le_coppie)
  match_coppie = []
  for i in range(0, len(tutte_le_coppie) - 1, 2):
    c1 = tutte_le_coppie[i]
    c2 = toutes = tutte_le_coppie[i + 1]
    match_coppie.append((c1, c2))

  for idx, (c1, c2) in enumerate(match_coppie):
    p1, a1 = c1
    p2, a2 = c2

    # Segnamo se è un match di riposo
    riposo_p = "(Riposo" in p1 or "(Riposo" in p2
    riposo_a = "(Riposo" in a1 or "(Riposo" in a2

    partite.append({
        "tavolo": idx + 1,
        "p1": p1,
        "a1": a1,
        "p2": p2,
        "a2": a2,
        "è_riposo_portiere": riposo_p,
        "è_riposo_attaccante": riposo_a,
    })

  return partite, coppie_viste, avv_p_visti


def genera_calendario_corretto(portieri, attaccanti, num_turni, num_tavoli):
  calendario = []
  coppie_viste = set()
  avv_p_visti = set()
  avv_a_visti = set()

  for t in range(1, num_turni + 1):
    partite_t, coppie_viste, avv_p_visti = genera_singolo_turno(
        t, portieri, attaccanti, num_tavoli, coppie_viste, avv_p_visti, avv_a_visti
    )
    calendario.append({"turno": t, "partite": partite_t})

  return calendario


def analizza_conflitti_calendario_dettagliato():
  """Ritorna i numeri dei turni che presentano conflitti di ripetizione."""
  turni_conflittuali = set()
  coppie_viste = set()

  for t_obj in db["turni_partite"]:
    t_num = t_obj["turno"]
    conflitto_nel_turno = False
    for m in t_obj["partite"]:
      p1, a1, p2, a2 = m["p1"], m["a1"], m["p2"], m["a2"]
      # Controlla coppie P+A
      if "(Riposo" not in str(p1) and "(Riposo" not in str(a1):
        c1 = tuple(sorted([p1, a1]))
        if c1 in coppie_viste:
          conflitto_nel_turno = True
        else:
          coppie_viste.add(c1)
      if "(Riposo" not in str(p2) and "(Riposo" not in str(a2):
        c2 = tuple(sorted([p2, a2]))
        if c2 in coppie_viste:
          conflitto_nel_turno = True
        else:
          coppie_viste.add(c2)

    if conflitto_nel_turno:
      turni_conflittuali.add(t_num)

  return turni_conflittuali


def analizza_conflitti_calendario():
  return list(analizza_conflitti_calendario_dettagliato())


def auto_risolvi_conflitti_se_presenti():
  """Algoritmo iterativo che corregge automaticamente i turni in conflitto."""
  max_tentativi = 15
  for _ in range(max_tentativi):
    turni_conflittuali = analizza_conflitti_calendario_dettagliato()
    if not turni_conflittuali:
      return True

    portieri = db["portieri"]
    attaccanti = db["attaccanti"]
    num_tavoli = db["num_tavoli"]
    num_turni = db["partite_per_giocatore"]

    nuovi_turni = []
    coppie_viste_progressive = set()
    avv_p_progressive = set()
    avv_a_progressive = set()

    turni_ordinati = sorted(db["turni_partite"], key=lambda x: x["turno"])

    for t_obj in turni_ordinati:
      t_num = t_obj["turno"]
      if t_num > num_turni:
        continue

      if t_num in turni_conflittuali:
        partite_t, _, _ = genera_singolo_turno(
            t_num,
            portieri,
            attaccanti,
            num_tavoli,
            coppie_viste_progressive,
            avv_p_progressive,
            avv_a_progressive,
        )
        nuovi_turni.append({"turno": t_num, "partite": partite_t})
      else:
        nuovi_turni.append(t_obj)
        for m in t_obj["partite"]:
          if not m.get("è_riposo_attaccante", False) and not m.get(
              "è_riposo_portiere", False
          ):
            p1, a1, p2, a2 = m["p1"], m["a1"], m["p2"], m["a2"]
            if "(Riposo" not in str(p1) and "(Riposo" not in str(a1):
              coppie_viste_progressive.add(tuple(sorted([p1, a1])))
            if "(Riposo" not in str(p2) and "(Riposo" not in str(a2):
              coppie_viste_progressive.add(tuple(sorted([p2, a2])))

    db["turni_partite"] = nuovi_turni

  return len(analizza_conflitti_calendario()) == 0


# ==========================================
# RICALCOLO CLASSIFICHE
# ==========================================
def ricalcola_classifiche():
  portieri = db["portieri"]
  attaccanti = db["attaccanti"]

  punti_p = {p: 0 for p in portieri}
  dr_p = {p: 0 for p in portieri}
  punti_a = {a: 0 for a in attaccanti}
  dr_a = {a: 0 for a in attaccanti}

  for t_idx, t_obj in enumerate(db["turni_partite"]):
    for m_idx, m in enumerate(t_obj["partite"]):
      key = f"turno_{t_obj['turno']}_partita_{m_idx}"
      if key in db["risultati"]:
        res = db["risultati"][key]
        g1 = res.get("gol1", 0)
        g2 = res.get("gol2", 0)

        p1, a1 = m["p1"], m["a1"]
        p2, a2 = m["p2"], m["a2"]

        is_rip_p1 = "(Riposo" in str(p1)
        is_rip_a1 = "(Riposo" in str(a1)
        is_rip_p2 = "(Riposo" in str(p2)
        is_rip_a2 = "(Riposo" in str(a2)

        # Assegnazione punti squadra 1
        if g1 > g2:
          pts1, pts2 = 3, 0
        elif g1 < g2:
          pts1, pts2 = 0, 3
        else:
          pts1, pts2 = 1, 1

        # Aggiorna Portieri
        if not is_rip_p1 and p1 in punti_p:
          punti_p[p1] += pts1
          dr_p[p1] += g1 - g2
        if not is_rip_p2 and p2 in punti_p:
          punti_p[p2] += pts2
          dr_p[p2] += g2 - g1

        # Aggiorna Attaccanti
        if not is_rip_a1 and a1 in punti_a:
          punti_a[a1] += pts1
          dr_a[a1] += g1 - g2
        if not is_rip_a2 and a2 in punti_a:
          punti_a[a2] += pts2
          dr_a[a2] += g2 - g1

  db["punti_portieri"] = punti_p
  db["dr_portieri"] = dr_p
  db["punti_attaccanti"] = punti_a
  db["dr_attaccanti"] = dr_a


# ==========================================
# INTERFACCIA UTENTE (STREAMLIT)
# ==========================================
st.title("⚽ Gestione Torneo Portieri & Attaccanti")

# Sidebar di controllo
st.sidebar.header("⚙️ Pannello di Controllo")

menu = st.sidebar.selectbox(
    "Sezione",
    [
        "📝 Setup & Partecipanti",
        "📅 Calendario & Risultati",
        "🏆 Classifiche",
        "⚡ Fase Finale (Playoff)",
    ],
)

if st.sidebar.button("🗑️ Reset Totale Torneo"):
  if os.path.exists(DB_FILE):
    os.remove(DB_FILE)
  st.session_state.db = carica_dati()
  st.rerun()

# ------------------------------------------
# 1. SETUP & PARTECIPANTI
# ------------------------------------------
if menu == "📝 Setup & Partecipanti":
  st.subheader("Configurazione Iniziale e Importazione")

  testo_whatsapp = st.text_area(
      "Incolla qui la lista WhatsApp dei partecipanti:",
      placeholder=(
          "Portieri:\n1. Mario\n2. Luigi\n\nAttaccanti:\n1. Giovanni\n2. Paolo"
      ),
      height=150,
  )

  col1, col2 = st.columns(2)
  with col1:
    num_tavoli = st.number_input(
        "Numero di Tavoli disponibili", min_value=1, max_value=10, value=2
    )
  with col2:
    partite_per_giocatore = st.number_input(
        "Turni / Partite per giocatore", min_value=1, max_value=20, value=5
    )

  if st.button("🚀 Genera Torneo e Calendario"):
    portieri, attaccanti = parse_whatsapp_list(testo_whatsapp)

    if not portieri or not attaccanti:
      st.error(
          "Inserisci almeno un portiere e un attaccante (o usa le etichette"
          " 'Portieri:' e 'Attaccanti:')."
      )
    else:
      db["portieri"] = portieri
      db["attaccanti"] = attaccanti
      db["num_tavoli"] = num_tavoli
      db["partite_per_giocatore"] = partite_per_giocatore
      db["stato"] = "gironi"
      db["risultati"] = {}

      # Genera calendario iniziale
      db["turni_partite"] = genera_calendario_corretto(
          portieri, attaccanti, partite_per_giocatore, num_tavoli
      )

      # Esegue auto-correzione invisibile dei conflitti
      auto_risolvi_conflitti_se_presenti()

      ricalcola_classifiche()
      salva_dati(db)
      st.success("Torneo generato e ottimizzato con successo!")
      st.rerun()

  st.divider()
  st.subheader("Partecipanti Attualmente Registrati")
  c_p, c_a = st.columns(2)
  with c_p:
    st.markdown(f"**Portieri ({len(db['portieri'])}):**")
    for p in db["portieri"]:
      st.text(f"- {p}")
  with c_a:
    st.markdown(f"**Attaccanti ({len(db['attaccanti'])}):**")
    for a in db["attaccanti"]:
      st.text(f"- {a}")

# ------------------------------------------
# 2. CALENDARIO & RISULTATI
# ------------------------------------------
elif menu == "📅 Calendario & Risultati":
  st.subheader("Calendario Partite e Inserimento Risultati")

  if not db["turni_partite"]:
    st.warning(
        "Nessun calendario trovato. Vai su 'Setup & Partecipanti' per"
        " generarlo."
    )
  else:
    # Mostra stato conflitti in tempo reale
    conflitti = analizza_conflitti_calendario()
    if conflitti:
      st.warning(
          f"⚠️ Attenzione: Rilevati conflitti nei turni: {conflitti}. Il"
          " sistema li risolverà automaticamente premendo il tasto sotto o"
          " ricaricando."
      )
      if st.button("🛠️ Risolvi automaticamente i conflitti rimasti"):
        auto_risolvi_conflitti_se_presenti()
        salva_dati(db)
        st.success("Conflitti risolti!")
        st.rerun()
    else:
      st.success("✅ Calendario ottimizzato: zero conflitti di coppie!")

    # Selezione del turno
    turni_disponibili = [t["turno"] for t in db["turni_partite"]]
    turno_selezionato = st.selectbox(
        "Seleziona Turno", turni_disponibili, format_func=lambda x: f"Turno {x}"
    )

    # Trova il turno corrispondente
    t_obj = next(
        (t for t in db["turni_partite"] if t["turno"] == turno_selezionato), None
    )

    if t_obj:
      st.markdown(f"### Partite del Turno {turno_selezionato}")

      for idx, m in enumerate(t_obj["partite"]):
        key = f"turno_{turno_selezionato}_partita_{idx}"

        col_tav, col_s1, col_res1, col_sep, col_res2, col_s2 = st.columns(
            [1, 3, 1, 0.2, 1, 3]
        )

        with col_tav:
          st.markdown(f"**Tav. {m['tavolo']}**")

        with col_s1:
          st.text(f"{m['p1']} + {m['a1']}")

        # Recupera valori salvati
        saved_g1 = db["risultati"].get(key, {}).get("gol1", 0)
        saved_g2 = db["risultati"].get(key, {}).get("gol2", 0)

        with col_res1:
          g1 = st.number_input(
              "G1",
              min_value=0,
              max_value=20,
              value=saved_g1,
              key=f"g1_{key}",
              label_visibility="collapsed",
          )
        with col_sep:
          st.markdown(":")
        with col_res2:
          g2 = st.number_input(
              "G2",
              min_value=0,
              max_value=20,
              value=saved_g2,
              key=f"g2_{key}",
              label_visibility="collapsed",
          )

        with col_s2:
          st.text(f"{m['p2']} + {m['a2']}")

        # Salva al volo nel db dei risultati
        if key not in db["risultati"]:
          db["risultati"][key] = {}
        db["risultati"][key]["gol1"] = g1
        db["risultati"][key]["gol2"] = g2

      if st.button("💾 Salva Risultati Turno e Aggiorna Classifica"):
        ricalcola_classifiche()
        salva_dati(db)
        st.success("Risultati salvati e classifiche aggiornate!")

# ------------------------------------------
# 3. CLASSIFICHE
# ------------------------------------------
elif menu == "🏆 Classifiche":
  st.subheader("Classifiche Ufficiali Gironi")

  col_cp, col_ca = st.columns(2)

  with col_cp:
    st.markdown("### 🧤 Portieri")
    punti_p = db["punti_portieri"]
    dr_p = db["dr_portieri"]

    # Ordina per Punti descrescente, poi Differenza Reti
    classifica_p = sorted(
        punti_p.keys(), key=lambda x: (punti_p[x], dr_p.get(x, 0)), reverse=True
    )

    dati_p = []
    for pos, p in enumerate(classifica_p, 1):
      dati_p.append({
          "Pos": pos,
          "Portiere": p,
          "Punti": punti_p[p],
          "DR": dr_p.get(p, 0),
      })
    if dati_p:
      st.dataframe(dati_p, use_container_width=True)
    else:
      st.info("Nessun dato disponibile.")

  with col_ca:
    st.markdown("### 🎯 Attaccanti")
    punti_a = db["punti_attaccanti"]
    dr_a = db["dr_attaccanti"]

    classifica_a = sorted(
        punti_a.keys(), key=lambda x: (punti_a[x], dr_a.get(x, 0)), reverse=True
    )

    dati_a = []
    for pos, a in enumerate(classifica_a, 1):
      dati_a.append({
          "Pos": pos,
          "Attaccante": a,
          "Punti": punti_a[a],
          "DR": dr_a.get(a, 0),
      })
    if dati_a:
      st.dataframe(dati_a, use_container_width=True)
    else:
      st.info("Nessun dato disponibile.")

# ------------------------------------------
# 4. FASE FINALE (PLAYOFF)
# ------------------------------------------
elif menu == "⚡ Fase Finale (Playoff)":
  st.subheader("Fase Finale / Playoff")
  st.info(
      "Qui puoi gestire gli accoppiamenti finali in base alle classifiche dei"
      " gironi."
  )

  punti_p = db["punti_portieri"]
  dr_p = db["dr_portieri"]
  classifica_p = sorted(
      punti_p.keys(), key=lambda x: (punti_p[x], dr_p.get(x, 0)), reverse=True
  )

  punti_a = db["punti_attaccanti"]
  dr_a = db["dr_attaccanti"]
  classifica_a = sorted(
      punti_a.keys(), key=lambda x: (punti_a[x], dr_a.get(x, 0)), reverse=True
  )

  if len(classifica_p) >= 4 and len(classifica_a) >= 4:
    st.markdown("### Top 4 Portieri e Top 4 Attaccanti qualificati:")
    c1, c2 = st.columns(2)
    with c1:
      st.write("**Portieri:**")
      for i in range(min(4, len(classifica_p))):
        st.text(f"{i+1}° - {classifica_p[i]} ({punti_p[classifica_p[i]]} pt)")
    with c2:
      st.write("**Attaccanti:**")
      for i in range(min(4, len(classifica_a))):
        st.text(f"{i+1}° - {classifica_a[i]} ({punti_a[classifica_a[i]]} pt)")
  else:
    st.warning("Servono almeno 4 portieri e 4 attaccanti in classifica.")
