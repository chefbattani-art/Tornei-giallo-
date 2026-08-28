        elif scelta_utente != "-- Seleziona il tuo nome --":
          st.query_params["giocatore"] = scelta_utente
          st.rerun()
        st.stop()
      else:
        # Aggiunta del collaboratore alla barra utente
        if "collaboratore" not in st.session_state:
          st.session_state.collaboratore = "Gemini"

        col_n1, col_n2, col_n3 = st.columns([2, 1, 1])
        with col_n1:
          st.markdown(
              f"""
                    <div style="background: #080e1e; padding: 12px 18px; border-radius: 12px; border: 1px solid #00f2fe; font-weight: 600; color: #f8fafc; font-size: 1.05rem; box-shadow: 0 0 10px rgba(0, 242, 254, 0.2);">
                        👤 Stai visualizzando come: <span style="color: #fbbf24; font-weight: 700;">{giocatore_selezionato}</span>
                    </div>
                """,
              unsafe_allow_html=True,
          )

          ricalcola_classifiche()
          sorted_p_temp = sorted(
              db["punti_portieri"].items(),
              key=lambda x: (x[1], db["dr_portieri"].get(x[0], 0)),
              reverse=True,
          )
          sorted_a_temp = sorted(
              db["punti_attaccanti"].items(),
              key=lambda x: (x[1], db["dr_attaccanti"].get(x[0], 0)),
              reverse=True,
          )

          pos_str = "N/D"
          punti_val = 0
          if giocatore_selezionato in db["portieri"]:
            for idx, (p, pt) in enumerate(sorted_p_temp):
              if p == giocatore_selezionato:
                pos_str = f"{idx+1}° (Portiere)"
                punti_val = pt
                break
          elif giocatore_selezionato in db["attaccanti"]:
            for idx, (a, pt) in enumerate(sorted_a_temp):
              if a == giocatore_selezionato:
                pos_str = f"{idx+1}° (Attaccante)"
                punti_val = pt
                break

          st.markdown(
              f"""
                <div style="border: 2px solid #00ffff; border-radius: 10px; padding: 10px; margin-top: 10px; margin-bottom: 10px; background-color: rgba(0, 255, 255, 0.05); text-align: center; color: white; font-family: sans-serif;">
                    <span style="font-size: 13px; color: #00ffff; font-weight: 600;">LA TUA SITUAZIONE</span><br>
                    <b style="font-size: 15px;">Posizione:</b> {pos_str} &nbsp;&nbsp;|&nbsp;&nbsp; 
                    <b style="font-size: 15px;">Punti:</b> {punti_val}
                </div>
                """,
              unsafe_allow_html=True,
          )
        with col_n2:
          st.markdown(
              f"""
                    <div style="background: #080e1e; padding: 12px 18px; border-radius: 12px; border: 1px solid #22c55e; font-weight: 600; color: #f8fafc; font-size: 1.05rem; box-shadow: 0 0 10px rgba(34, 197, 94, 0.2); text-align: center;">
                        🤖 Collaboratore: <span style="color: #4ade80; font-weight: 700;">{st.session_state.collaboratore}</span>
                    </div>
                """,
              unsafe_allow_html=True,
          )
        with col_n3:
          if st.button("🔄 Cambia Nome", use_container_width=True):
            st.query_params.clear()
            st.rerun()
        st.markdown("---")
    else:
      giocatore_selezionato = "-- Seleziona il tuo nome --"
