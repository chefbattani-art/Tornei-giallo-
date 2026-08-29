        with st.expander(f"⚙️ Inserisci Risultato Biliardino {tavolo_num} (Turno {t_obj['turno']})", expanded=st.session_state[exp_key_open]):
          with st.form(key=f"form_{m['id']}"):
            st.write("Inserisci i goal assegnati a ciascuna squadra:")
            
            curr_g1 = int(m.get("gol1", 0))
            curr_g2 = int(m.get("gol2", 0))
            
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                st.markdown(f'<b>🥅 {m["p1"]} & {m["a1"]}</b>', unsafe_allow_html=True)
                nuovo_g1 = st.number_input("Gol S1", min_value=0, max_value=15, value=curr_g1, key=f"num_g1_{m['id']}", label_visibility="collapsed")
            with col_g2:
                st.markdown(f'<b>🥅 {m["p2"]} & {m["a2"]}</b>', unsafe_allow_html=True)
                nuovo_g2 = st.number_input("Gol S2", min_value=0, max_value=15, value=curr_g2, key=f"num_g2_{m['id']}", label_visibility="collapsed")
            
            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button("Salva Risultato", use_container_width=True)
            if submitted:
              m["gol1"] = int(nuovo_g1)
              m["gol2"] = int(nuovo_g2)
              m["giocata"] = True
              ricalcola_classifiche()
              salva_dati(db)
              st.session_state[exp_key_open] = False
              st.rerun()
