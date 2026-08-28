st.markdown("---")
st.markdown("### 📅 Partite dei Turni (Archivio)")

for turno_obj in db["turni_partite"]:
  turno_num = turno_obj["turno"]
  turno_nome_str = str(turno_num)
  is_extra = "Extra" in turno_nome_str or "Recupero" in turno_nome_str

  tutte_giocate = all(m.get("giocata", False) for m in turno_obj["partite"])
  alcuna_giocata = any(m.get("giocata", False) for m in turno_obj["partite"])
  in_corso = alcuna_giocata and not tutte_giocate

  if is_extra:
    header_text = f"⭐ {turno_num} (TURNO EXTRA FINALE - RECUPERO PRESENZE)"
    expander_border = "#fbbf24"
    espanso_default = True
  elif tutte_giocate:
    header_text = f"Turno {turno_num} (Completato ✅)"
    expander_border = "#2563eb"
    espanso_default = False
  elif in_corso:
    header_text = f"Turno {turno_num} (In corso ⏳)"
    expander_border = "#2563eb"
    espanso_default = True
  else:
    header_text = f"Turno {turno_num} (Da giocare ⏳)"
    expander_border = "#2563eb"
    espanso_default = False

  with st.expander(header_text, expanded=espanso_default):
    if is_extra:
      portieri_in_rec = set()
      for m_rec in turno_obj["partite"]:
        portieri_in_rec.add(m_rec["p1"])
        portieri_in_rec.add(m_rec["p2"])
      str_portieri = ", ".join(portieri_in_rec)

      st.html(
          f"""
              <div style="background: linear-gradient(135deg, #451a03, #78350f); border: 2px solid #fbbf24; border-radius: 12px; padding: 16px; margin-bottom: 14px; color: #f8fafc; box-shadow: 0 0 20px rgba(251, 191, 36, 0.4);">
                  <div style="color: #fbbf24; font-weight: 800; font-size: 1.15rem; margin-bottom: 8px;">⭐ TURNO EXTRA: RECUPERO PARTITE MANCANTI</div>
                  <div style="font-size: 0.98rem; margin-bottom: 8px;">Questo turno extra è posizionato in fondo alla lista e serve a far pareggiare il numero di incontri a tutti gli attaccanti.</div>
                  <div style="font-size: 0.92rem; color: #38bdf8; font-weight: 600;">Portieri in campo per supporto (NON prenderanno punti/statistiche in questa specifica sessione):</div>
                  <div style="margin-top: 6px; font-weight: 700; color: #ffffff;">> {str_portieri}</div>
              </div>
          """
      )

    for idx, m in enumerate(turno_obj["partite"]):
      tavolo_num = (idx % num_tavoli) + 1
      match_id = m["id"]

      if m["giocata"]:
        box_bg = "linear-gradient(135deg, #450a0a, #7f1d1d)"
        border_color = "#ef4444"
        text_content = f"<div style='color: #fbbf24; font-size: 1.1rem; font-weight: 700; margin: 6px 0;'>Risultato: {m['gol1']} - {m['gol2']}</div>"
        label_stato = f"Biliardino {tavolo_num} (Giocata ✅)"
      else:
        box_bg = (
            "linear-gradient(135deg, #451a03, #78350f)"
            if is_extra
            else "linear-gradient(135deg, #022c22, #064e3b)"
        )
        border_color = "#fbbf24" if is_extra else "#22c55e"
        text_content = "<div style='color: #fbbf24; font-size: 1.1rem; font-weight: 800; margin: 6px 0;'>VS</div>"
        label_stato = f"Biliardino {tavolo_num}"

      st.html(
          f"""
                  <div style="background: {box_bg}; border: 1px solid {border_color}; border-radius: 12px; padding: 14px; margin-bottom: 10px; color: white; text-align: center;">
                      <div style="font-weight: 700; margin-bottom: 6px; font-size: 0.95rem; text-transform: uppercase; color: #00f2fe;">{label_stato}</div>
                      <div style="font-size: 1rem; font-weight: 600; color: #f8fafc;">🥅 {m['p1']} / ⚽ {m['a1']}</div>
                      {text_content}
                      <div style="font-size: 1rem; font-weight: 600; color: #f8fafc;">🥅 {m['p2']} / ⚽ {m['a2']}</div>
                  </div>
              """
      )

      if is_admin:
        with st.expander(
            f"⚙️ Modifica Risultato Biliardino {tavolo_num} (Admin)",
            expanded=False,
        ):
          st.markdown(f"**🥅 {m['p1']} / ⚽ {m['a1']} (Gol Coppia 1)**")
          curr_m1 = int(m.get("gol1", 0))
          rc1 = st.columns(4)
          for g_val in range(4):
            with rc1[g_val]:
              sel_m1 = curr_m1 == g_val
              lbl_m1 = f"⭐ {g_val}" if sel_m1 else str(g_val)
              if st.button(
                  lbl_m1,
                  key=f"adm_g1_{match_id}_{g_val}",
                  use_container_width=True,
              ):
                m["gol1"] = g_val
                salva_dati(db)
                st.rerun()
          rc2 = st.columns(4)
          for g_val in range(4, 8):
            with rc2[g_val - 4]:
              sel_m1 = curr_m1 == g_val
              lbl_m1 = f"⭐ {g_val}" if sel_m1 else str(g_val)
              if st.button(
                  lbl_m1,
                  key=f"adm_g1_{match_id}_{g_val}",
                  use_container_width=True,
              ):
                m["gol1"] = g_val
                salva_dati(db)
                st.rerun()

          st.markdown(
              "<div style='margin: 8px 0;'></div>", unsafe_allow_html=True
          )
          st.markdown(f"**🥅 {m['p2']} / ⚽ {m['a2']} (Gol Coppia 2)**")
          curr_m2 = int(m.get("gol2", 0))
          rc3 = st.columns(4)
          for g_val in range(4):
            with rc3[g_val]:
              sel_m2 = curr_m2 == g_val
              lbl_m2 = f"⭐ {g_val}" if sel_m2 else str(g_val)
              if st.button(
                  lbl_m2,
                  key=f"adm_g2_{match_id}_{g_val}",
                  use_container_width=True,
              ):
                m["gol2"] = g_val
                salva_dati(db)
                st.rerun()
          rc4 = st.columns(4)
          for g_val in range(4, 8):
            with rc4[g_val - 4]:
              sel_m2 = curr_m2 == g_val
              lbl_m2 = f"⭐ {g_val}" if sel_m2 else str(g_val)
              if st.button(
                  lbl_m2,
                  key=f"adm_g2_{match_id}_{g_val}",
                  use_container_width=True,
              ):
                m["gol2"] = g_val
                salva_dati(db)
                st.rerun()

          st.markdown(
              "<div style='margin: 10px 0;'></div>", unsafe_allow_html=True
          )
          if st.button(
              "💾 Salva Modifica",
              key=f"save_{match_id}",
              use_container_width=True,
          ):
            m["giocata"] = True
            ricalcola_classifiche()
            salva_dati(db)
            st.success("Salvato!")
            st.rerun()
