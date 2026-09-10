from datetime import datetime, timedelta
from fpdf import FPDF
import json
import os
import random
import re
import time
import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Torneo Biliardino 'Giallo' Live", layout="wide")

st_autorefresh(interval=3000, debounce=True, key="auto_refresh_torneo")

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


def genera_singolo_turno(
    t,
    portieri,
    attaccanti,
    num_tavoli,
    coppie_viste_esplicite,
    avversari_portieri_espliciti,
    avversari_attaccanti_espliciti,
):
  p_list = list(portieri)
  a_list = list(attaccanti)

  is_port_eccesso = len(p_list) > len(a_list)

  if is_port_eccesso:
    idx_rip = (t - 1) % len(p_list)
    portiere_rip = p_list.pop(idx_rip)
    ruolo_rip = ("portiere", portiere_rip)
  else:
    idx_rip = (t - 1) % len(a_list)
    attaccante_rip = a_list.pop(idx_rip)
    ruolo_rip = ("attaccante", attaccante_rip)

  miglior_config = None
  min_conflitti = 999999
  miglior_set_locali = None

  for _ in range(500):
    p_c = list(p_list)
    a_c = list(a_list)
    random.shuffle(p_c)
    random.shuffle(a_c)

    partite_provvisorie = []
    conflitti_turno = 0
    coppie_turno_locali = set()
    avv_p_turno_locali = set()
    avv_a_turno_locali = set()

    i = 0
    while i < len(p_c) and i + 1 < len(p_c):
      p1, a1 = p_c[i], a_c[i]
      p2, a2 = p_c[i + 1], a_c[i + 1]

      c1 = tuple(sorted([p1, a1]))
      c2 = tuple(sorted([p2, a2]))
      s1 = tuple(sorted([p1, p2]))
      s2 = tuple(sorted([a1, a2]))

      if (
          c1 in coppie_viste_esplicite
          or c2 in coppie_viste_esplicite
          or s1 in avversari_portieri_espliciti
          or s2 in avversari_attaccanti_espliciti
          or c1 in coppie_turno_locali
          or c2 in coppie_turno_locali
          or s1 in avv_p_turno_locali
          or s2 in avv_a_turno_locali
      ):
        conflitti_turno += 1

      coppie_turno_locali.add(c1)
      coppie_turno_locali.add(c2)
      avv_p_turno_locali.add(s1)
      avv_a_turno_locali.add(s2)

      match_id = f"t{t}_m{len(partite_provvisorie)}"
      partite_provvisorie.append({
          "id": match_id,
          "p1": p1,
          "a1": a1,
          "p2": p2,
          "a2": a2,
          "giocata": False,
          "in_corso": False,
          "gol1": 0,
          "gol2": 0,
      })
      i += 2

    if conflitti_turno < min_conflitti:
      min_conflitti = conflitti_turno
      miglior_config = partite_provvisorie
      miglior_set_locali = (
          coppie_turno_locali,
          avv_p_turno_locali,
          avv_a_turno_locali,
      )
      if min_conflitti == 0:
        break

  partite_turno = miglior_config if miglior_config is not None else []

  tipo_rip, nome_rip = ruolo_rip
  if tipo_rip == "attaccante":
    partite_turno.append({
        "id": f"t{t}_riposo_a",
        "p1": "",
        "a1": nome_rip,
        "p2": "",
        "a2": "",
        "giocata": True,
        "in_corso": False,
        "gol1": 0,
        "gol2": 0,
        "è_riposo_attaccante": True,
    })
  else:
    partite_turno.append({
        "id": f"t{t}_riposo_p",
        "p1": nome_rip,
        "a1": "",
        "p2": "",
        "a2": "",
        "giocata": True,
        "in_corso": False,
        "gol1": 0,
        "gol2": 0,
        "è_riposo_portiere": True,
    })

  return partite_turno, ruolo_rip, miglior_set_locali


def genera_calendario_corretto(portieri, attaccanti, num_turni, num_tavoli):
  p_list = list(portieri)
  a_list = list(attaccanti)

  turni_partite = []
  ruoli_riposo_per_turno = []

  coppie_viste = set()
  avversari_portieri = set()
  avversari_attaccanti = set()

  for t in range(1, num_turni + 1):
    partite_turno, ruolo_rip, sets_locali = genera_singolo_turno(
        t,
        p_list,
        a_list,
        num_tavoli,
        coppie_viste,
        avversari_portieri,
        avversari_attaccanti,
    )
    ruoli_riposo_per_turno.append(ruolo_rip)

    if sets_locali:
      c_loc, ap_loc, aa_loc = sets_locali
      coppie_viste.update(c_loc)
      avversari_portieri.update(ap_loc)
      avversari_attaccanti.update(aa_loc)

    turni_partite.append({"turno": t, "partite": partite_turno})

  elementi_da_recuperare = [val[1] for val in ruoli_riposo_per_turno]
  if elementi_da_recuperare:
    turno_num = num_turni + 1
    random.shuffle(elementi_da_recuperare)
    partite_turno_extra = []
    match_idx = 0

    is_portieri_in_eccesso = len(p_list) > len(a_list)
    if is_portieri_in_eccesso:
      attaccanti_jolly = list(attaccanti)
      random.shuffle(attaccanti_jolly)
      a_index = 0
      for i in range(0, len(elementi_da_recuperare), 2):
        if i + 1 < len(elementi_da_recuperare):
          p1_r = elementi_da_recuperare[i]
          p2_r = elementi_da_recuperare[i + 1]
          aj1 = attaccanti_jolly[a_index % len(attaccanti_jolly)]
          aj2 = attaccanti_jolly[(a_index + 1) % len(attaccanti_jolly)]
          a_index += 2

          partite_turno_extra.append({
              "id": f"t{turno_num}_m{match_idx}",
              "p1": p1_r,
              "a1": f"{aj1} (Jolly)",
              "p2": p2_r,
              "a2": f"{aj2} (Jolly)",
              "giocata": False,
              "in_corso": False,
              "gol1": 0,
              "gol2": 0,
              "è_extra_recupero": True,
              "is_portieri_jolly": True,
          })
          match_idx += 1
    else:
      portieri_jolly = list(portieri)
      random.shuffle(portieri_jolly)
      p_index = 0
      for i in range(0, len(elementi_da_recuperare), 2):
        if i + 1 < len(elementi_da_recuperare):
          a1 = elementi_da_recuperare[i]
          a2 = elementi_da_recuperare[i + 1]
          pj1 = portieri_jolly[p_index % len(portieri_jolly)]
          pj2 = portieri_jolly[(p_index + 1) % len(portieri_jolly)]
          p_index += 2

          partite_turno_extra.append({
              "id": f"t{turno_num}_m{match_idx}",
              "p1": f"{pj1} (Jolly)",
              "a1": a1,
              "p2": f"{pj2} (Jolly)",
              "a2": a2,
              "giocata": False,
              "in_corso": False,
              "gol1": 0,
              "gol2": 0,
              "è_extra_recupero": True,
              "is_portieri_jolly": False,
          })
          match_idx += 1

      if len(elementi_da_recuperare) % 2 != 0:
        a_singolo = elementi_da_recuperare[-1]
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
            "is_portieri_jolly": False,
        })

    if partite_turno_extra:
      turni_partite.append({"turno": turno_num, "partite": partite_turno_extra})

  return turni_partite


def analizza_conflitti_calendario():
  coppie_viste = {}
  avversari_portieri = {}
  avversari_attaccanti = {}
  errori = []

  for turno_obj in db["turni_partite"]:
    t_num = turno_obj["turno"]
    if t_num > db.get("partite_per_giocatore", 6):
      continue

    for m in turno_obj["partite"]:
      if (
          m.get("è_riposo_attaccante", False)
          or m.get("è_riposo_portiere", False)
          or m.get("a2") == "RIPOSO"
      ):
        continue

      p1, a1 = m["p1"], m["a1"]
      p2, a2 = m["p2"], m["a2"]

      for squadra in [(p1, a1), (p2, a2)]:
        if "(Jolly)" not in str(squadra[0]) and "(Jolly)" not in str(
            squadra[1]
        ):
          coppia = tuple(sorted(squadra))
          if coppia in coppie_viste:
            errori.append(
                f"Turno {t_num}: {squadra[0]} e {squadra[1]} hanno già giocato"
                f" insieme nel Turno {coppie_viste[coppia]}."
            )
          else:
            coppie_viste[coppia] = t_num

      if "(Jolly)" not in str(p1) and "(Jolly)" not in str(p2):
        sfida_p = tuple(sorted([p1, p2]))
        if sfida_p in avversari_portieri:
          errori.append(
              f"Turno {t_num}: I portieri {p1} e {p2} si sono già affrontati"
              f" nel Turno {avversari_portieri[sfida_p]}."
          )
        else:
          avversari_portieri[sfida_p] = t_num

      if "(Jolly)" not in str(a1) and "(Jolly)" not in str(a2):
        sfida_a = tuple(sorted([a1, a2]))
        if sfida_a in avversari_attaccanti:
          errori.append(
              f"Turno {t_num}: Gli attaccanti {a1} e {a2} si sono già"
              f" affrontati nel Turno {avversari_attaccanti[sfida_a]}."
          )
        else:
          avversari_attaccanti[sfida_a] = t_num

  return errori


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
      },
  ]
  db["fasi_finali"] = [
      {"turno": 1, "nome": "Quarti di Finale", "partite": quarti_partite}
  ]
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
  st.sidebar.subheader("🎲 Gestione Sorteggi")
  if st.sidebar.button(
      "🔄 Rigenera/Risorteggia Calendario", use_container_width=True
  ):
    if db["portieri"] and db["attaccanti"]:
      db["turni_partite"] = genera_calendario_corretto(
          db["portieri"],
          db["attaccanti"],
          db["partite_per_giocatore"],
          db["num_tavoli"],
      )
      ricalcola_classifiche()
      salva_dati(db)
      if "ultimi_errori" in st.session_state:
        del st.session_state["ultimi_errori"]
      st.sidebar.success("Calendario rigenerato con successo!")
      st.rerun()

  st.sidebar.markdown("---")
  st.sidebar.subheader("🔍 Verifica e Risoluzione Conflitti")

  if "is_loading_conflitti" not in st.session_state:
    st.session_state["is_loading_conflitti"] = False

  if st.sidebar.button(
      "🧹 Verifica e Pulisci Conflitti (Auto)", use_container_width=True
  ):
    st.session_state["is_loading_conflitti"] = True
    st.rerun()

  if st.session_state["is_loading_conflitti"]:
    portieri = db["portieri"]
    attaccanti = db["attaccanti"]
    num_tavoli = db["num_tavoli"]
    num_turni = db["partite_per_giocatore"]

    errori_iniziali = len(analizza_conflitti_calendario())

    with st.sidebar.status(
        "⏳ Ricerca della combinazione perfetta...", expanded=True
    ) as status:
      timer_placeholder = st.empty()

      max_tentativi = 2000
      successo = False
      start_time = time.time()

      for tentativo in range(1, max_tentativi + 1):
        tempo_trascorso = int(time.time() - start_time)
        timer_placeholder.markdown(
            f"⏱️ Tempo trascorso: **{tempo_trascorso}s** (Tentativo:"
            f" {tentativo}/{max_tentativi})"
        )

        nuovi_turni = genera_calendario_corretto(
            portieri, attaccanti, num_turni, num_tavoli
        )
        db["turni_partite"] = nuovi_turni

        res_errs = analizza_conflitti_calendario()
        if not res_errs:
          successo = True
          tempo_totale = int(time.time() - start_time)
          status.update(
              label=(
                  f"Trovata combinazione pulita al tentativo {tentativo} in"
                  f" {tempo_totale}s!"
              ),
              state="complete",
              expanded=False,
          )
          break

      if not successo:
        status.update(
            label=(
                "Raggiunti i tentativi massimi senza azzerare tutto. Riprova o"
                " riduci i turni."
            ),
            state="error",
            expanded=True,
        )

    ricalcola_classifiche()
    salva_dati(db)
    st.session_state["ultimi_errori"] = analizza_conflitti_calendario()
    conflitti_finali = len(st.session_state["ultimi_errori"])
    st.session_state["is_loading_conflitti"] = False

    if conflitti_finali == 0:
      st.sidebar.success(
          f"✅ Ottimo! Rilevati {errori_iniziali} conflitti e portati a"
          " 0 conflitti!"
      )
    else:
      st.sidebar.warning(
          f"Completato. Da {errori_iniziali} siamo scesi a {conflitti_finali}"
          " conflitti."
      )
    st.rerun()

  if "ultimi_errori" in st.session_state and not st.session_state[
      "is_loading_conflitti"
  ]:
    errs = st.session_state["ultimi_errori"]
    num_errs = len(errs)
    with st.sidebar.expander(
        f"📊 Dettaglio Conflitti ({num_errs})", expanded=(num_errs > 0)
    ):
      if num_errs == 0:
        st.success(
            "Tutti i vincoli sono perfetti: 0 coppie ripetute e 0 avversari"
            " ripetuti!"
        )
      else:
        st.error(f"Rilevati {num_errs} conflitti.")
        for e in errs:
          st.markdown(f"- {e}")

  st.sidebar.markdown("---")
  st.sidebar.subheader("🕹️ Avanzamento Fasi")
  if db["stato"] == "gironi":
    if st.sidebar.button(
        "🏆 Avvia Quarti di Finale", use_container_width=True, key="sb_quarti"
    ):
      avvia_quarti()
      st.rerun()
  elif db["stato"] == "eliminatorie":
    if st.sidebar.button(
        "⬅️ Indietro ai Gironi", use_container_width=True, key="sb_back_gironi"
    ):
      db["stato"] = "gironi"
      salva_dati(db)
      st.rerun()

  st.sidebar.markdown("---")
  st.sidebar.subheader("✏️ Modifica Nome Giocatore")
  tutti_giocatori_admin = sorted(list(set(db["portieri"] + db["attaccanti"])))
  if tutti_giocatori_admin:
    giocatore_da_modificare = st.sidebar.selectbox(
        "Seleziona giocatore",
        tutti_giocatori_admin,
        key="admin_sel_mod_giocatore",
    )
    nuovo_nome = st.sidebar.text_input(
        "Nuovo nome", key="admin_nuovo_nome_giocatore"
    )
    if st.sidebar.button("Conferma Modifica Nome", use_container_width=True):
      nuovo_nome_clean = nuovo_nome.strip()
      if not nuovo_nome_clean:
        st.sidebar.error("Inserisci un nome valido.")
      elif nuovo_nome_clean in tutti_giocatori_admin:
        st.sidebar.error("Esiste già un giocatore con questo nome.")
      else:
        if giocatore_da_modificare in db["portieri"]:
          idx_p = db["portieri"].index(giocatore_da_modificare)
          db["portieri"][idx_p] = nuovo_nome_clean
        if giocatore_da_modificare in db["attaccanti"]:
          idx_a = db["attaccanti"].index(giocatore_da_modificare)
          db["attaccanti"][idx_a] = nuovo_nome_clean

        for diz_chiave in ["punti_portieri", "dr_portieri"]:
          if giocatore_da_modificare in db[diz_chiave]:
            db[diz_chiave][nuovo_nome_clean] = db[diz_chiave].pop(
                giocatore_da_modificare
            )
        for diz_chiave in ["punti_attaccanti", "dr_attaccanti"]:
          if giocatore_da_modificare in db[diz_chiave]:
            db[diz_chiave][nuovo_nome_clean] = db[diz_chiave].pop(
                giocatore_da_modificare
            )

        for t_obj in db["turni_partite"]:
          for m in t_obj["partite"]:
            for campo in ["p1", "p2", "a1", "a2"]:
              valore_attuale = str(m.get(campo, ""))
              if giocatore_da_modificare in valore_attuale:
                m[campo] = valore_attuale.replace(
                    giocatore_da_modificare, nuovo_nome_clean
                )

        salva_dati(db)
        if "ultimi_errori" in st.session_state:
          del st.session_state["ultimi_errori"]
        st.sidebar.success(
            f"Nome modificato da '{giocatore_da_modificare}' a"
            f" '{nuovo_nome_clean}' con successo!"
        )
        st.rerun()

st.markdown(
    """
    <div style="text-align: center; margin-bottom: 14px; background: linear-gradient(135deg, #0b0f19, #111827); padding: 22px; border-radius: 20px; border: 2px solid #fbbf24; box-shadow: 0 0 20px rgba(251, 191, 36, 0.2);">
        <h1 style="margin: 0; color: #fbbf24; font-size: 2rem; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;">🏆 Torneo Biliardino 'Giallo' Live</h1>
    </div>
""",
    unsafe_allow_html=True,
)

tutti_i_giocatori = sorted(list(set(db["portieri"] + db["attaccanti"])))


def pulisci_nome(testo):
  testo = (
      str(testo)
      .replace("🥅", "")
      .replace("🚪", "")
      .replace("⚽", "")
      .replace("⏳", "")
      .replace("[RIPOSO]", "")
      .replace("(Jolly)", "")
  )
  return testo.strip()


def ricalcola_classifiche():
  p_punti = {p: 0 for p in db["portieri"]}
  p_dr = {p: 0 for p in db["portieri"]}
  a_punti = {a: 0 for a in db["attaccanti"]}
  a_dr = {a: 0 for a in db["attaccanti"]}

  for turno_obj in db["turni_partite"]:
    for m in turno_obj["partite"]:
      if (
          m.get("giocata", False)
          and not m.get("è_riposo_attaccante", False)
          and not m.get("è_riposo_portiere", False)
          and m.get("a2") != "RIPOSO"
      ):
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
        is_portieri_jolly = m.get("is_portieri_jolly", False)

        a1_pulito = pulisci_nome(m["a1"])
        a2_pulito = pulisci_nome(m["a2"])

        is_jolly_a1 = "(Jolly)" in str(m["a1"])
        is_jolly_a2 = "(Jolly)" in str(m["a2"])
        is_jolly_p1 = "(Jolly)" in str(m["p1"])
        is_jolly_p2 = "(Jolly)" in str(m["p2"])

        if a1_pulito in a_punti and not is_portieri_jolly and not is_jolly_a1:
          a_punti[a1_pulito] += pt_s1
          a_dr[a1_pulito] += g1 - g2
        if a2_pulito in a_punti and not is_portieri_jolly and not is_jolly_a2:
          a_punti[a2_pulito] += pt_s2
          a_dr[a2_pulito] += g2 - g1

        p1_pulito = pulisci_nome(m["p1"])
        p2_pulito = pulisci_nome(m["p2"])

        if (
            p1_pulito in p_punti
            and not (is_extra and is_portieri_jolly)
            and not is_jolly_p1
        ):
          p_punti[p1_pulito] += pt_s1
          p_dr[p1_pulito] += g1 - g2
        if (
            p2_pulito in p_punti
            and not (is_extra and is_portieri_jolly)
            and not is_jolly_p2
        ):
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
      if m.get("è_riposo_attaccante", False) or m.get(
          "è_riposo_portiere", False
      ):
        if ruolo == "attaccante" and pulisci_nome(m["a1"]) == nome:
          totali += 1
        if ruolo == "portiere" and pulisci_nome(m["p1"]) == nome:
          totali += 1
        continue

      if m.get("a2") == "RIPOSO" and pulisci_nome(m["a1"]) == nome:
        totali += 1
        continue

      is_presente = False
      if ruolo == "portiere":
        p1_pulito = pulisci_nome(m["p1"])
        p2_pulito = pulisci_nome(m["p2"])
        if (p1_pulito == nome or p2_pulito == nome) and not (
            m.get("è_extra_recupero", False)
            and m.get("is_portieri_jolly", False)
        ):
          is_presente = True
      elif ruolo == "attaccante":
        a1_pulito = pulisci_nome(m["a1"])
        a2_pulito = pulisci_nome(m["a2"])
        if (a1_pulito == nome or a2_pulito == nome) and not (
            m.get("è_extra_recupero", False)
            and not m.get("is_portieri_jolly", False)
        ):
          is_presente = True

      if is_presente:
        totali += 1
        if m.get("giocata", False):
          giocate += 1
  return giocate, totali


def posticipa_partita_in_corso(match_id):
  match_trovato = None
  turno_trovato = None

  for t_obj in db["turni_partite"]:
    for m in t_obj["partite"]:
      if m["id"] == match_id:
        match_trovato = m
        turno_trovato = t_obj
        break
    if match_trovato:
      break

  if match_trovato and turno_trovato:
    turno_trovato["partite"].remove(match_trovato)
    inserito = False
    for i in range(len(turno_trovato["partite"]) - 1, -1, -1):
      p = turno_trovato["partite"][i]
      if (
          not p.get("giocata", False)
          and not p.get("è_riposo_attaccante", False)
          and not p.get("è_riposo_portiere", False)
      ):
        turno_trovato["partite"].insert(i + 1, match_trovato)
        inserito = True
        break
    if not inserito:
      turno_trovato["partite"].insert(0, match_trovato)

  salva_dati(db)


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
    pdf.cell(
        0,
        8,
        f"Turno {t_nome}"
        + (
            " (Turno Extra Recupero)"
            if t_nome > db.get("partite_per_giocatore", 6)
            else ""
        ),
        0,
        1,
        "L",
    )
    pdf.set_font("Arial", "", 10)

    for idx, m in enumerate(turno_obj["partite"]):
      if m.get("è_riposo_attaccante", False):
        riga = f"  - Riposa ATT: {m['a1']}"
      elif m.get("è_riposo_portiere", False):
        riga = f"  - Riposa POR: {m['p1']}"
      elif m.get("a2") == "RIPOSO":
        riga = f"  - {m['p1']} e {m['a1']} (Turno singolo / Riposo)"
      else:
        tavolo_num = (idx % num_tavoli) + 1
        risultato = (
            f"{m['gol1']} - {m['gol2']}"
            if m.get("giocata", False)
            else "Da giocare"
        )
        riga = (
            f"  - Biliardino {tavolo_num}: {m['p1']} e {m['a1']} vs {m['p2']} e"
            f" {m['a2']} -> {risultato}"
        )

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
            background: linear-gradient(135deg, #111827, #1f2937) !important;
            color: #fbbf24 !important;
            border: 1px solid #fbbf24 !important;
            border-radius: 12px !important;
            font-weight: 700 !important;
            font-size: 1.1rem !important;
            height: 50px !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            transition: all 0.2s ease-in-out;
        }
        button[data-testid="stBaseButton-secondary"]:hover {
            border-color: #fef08a !important;
            color: #fef08a !important;
            box-shadow: 0 0 15px rgba(251, 191, 36, 0.4);
        }
        .live-match-box {
            background: linear-gradient(135deg, #064e3b, #022c22);
            border: 2px solid #34d399;
            border-radius: 16px;
            padding: 16px;
            margin-bottom: 14px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(52, 211, 153, 0.2);
        }
        .finished-match-box {
            background: linear-gradient(135deg, #450a0a, #7f1d1d);
            border: 2px solid #f87171;
            border-radius: 16px;
            padding: 14px;
            margin-bottom: 14px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(248, 113, 113, 0.25);
        }
        .queue-match-box {
            background: linear-gradient(135deg, #1e3a8a, #1e293b);
            border: 2px solid #60a5fa;
            border-radius: 14px;
            padding: 14px 18px;
            margin-bottom: 10px;
            box-shadow: 0 4px 12px rgba(96, 165, 250, 0.25);
        }
        .riposo-match-box {
            background: linear-gradient(135deg, #0c4a6e, #0369a1);
            border: 2px solid #38bdf8;
            border-radius: 16px;
            padding: 14px;
            margin-bottom: 14px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(56, 189, 248, 0.2);
        }
        .rank-card-green {
            background: linear-gradient(135deg, rgba(6, 78, 59, 0.4), rgba(2, 44, 34, 0.6));
            border-left: 6px solid #34d399;
            border-top: 1px solid #059669;
            border-right: 1px solid #059669;
            border-bottom: 1px solid #059669;
            padding: 10px 14px;
            border-radius: 10px;
            margin-bottom: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .rank-card-red {
            background: linear-gradient(135deg, rgba(127, 29, 29, 0.3), rgba(69, 10, 10, 0.5));
            border-left: 6px solid #f87171;
            border-top: 1px solid #991b1b;
            border-right: 1px solid #991b1b;
            border-bottom: 1px solid #991b1b;
            padding: 10px 14px;
            border-radius: 10px;
            margin-bottom: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
    </style>
""",
    unsafe_allow_html=True,
)

if db["stato"] == "setup":
  st.subheader("1. Configurazione Iniziale del Torneo")
  if not is_admin:
    st.warning("Accedi come Admin dalla barra laterale per configurare.")
  else:
    whatsapp_text = st.text_area("Incolla qui la lista da WhatsApp:")
    col1, col2 = st.columns(2)
    with col1:
      db["num_tavoli"] = int(
          st.text_input(
              "Numero di biliardini",
              value=str(db["num_tavoli"]),
              type="default",
          )
      )
    with col2:
      db["partite_per_giocatore"] = int(
          st.text_input(
              "Turni / Partite garantite",
              value=str(db["partite_per_giocatore"]),
              type="default",
          )
      )
    db["admin_pin"] = st.text_input("PIN Admin", value=db["admin_pin"])

    if st.button("🚀 Avvia il Torneo e Genera Calendario"):
      portieri, attaccanti = [], []
      for line in whatsapp_text.split("\n"):
        if "🚪" in line or "🥅" in line:
          n = pulisci_nome(line)
          if n:
            portieri.append(n)
        elif "⚽" in line:
          n = pulisci_nome(line)
          if n:
            attaccanti.append(n)

      if len(portieri) < 2 or len(attaccanti) < 2:
        st.error(
            f"Inserisci almeno 2 portieri e 2 attaccanti. Rilevati:"
            f" {len(portieri)} portieri e {len(attaccanti)} attaccanti."
        )
      else:
        db["portieri"] = portieri
        db["attaccanti"] = attaccanti
        db["punti_portieri"] = {p: 0 for p in portieri}
        db["dr_portieri"] = {p: 0 for p in portieri}
        db["punti_attaccanti"] = {a: 0 for a in attaccanti}
        db["dr_attaccanti"] = {a: 0 for a in attaccanti}
        db["stato"] = "gironi"
        db["turni_partite"] = genera_calendario_corretto(
            portieri, attaccanti, db["partite_per_giocatore"], db["num_tavoli"]
        )
        if "ultimi_errori" in st.session_state:
          del st.session_state["ultimi_errori"]
        salva_dati(db)
        st.success("Torneo avviato con successo!")
        st.rerun()

if db["stato"] == "gironi":
  if st.session_state.get("is_loading_conflitti", False):
    st.markdown(
        """
        <div style="text-align: center; padding: 80px 20px;">
            <div style="font-size: 3rem; margin-bottom: 15px;">⏳</div>
            <h2 style="color: #fbbf24; margin-bottom: 10px;">Ottimizzazione del calendario in corso...</h2>
            <p style="color: #94a3b8; font-size: 1.1rem;">Sto analizzando tutte le combinazioni per azzerare i conflitti tra coppie e avversari. Lo schema delle partite tornerà visibile non appena completato.</p>
        </div>
    """,
        unsafe_allow_html=True,
    )
    st.stop()

  ricalcola_classifiche()
  num_tavoli = db.get("num_tavoli", 3)

  params = st.query_params
  giocatore_salvato = params.get("giocatore", "-- Seleziona --")

  if giocatore_salvato not in ["-- Seleziona --"] + tutti_i_giocatori:
    giocatore_salvato = "-- Seleziona --"

  if giocatore_salvato == "-- Seleziona --" and not is_admin:
    st.markdown(
        """
        <div style="text-align: center; padding: 40px 20px; background: linear-gradient(135deg, #0b0f19, #111827); border-radius: 24px; border: 2px solid #fbbf24; box-shadow: 0 0 30px rgba(251, 191, 36, 0.25); max-width: 600px; margin: 40px auto;">
            <div style="font-size: 3rem; margin-bottom: 10px;">⚽⚽</div>
            <h1 style="color: #fbbf24; font-size: 1.8rem; font-weight: 800; text-transform: uppercase; margin-bottom: 10px;">Benvenuto nel Torneo Giallo!</h1>
            <p style="color: #94a3b8; font-size: 1.05rem; margin-bottom: 25px;">Seleziona il tuo nome dall'elenco sottostante per accedere al tuo profilo, vedere le tue partite e inserire i tuoi risultati.</p>
            <div style="font-size: 1.1rem; color: #fbbf24; font-weight: 700; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 1px;">👇 Seleziona il tuo nome 👇</div>
        </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(
        "<div style='max-width: 500px; margin: 0 auto;'>", unsafe_allow_html=True
    )
    scelta_iniziale = st.selectbox(
        "Il tuo nome:",
        ["-- Seleziona --"] + tutti_i_giocatori,
        key="selettore_ingresso_giocatore",
        label_visibility="collapsed",
    )

    if scelta_iniziale != "-- Seleziona --":
      st.query_params["giocatore"] = scelta_iniziale
      st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.stop()

  giocatore_selezionato = (
      giocatore_salvato if giocatore_salvato != "-- Seleziona --" else None
  )

  if giocatore_selezionato:
    col_cambia_1, col_cambia_2 = st.columns([6, 1])
    with col_cambia_2:
      if st.button(
          "🔄 Esci",
          use_container_width=True,
          help="Torna alla schermata di scelta nome",
      ):
        if "giocatore" in st.query_params:
          del st.query_params["giocatore"]
        st.rerun()

  if giocatore_selezionato:
    ruolo_p = (
        "portiere" if giocatore_selezionato in db["portieri"] else "attaccante"
    )
    pts = (
        db["punti_portieri"].get(giocatore_selezionato, 0)
        if ruolo_p == "portiere"
        else db["punti_attaccanti"].get(giocatore_selezionato, 0)
    )
    dr = (
        db["dr_portieri"].get(giocatore_selezionato, 0)
        if ruolo_p == "portiere"
        else db["dr_attaccanti"].get(giocatore_selezionato, 0)
    )

    if ruolo_p == "portiere":
      sorted_list = sorted(
          db["punti_portieri"].items(),
          key=lambda x: (x[1], db["dr_portieri"].get(x[0], 0)),
          reverse=True,
      )
    else:
      sorted_list = sorted(
          db["punti_attaccanti"].items(),
          key=lambda x: (x[1], db["dr_attaccanti"].get(x[0], 0)),
          reverse=True,
      )

    pos = next(
        (
            i + 1
            for i, item in enumerate(sorted_list)
            if item[0] == giocatore_selezionato
        ),
        "-",
    )

    st.markdown(
        f"""
      <div style="background: linear-gradient(135deg, #0b0f19, #111827); border: 2px solid #fbbf24; border-radius: 20px; padding: 20px; margin-top: 10px; margin-bottom: 20px; box-shadow: 0 0 20px rgba(251,191,36,0.2);">
        <div style="font-size: 0.85rem; color: #fbbf24; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px;">IL TUO PROFILO SALVATO</div>
        <div style="font-size: 1.6rem; font-weight: 800; color: #ffffff; margin-bottom: 16px;">
          {'🥅' if ruolo_p == 'portiere' else '⚽'} {giocatore_selezionato}
        </div>
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px;">
          <div style="background: rgba(15, 23, 42, 0.8); border: 1px solid #334155; padding: 12px; border-radius: 12px; text-align: center;">
            <div style="font-size: 0.75rem; color: #94a3b8; font-weight: 700; text-transform: uppercase;">POSIZIONE</div>
            <div style="font-size: 1.25rem; font-weight: 800; color: #34d399; margin-top: 4px;">{pos}° POSTO</div>
          </div>
          <div style="background: rgba(15, 23, 42, 0.8); border: 1px solid #334155; padding: 12px; border-radius: 12px; text-align: center;">
            <div style="font-size: 0.75rem; color: #94a3b8; font-weight: 700; text-transform: uppercase;">RUOLO</div>
            <div style="font-size: 1.15rem; font-weight: 800; color: #60a5fa; margin-top: 4px;">{ruolo_p.capitalize()}</div>
          </div>
          <div style="background: rgba(15, 23, 42, 0.8); border: 1px solid #334155; padding: 12px; border-radius: 12px; text-align: center;">
            <div style="font-size: 0.75rem; color: #94a3b8; font-weight: 700; text-transform: uppercase;">PUNTI / DR</div>
            <div style="font-size: 1.15rem; font-weight: 800; color: #fbbf24; margin-top: 4px;">{pts} PT <span style="font-size: 0.85rem; color: #94a3b8;">({dr:+d})</span></div>
          </div>
        </div>
      </div>
    """,
        unsafe_allow_html=True,
    )

  partite_aperte_totali = []
  for t_obj in db["turni_partite"]:
    for idx, m in enumerate(t_obj["partite"]):
      if (
          not m.get("giocata", False)
          and not m.get("è_riposo_attaccante", False)
          and not m.get("è_riposo_portiere", False)
          and m.get("a2") != "RIPOSO"
      ):
        tavolo_num = (idx % num_tavoli) + 1
        partite_aperte_totali.append({
            "turno": t_obj["turno"],
            "match": m,
            "tavolo": tavolo_num,
        })

  if giocatore_selezionato:
    match_trovato = None
    stato_partita = None
    tavolo_assegnato = None
    turno_attivo = None

    for idx_globale, item in enumerate(partite_aperte_totali):
      m = item["match"]
      t_num = item["turno"]
      tav_num = item["tavolo"]

      p1_pulito = pulisci_nome(m["p1"])
      p2_pulito = pulisci_nome(m["p2"])
      a1_pulito = pulisci_nome(m["a1"])
      a2_pulito = pulisci_nome(m["a2"])

      coinvolto = (
          giocatore_selezionato == p1_pulito
          or giocatore_selezionato == p2_pulito
          or giocatore_selezionato == a1_pulito
          or giocatore_selezionato == a2_pulito
      )

      if coinvolto:
        if idx_globale < num_tavoli:
          match_trovato = m
          turno_attivo = t_num
          stato_partita = "in_corso"
          tavolo_assegnato = tav_num
        elif idx_globale < num_tavoli * 2:
          match_trovato = m
          turno_attivo = t_num
          stato_partita = "in_coda"
        break

    if match_trovato:
      st.markdown("### 🔍 La tua partita:")
      if stato_partita == "in_corso":
        st.markdown(
            f"""
          <div class="live-match-box">
              <div style="font-weight: 800; color: #34d399; font-size: 1.1rem; margin-bottom: 4px;">🟢 LA TUA PARTITA (Biliardino {tavolo_assegnato} - Turno {turno_attivo})</div>
              <div style="font-size: 1.25rem; font-weight: 700; color: #f8fafc; margin: 6px 0;">
                  {match_trovato['p1']} e {match_trovato['a1']} <span style="color:#34d399; font-weight:400;">VS</span> {match_trovato['p2']} e {match_trovato['a2']}
              </div>
          </div>
        """,
            unsafe_allow_html=True,
        )

        if st.button(
            "⏱️ Posticipa questa partita in coda",
            key=f"posticipa_pers_{match_trovato['id']}",
            use_container_width=True,
        ):
          posticipa_partita_in_corso(match_trovato["id"])
          st.success("Partita posticipata in coda e prossimi match avanzati!")
          st.rerun()

        exp_key_open_pers = f"exp_open_pers_{match_trovato['id']}"
        if exp_key_open_pers not in st.session_state:
          st.session_state[exp_key_open_pers] = False

        with st.expander(
            f"⚙️ Inserisci il Risultato (Biliardino {tavolo_assegnato})",
            expanded=st.session_state[exp_key_open_pers],
        ):
          with st.form(key=f"form_pers_{match_trovato['id']}"):
            st.write("Inserisci i goal assegnati a ciascuna squadra:")
            curr_g1 = str(match_trovato.get("gol1", 0))
            curr_g2 = str(match_trovato.get("gol2", 0))

            col_pers_1, col_pers_2 = st.columns(2)
            with col_pers_1:
              st.markdown(
                  f'<b>🥅 {match_trovato["p1"]} & {match_trovato["a1"]}</b>',
                  unsafe_allow_html=True,
              )
              str_g1 = st.text_input(
                  "Gol S1",
                  value=curr_g1,
                  key=f"num_pers_g1_{match_trovato['id']}",
                  label_visibility="collapsed",
              )
            with col_pers_2:
              st.markdown(
                  f'<b>🥅 {match_trovato["p2"]} & {match_trovato["a2"]}</b>',
                  unsafe_allow_html=True,
              )
              str_g2 = st.text_input(
                  "Gol S2",
                  value=curr_g2,
                  key=f"num_pers_g2_{match_trovato['id']}",
                  label_visibility="collapsed",
              )

            st.markdown("<br>", unsafe_allow_html=True)
            submitted_pers = st.form_submit_button(
                "Salva Risultato", use_container_width=True
            )
            if submitted_pers:
              try:
                match_trovato["gol1"] = (
                    int(str_g1) if str_g1.strip() != "" else 0
                )
                match_trovato["gol2"] = (
                    int(str_g2) if str_g2.strip() != "" else 0
                )
              except ValueError:
                match_trovato["gol1"] = 0
                match_trovato["gol2"] = 0
              match_trovato["giocata"] = True
              ricalcola_classifiche()
              salva_dati(db)
              st.session_state[exp_key_open_pers] = False
              st.rerun()
      elif stato_partita == "in_coda":
        st.markdown(
            f"""
          <div class="queue-match-box">
              <div style="font-size: 0.9rem; color: #93c5fd; font-weight: 700;">⏳ LA TUA PARTITA IN CODA (Turno {turno_attivo})</div>
              <div style="font-size: 1.15rem; font-weight: 700; color: #ffffff; margin-top: 4px;">
                  {match_trovato['p1']} e {match_trovato['a1']} <span style="color: #60a5fa;">vs</span> {match_trovato['p2']} e {match_trovato['a2']}
              </div>
              <div style="font-size: 0.9rem; color: #94a3b8; margin-top: 4px;">In attesa che si liberi un biliardino.</div>
          </div>
        """,
            unsafe_allow_html=True,
        )

  st.markdown("---")

  partite_aperte_totali_aggiornate = []
  for t_obj in db["turni_partite"]:
    for idx, m in enumerate(t_obj["partite"]):
      if (
          not m.get("giocata", False)
          and not m.get("è_riposo_attaccante", False)
          and not m.get("è_riposo_portiere", False)
          and m.get("a2") != "RIPOSO"
      ):
        tavolo_num = (idx % num_tavoli) + 1
        partite_aperte_totali_aggiornate.append({
            "turno": t_obj["turno"],
            "match": m,
            "tavolo": tavolo_num,
        })

  partite_in_corso_gen = partite_aperte_totali_aggiornate[:num_tavoli]
  partite_in_coda_gen = partite_aperte_totali_aggiornate[
      num_tavoli : num_tavoli * 2
  ]

  st.markdown(f"### 🟢 PARTITE IN CORSO ( sui {num_tavoli} Biliardini )")
  if partite_in_corso_gen:
    for item in partite_in_corso_gen:
      m = item["match"]
      tav_num = item["tavolo"]

      p1_p = pulisci_nome(m["p1"])
      p2_p = pulisci_nome(m["p2"])
      a1_p = pulisci_nome(m["a1"])
      a2_p = pulisci_nome(m["a2"])
      utente_coinvolto = (
          giocatore_selezionato is not None
          and giocatore_selezionato in [p1_p, p2_p, a1_p, a2_p]
      )

      st.markdown(
          f"""
        <div class="live-match-box">
            <div style="font-weight: 800; color: #34d399; font-size: 1.1rem; margin-bottom: 4px;">🏟️ BILIARDINO {tav_num} (Turno {item['turno']}) — LIVE 🟢</div>
            <div style="font-size: 1.25rem; font-weight: 700; color: #f8fafc; margin: 6px 0;">
                {m['p1']} e {m['a1']} <span style="color:#34d399; font-weight:400;">VS</span> {m['p2']} e {m['a2']}
            </div>
        </div>
      """,
          unsafe_allow_html=True,
      )

      if utente_coinvolto or is_admin:
        if st.button(
            "⏱️ Posticipa match",
            key=f"posticipa_gen_{m['id']}",
            use_container_width=True,
        ):
          posticipa_partita_in_corso(m["id"])
          st.success("Partita posticipata e slot avanzato!")
          st.rerun()

        exp_key_gen = f"exp_open_gen_{m['id']}"
        if exp_key_gen not in st.session_state:
          st.session_state[exp_key_gen] = False

        with st.expander(
            f"⚙️ Inserisci Risultato Biliardino {tav_num} (Turno"
            f" {item['turno']})",
            expanded=st.session_state[exp_key_gen],
        ):
          with st.form(key=f"form_gen_{m['id']}"):
            st.write("Inserisci i goal assegnati a ciascuna squadra:")
            curr_g1 = str(m.get("gol1", 0))
            curr_g2 = str(m.get("gol2", 0))

            col_gen_1, col_gen_2 = st.columns(2)
            with col_gen_1:
              st.markdown(
                  f'<b>🥅 {m["p1"]} & {m["a1"]}</b>', unsafe_allow_html=True
              )
              str_g1 = st.text_input(
                  "Gol S1",
                  value=curr_g1,
                  key=f"num_gen_g1_{m['id']}",
                  label_visibility="collapsed",
              )
            with col_gen_2:
              st.markdown(
                  f'<b>🥅 {m["p2"]} & {m["a2"]}</b>', unsafe_allow_html=True
              )
              str_g2 = st.text_input(
                  "Gol S2",
                  value=curr_g2,
                  key=f"num_gen_g2_{m['id']}",
                  label_visibility="collapsed",
              )

            st.markdown("<br>", unsafe_allow_html=True)
            submitted_gen = st.form_submit_button(
                "Salva Risultato", use_container_width=True
            )
            if submitted_gen:
              try:
                m["gol1"] = int(str_g1) if str_g1.strip() != "" else 0
                m["gol2"] = int(str_g2) if str_g2.strip() != "" else 0
              except ValueError:
                m["gol1"] = 0
                m["gol2"] = 0
              m["giocata"] = True
              ricalcola_classifiche()
              salva_dati(db)
              st.session_state[exp_key_gen] = False
              st.rerun()
  else:
    st.info("Nessuna partita in corso al momento.")

  st.markdown(f"### ⏳ PARTITE IN CODA (Prossimi {num_tavoli} match)")
  if partite_in_coda_gen:
    for item in partite_in_coda_gen:
      m = item["match"]
      st.markdown(
          f"""
        <div class="queue-match-box">
            <div style="font-size: 0.9rem; color: #93c5fd; font-weight: 700;">Turno {item['turno']} (In attesa di un tavolo libero)</div>
            <div style="font-size: 1.15rem; font-weight: 700; color: #ffffff; margin-top: 4px;">
                {m['p1']} e {m['a1']} <span style="color: #60a5fa;">vs</span> {m['p2']} e {m['a2']}
            </div>
        </div>
      """,
          unsafe_allow_html=True,
      )
  else:
    st.info("Nessuna partita in coda.")

  st.markdown("---")

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

  st.markdown("### 🔥 TUTTI I TURNI E RISULTATI")
  for t_obj in db["turni_partite"]:
    is_extra = t_obj["turno"] > db.get("partite_per_giocatore", 6)
    titolo_turno = (
        f"📌 Turno {t_obj['turno']} (Turno Extra Recupero - GIALLO 🟡)"
        if is_extra
        else f"📌 Turno {t_obj['turno']}"
    )
    st.markdown(f"#### {titolo_turno}")

    for idx, m in enumerate(t_obj["partite"]):
      if m.get("è_riposo_attaccante", False):
        st.markdown(
            f"""
            <div class="riposo-match-box">
                <div style="font-weight: 800; color: #e0f2fe; font-size: 1.1rem;">⏳ RIPOSO ATTACCANTE</div>
                <div style="font-size: 1.1rem; color: #ffffff; margin-top: 4px;"><b>Riposa ATT: {m['a1']}</b></div>
            </div>
        """,
            unsafe_allow_html=True,
        )
      elif m.get("è_riposo_portiere", False):
        st.markdown(
            f"""
            <div class="riposo-match-box">
                <div style="font-weight: 800; color: #e0f2fe; font-size: 1.1rem;">⏳ RIPOSO PORTIERE</div>
                <div style="font-size: 1.1rem; color: #ffffff; margin-top: 4px;"><b>Riposa POR: {m['p1']}</b></div>
            </div>
        """,
            unsafe_allow_html=True,
        )
      elif m.get("a2") == "RIPOSO":
        st.markdown(
            f"""
            <div class="riposo-match-box">
                <div style="font-weight: 800; color: #e0f2fe; font-size: 1.1rem;">⏳ TURNO SINGOLO / RIPOSO</div>
                <div style="font-size: 1.1rem; color: #ffffff; margin-top: 4px;"><b>{m['p1']} e {m['a1']}</b></div>
            </div>
        """,
            unsafe_allow_html=True,
        )
      else:
        tavolo_num = (idx % num_tavoli) + 1
        is_giocata = m.get("giocata", False)
        box_class = (
            "finished-match-box" if is_giocata else "live-match-box"
        )
        testo_risultato = (
            f"✅ <b>Risultato Finale: {m['gol1']} - {m['gol2']}</b>"
            if is_giocata
            else "⏳ <b>Da giocare</b>"
        )

        st.markdown(
            f"""
            <div class="{box_class}">
                <div style="font-weight: 700; color: {'#f87171' if is_giocata else '#34d399'}; margin-bottom: 4px;">🏟️ BILIARDINO {tavolo_num}</div>
                <div style="font-size: 1.2rem; font-weight: 700; color: #f8fafc; margin: 6px 0;">
                    {m['p1']} e {m['a1']} <span style="color:#34d399; font-weight:400;">VS</span> {m['p2']} e {m['a2']}
                </div>
                <div style="font-size: 1.1rem; margin-top: 8px;">{testo_risultato}</div>
            </div>
        """,
            unsafe_allow_html=True,
        )

        p1_p = pulisci_nome(m["p1"])
        p2_p = pulisci_nome(m["p2"])
        a1_p = pulisci_nome(m["a1"])
        a2_p = pulisci_nome(m["a2"])
        utente_coinvolto = (
            giocatore_selezionato is not None
            and giocatore_selezionato in [p1_p, p2_p, a1_p, a2_p]
        )

        if is_admin and is_giocata:
          if st.button(
              f"↩️ Annulla Risultato (Rimanda in coda)",
              key=f"annulla_{m['id']}",
              use_container_width=True,
          ):
            m["giocata"] = False
            m["gol1"] = 0
            m["gol2"] = 0
            t_obj["partite"].remove(m)
            t_obj["partite"].insert(len(t_obj["partite"]) - 1, m)
            ricalcola_classifiche()
            salva_dati(db)
            if "ultimi_errori" in st.session_state:
              del st.session_state["ultimi_errori"]
            st.success("Partita annullata e rimandata in coda correttamente!")
            st.rerun()

        if utente_coinvolto or is_admin:
          exp_key_open = f"exp_open_{m['id']}"
          if exp_key_open not in st.session_state:
            st.session_state[exp_key_open] = False

          with st.expander(
              f"⚙️ Inserisci Risultato Biliardino {tavolo_num} (Turno"
              f" {t_obj['turno']})",
              expanded=st.session_state[exp_key_open],
          ):
            with st.form(key=f"form_{m['id']}"):
              st.write("Inserisci i goal assegnati a ciascuna squadra:")

              curr_g1 = str(m.get("gol1", 0))
              curr_g2 = str(m.get("gol2", 0))

              col_g1, col_g2 = st.columns(2)
              with col_g1:
                st.markdown(
                    f'<b>🥅 {m["p1"]} & {m["a1"]}</b>', unsafe_allow_html=True
                )
                str_g1 = st.text_input(
                    "Gol S1",
                    value=curr_g1,
                    key=f"num_g1_{m['id']}",
                    label_visibility="collapsed",
                )
              with col_g2:
                st.markdown(
                    f'<b>🥅 {m["p2"]} & {m["a2"]}</b>', unsafe_allow_html=True
                )
                str_g2 = st.text_input(
                    "Gol S2",
                    value=curr_g2,
                    key=f"num_g2_{m['id']}",
                    label_visibility="collapsed",
                )

              st.markdown("<br>", unsafe_allow_html=True)
              submitted = st.form_submit_button(
                  "Salva Risultato", use_container_width=True
              )
              if submitted:
                try:
                  m["gol1"] = int(str_g1) if str_g1.strip() != "" else 0
                  m["gol2"] = int(str_g2) if str_g2.strip() != "" else 0
                except ValueError:
                  m["gol1"] = 0
                  m["gol2"] = 0
                m["giocata"] = True
                ricalcola_classifiche()
                salva_dati(db)
                st.session_state[exp_key_open] = False
                st.rerun()

  st.markdown("---")
  st.markdown("### 🏆 CLASSIFICHE PROFESSIONALI IN TEMPO REALE")
  st.markdown(
      "<div style='font-size: 0.9rem; color: #9ca3af; margin-bottom: 12px;'>🟢"
      " Prime 8 posizioni in zona qualificazione Quarti | 🔴 Ultime posizioni"
      " in zona eliminazione</div>",
      unsafe_allow_html=True,
  )

  st.markdown("#### 🥅 Classifica Portieri")
  sorted_p = sorted(
      db["punti_portieri"].items(),
      key=lambda x: (x[1], db["dr_portieri"].get(x[0], 0)),
      reverse=True,
  )
  for idx, (p, pt) in enumerate(sorted_p):
    gioc, tot = calcola_partite_giocate("portiere", p)
    dr_p = db["dr_portieri"].get(p, 0)
    card_class = "rank-card-green" if idx < 8 else "rank-card-red"
    st.markdown(
        f"""
      <div class="{card_class}">
        <div><b>{idx+1}°</b> &nbsp; 🥅 &nbsp; <b>{p}</b></div>
        <div style="color: #cbd5e1; font-size: 0.95rem;">Punti: <b>{pt}</b> &nbsp;|&nbsp; Diff. Reti: <b>{dr_p:+d}</b> &nbsp;|&nbsp; Partite: {gioc}/{tot}</div>
      </div>
    """,
        unsafe_allow_html=True,
    )

  st.markdown("<br>", unsafe_allow_html=True)
  st.markdown("#### ⚽ Classifica Attaccanti")
  sorted_a = sorted(
      db["punti_attaccanti"].items(),
      key=lambda x: (x[1], db["dr_attaccanti"].get(x[0], 0)),
      reverse=True,
  )
  for idx, (a, pt) in enumerate(sorted_a):
    gioc, tot = calcola_partite_giocate("attaccante", a)
    dr_a = db["dr_attaccanti"].get(a, 0)
    card_class = "rank-card-green" if idx < 8 else "rank-card-red"
    st.markdown(
        f"""
      <div class="{card_class}">
        <div><b>{idx+1}°</b> &nbsp; ⚽ &nbsp; <b>{a}</b></div>
        <div style="color: #cbd5e1; font-size: 0.95rem;">Punti: <b>{pt}</b> &nbsp;|&nbsp; Diff. Reti: <b>{dr_a:+d}</b> &nbsp;|&nbsp; Partite: {gioc}/{tot}</div>
      </div>
    """,
        unsafe_allow_html=True,
    )
