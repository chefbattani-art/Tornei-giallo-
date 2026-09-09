def genera_calendario_corretto(portieri, attaccanti, num_turni, num_tavoli):
  p_list = list(portieri)
  a_list = list(attaccanti)

  turni_partite = []
  compagni_precedenti = set()
  avversari_precedenti = set()
  ruoli_riposo_per_turno = {}

  is_portieri_in_eccesso = len(p_list) > len(a_list)

  def risolvi_turno(t):
    if t > num_turni:
      return True

    p_curr = list(p_list)
    a_curr = list(a_list)

    # Gestione riposi bilanciati
    if is_portieri_in_eccesso:
      idx_riposo_p = (t - 1) % len(p_curr)
      portiere_in_riposo = p_curr.pop(idx_riposo_p)
      ruoli_riposo_per_turno[t] = ("portiere", portiere_in_riposo)
    else:
      idx_riposo_a = (t - 1) % len(a_curr)
      attaccante_in_riposo = a_curr.pop(idx_riposo_a)
      ruoli_riposo_per_turno[t] = ("attaccante", attaccante_in_riposo)

    # Tentativi multipli di shuffle per il backtracking del turno
    for _ in range(1500):
      p_temp = list(p_curr)
      a_temp = list(a_curr)
      random.shuffle(p_temp)
      random.shuffle(a_temp)

      coppie_questo_turno = set()
      scontri_questo_turno = set()
      partite_tentative = []
      turno_valido = True

      i = 0
      while i < len(p_temp) and i + 1 < len(p_temp):
        p1, a1 = p_temp[i], a_temp[i]
        p2, a2 = p_temp[i + 1], a_temp[i + 1]

        squadra_1 = tuple(sorted([p1, a1]))
        squadra_2 = tuple(sorted([p2, a2]))

        # 1. Controllo compagni già fatti
        if (
            squadra_1 in compagni_precedenti
            or squadra_1 in coppie_questo_turno
            or squadra_2 in compagni_precedenti
            or squadra_2 in coppie_questo_turno
        ):
          turno_valido = False
          break

        # 2. Controllo avversari già incontrati (portiere/attaccante contro chiunque)
        giocatori_s1 = [p1, a1]
        giocatori_s2 = [p2, a2]
        conflitto_avversari = False
        scontri_singoli = []

        for g_a in giocatori_s1:
          for g_b in giocatori_s2:
            coppia_avversaria = tuple(sorted([g_a, g_b]))
            if (
                coppia_avversaria in avversari_precedenti
                or coppia_avversaria in scontri_questo_turno
            ):
              conflitto_avversari = True
              break
            scontri_singoli.append(coppia_avversaria)
          if conflitto_avversari:
            break

        if conflitto_avversari:
          turno_valido = False
          break

        coppie_questo_turno.add(squadra_1)
        coppie_questo_turno.add(squadra_2)
        for c_avv in scontri_singoli:
          scontri_questo_turno.add(c_avv)

        partite_tentative.append({
            "p1": p1,
            "a1": a1,
            "p2": p2,
            "a2": a2,
            "compagni": [squadra_1, squadra_2],
            "avversari": scontri_singoli,
        })
        i += 2

      if turno_valido:
        # Registriamo definitivamente i vincoli per questo turno
        for m_data in partite_tentative:
          for comp in m_data["compagni"]:
            compagni_precedenti.add(comp)
          for avv in m_data["avversari"]:
            avversari_precedenti.add(avv)

        partite_turno = []
        for match_idx, m_data in enumerate(partite_tentative):
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

        # Aggiunta riga di riposo
        tipo_rip, nome_rip = ruoli_riposo_per_turno[t]
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

        turni_partite.append({"turno": t, "partite": partite_turno})

        # Ricorsione al turno successivo
        if risolvi_turno(t + 1):
          return True

        # Backtracking: se i turni successivi si bloccano, annulliamo le scelte di questo turno
        turni_partite.pop()
        for m_data in partite_tentative:
          for comp in m_data["compagni"]:
            compagni_precedenti.remove(comp)
          for avv in m_data["avversari"]:
            avversari_precedenti.remove(avv)
        break

    return False

  # Avvio generazione dal Turno 1
  risolvi_turno(1)

  # Gestione turni extra di recupero (invariata rispetto al tuo codice originale)
  elementi_da_recuperare = [val[1] for val in ruoli_riposo_per_turno.values()]
  if len(elementi_da_recuperare) > 0:
    random.shuffle(elementi_da_recuperare)
    turno_num = num_turni + 1
    partite_turno_extra = []
    match_idx = 0

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

          match_id = f"t{turno_num}_m{match_idx}"
          partite_turno_extra.append({
              "id": match_id,
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
