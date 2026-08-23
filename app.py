# 2. GIRONI
if db["stato"] == "gironi":
    ricalcola_classifiche()
    num_tavoli = db.get("num_tavoli", 3)

    partite_in_corso = []
    partite_in_coda = []

    for turno_obj in db["turni_partite"]:
        for idx, m in enumerate(turno_obj["partite"]):
            tavolo_num = (idx % num_tavoli) + 1
            if not m["giocata"]:
                info_m = {"turno": turno_obj["turno"], "tavolo": tavolo_num, "m": m}
                if m.get("in_corso", False):
                    partite_in_corso.append(info_m)
                else:
                    partite_in_coda.append(info_m)

    # Limitiamo le partite in corso esattamente al numero di tavoli disponibili
    partite_in_corso = partite_in_corso[:num_tavoli]

    # 1. SEZIONE PARTITE IN CORSO (SFONDO GIALLO)
    if partite_in_corso:
        st.markdown(
            """
            <div style="padding: 10px; background-color: #fffde7; border: 2px solid #ffd54f; border-radius: 6px; margin-bottom: 10px;">
                <h4 style="margin: 0; color: #f57f17;">🔥 PARTITE IN CORSO (Sui biliardini):</h4>
            </div>
            """,
            unsafe_allow_html=True
        )
        for item in partite_in_corso:
            m = item["m"]
            match_id = m['id']
            
            st.markdown(f"""
                <div style="padding: 8px; background-color: #fffde7; border: 1px solid #ffe082; border-radius: 6px; margin-bottom: 8px;">
                    <b>📍 Biliardino {item['tavolo']} (Turno {item['turno']})</b><br>
                    🥅 {m['p1']} &nbsp;&nbsp;|&nbsp;&nbsp; ⚽ {m['a1']}<br>
                    🥅 {m['p2']} &nbsp;&nbsp;|&nbsp;&nbsp; ⚽ {m['a2']}
                </div>
            """, unsafe_allow_html=True)
            
            if is_admin:
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("⏹️ Ferma", key=f"stop_{match_id}", use_container_width=True):
                        m["in_corso"] = False
                        salva_dati(db)
                        st.rerun()
                with col_btn2:
                    with st.expander("⚙️ Gestisci Risultato"):
                        rg1 = st.radio("Gol S1", list(range(8)), index=int(m.get('gol1', 0)), horizontal=True, key=f"rg1_{match_id}")
                        rg2 = st.radio("Gol S2", list(range(8)), index=int(m.get('gol2', 0)), horizontal=True, key=f"rg2_{match_id}")
                        if st.button("💾 Salva Risultato", key=f"save_{match_id}", use_container_width=True):
                            m['gol1'] = rg1
                            m['gol2'] = rg2
                            m['giocata'] = True
                            m['in_corso'] = False
                            ricalcola_classifiche()
                            salva_dati(db)
                            st.rerun()
            st.markdown("---")

    # 2. SEZIONE PARTITE IN CODA (SFONDO VERDE)
    if partite_in_coda:
        st.markdown(
            """
            <div style="padding: 10px; background-color: #e8f5e9; border: 2px solid #81c784; border-radius: 6px; margin-bottom: 10px;">
                <h4 style="margin: 0; color: #2e7d32;">📢 PROSSIMI IN CODA (Preparatevi):</h4>
            </div>
            """,
            unsafe_allow_html=True
        )
        # 🔹 LIMITIAMO LE PARTITE IN CODA ESATTAMENTE AL NUMERO DI TAVOLI (uguali a quelle in corso)
        for item in partite_in_coda[:num_tavoli]:
            m = item["m"]
            match_id = m['id']
            
            st.markdown(f"""
                <div style="padding: 8px; background-color: #e8f5e9; border: 1px solid #c8e6c9; border-radius: 6px; margin-bottom: 8px;">
                    <b>👉 In Coda (Turno {item['turno']})</b><br>
                    🥅 {m['p1']} &nbsp;&nbsp;|&nbsp;&nbsp; ⚽ {m['a1']}<br>
                    🥅 {m['p2']} &nbsp;&nbsp;|&nbsp;&nbsp; ⚽ {m['a2']}
                </div>
            """, unsafe_allow_html=True)
            
            if is_admin:
                if st.button("▶️ Avvia Partita", key=f"start_{match_id}", use_container_width=True):
                    m["in_corso"] = True
                    salva_dati(db)
                    st.rerun()
            st.markdown("---")
