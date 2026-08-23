# 3. ELIMINATORIE
elif db["stato"] == "eliminatorie":
    st.subheader("🏆 Fasi Finali a Eliminazione Diretta")
    num_tavoli = db.get("num_tavoli", 2)
    
    fasi = db["fasi_finali"]
    
    for f_idx, f_turno in enumerate(fasi):
        st.markdown(f"### 🔥 {f_turno['nome']} (Turno {f_turno['turno']})")
        
        tutti_giocati = True
        vincitori_turno = []
        perdenti_turno = []
        
        for idx, m in enumerate(f_turno["partite"]):
            tavolo_num = (idx % num_tavoli) + 1
            match_id = m['id']

            if m.get("giocata", False):
                if m["gol1"] >= m["gol2"]:
                    vincitori_turno.append({"p": m["p1"], "a": m["a1"]})
                    perdenti_turno.append({"p": m["p2"], "a": m["a2"]})
                else:
                    vincitori_turno.append({"p": m["p2"], "a": m["a2"]})
                    perdenti_turno.append({"p": m["p1"], "a": m["a1"]})
            else:
                tutti_giocati = False

            st.markdown(f"**📍 Biliardino {tavolo_num}**")
            col_s1, col_mid, col_s2 = st.columns([4, 2.5, 4], gap="small")
            
            with col_s1:
                st.info(f"🥅 **{m['p1']}**\n\n⚽ **{m['a1']}**")
            
            with col_mid:
                if m["giocata"]:
                    st.error(f"🛑 **{m['gol1']} - {m['gol2']}**")
                elif m.get("in_corso", False):
                    st.warning("🔥 **In Corso**")
                else:
                    st.write("**VS**")
                    if is_admin:
                        if st.button("▶️ Avvia", key=f"ef_btn_{match_id}", use_container_width=True):
                            m["in_corso"] = True
                            salva_dati(db)
                            st.rerun()
                
                if is_admin:
                    with st.expander("⚙️ Gestisci Risultato"):
                        rg1 = st.radio("Gol S1", list(range(8)), index=int(m.get('gol1', 0)), horizontal=True, key=f"ef_rg1_{match_id}")
                        rg2 = st.radio("Gol S2", list(range(8)), index=int(m.get('gol2', 0)), horizontal=True, key=f"ef_rg2_{match_id}")
                        if st.button("💾 Salva", key=f"ef_save_{match_id}", use_container_width=True):
                            m['gol1'] = rg1
                            m['gol2'] = rg2
                            m['giocata'] = True
                            m['in_corso'] = False
                            salva_dati(db)
                            st.success("Salvato!")
                            st.rerun()

            with col_s2:
                st.info(f"🥅 **{m['p2']}**\n\n⚽ **{m['a2']}**")
            st.markdown("---")

        # 1. Generazione Semifinali dai Quarti
        if tutti_giocati and is_admin:
            if f_turno['nome'] == "Quarti di Finale" and len(vincitori_turno) == 4 and not any(f['nome'] == "Semifinali" for f in fasi):
                # vincitori_turno[0] = Q1, [1] = Q2, [2] = Q3, [3] = Q4
                semifinale_partite = [
                    {
                        "id": "ef_t2_m1", 
                        "p1": vincitori_turno[0]["p"], "a1": vincitori_turno[1]["a"],  # Portiere Q1 + Attaccante Q2
                        "p2": vincitori_turno[3]["p"], "a2": vincitori_turno[2]["a"],  # Portiere Q4 + Attaccante Q3
                        "giocata": False, "in_corso": False, "gol1": 0, "gol2": 0
                    },
                    {
                        "id": "ef_t2_m2", 
                        "p1": vincitori_turno[0]["p"], "a1": vincitori_turno[1]["a"],  # Portiere Q1 + Attaccante Q2
                        "p2": vincitori_turno[2]["p"], "a2": vincitori_turno[3]["a"],  # Portiere Q3 + Attaccante Q4
                        "giocata": False, "in_corso": False, "gol1": 0, "gol2": 0
                    }
                ]
                db["fasi_finali"].append({"turno": 2, "nome": "Semifinali", "partite": semifinale_partite})
                salva_dati(db)
                st.success("Semifinali generate con i tuoi incroci esatti!")
                st.rerun()
                
            # 2. Generazione Finali (1°-2° e 3°-4°) dalle Semifinali
            elif f_turno['nome'] == "Semifinali" and len(vincitori_turno) == 2 and not any(f['nome'] == "Finali" for f in fasi):
                # SF1 vincente = vincitori_turno[0], SF2 vincente = vincitori_turno[1]
                # SF1 perdente = perdenti_turno[0], SF2 perdente = perdenti_turno[1]
                
                sf1_v = vincitori_turno[0]
                sf2_v = vincitori_turno[1]
                sf1_p = perdenti_turno[0]
                sf2_p = perdenti_turno[1]
                
                finali_partite = [
                    {
                        "id": "ef_t3_m1", 
                        "nome_partita": "🥇 Finalissima (1° - 2° Posto)",
                        "p1": sf2_v["p"], "a1": sf1_v["a"],  # Portiere SF2 + Attaccante SF1
                        "p2": sf1_v["p"], "a2": sf2_v["a"],  # Portiere SF1 + Attaccante SF2
                        "giocata": False, "in_corso": False, "gol1": 0, "gol2": 0
                    },
                    {
                        "id": "ef_t3_m2", 
                        "nome_partita": "🥉 Finale 3° - 4° Posto",
                        "p1": sf2_p["p"], "a1": sf1_p["a"],  # Portiere perdente SF2 + Attaccante perdente SF1
                        "p2": sf1_p["p"], "a2": sf2_p["a"],  # Portiere perdente SF1 + Attaccante perdente SF2
                        "giocata": False, "in_corso": False, "gol1": 0, "gol2": 0
                    }
                ]
                db["fasi_finali"].append({"turno": 3, "nome": "Finali (1°-2° e 3°-4° Posto)", "partite": finali_partite})
                salva_dati(db)
                st.success("Finali generate con successo!")
                st.rerun()
