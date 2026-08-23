def calcola_orario_stimato_fine():
    if db["stato"] != "gironi":
        return None
        
    num_tavoli = db.get("num_tavoli", 3)
    
    totale_partite = 0
    partite_giocate = 0
    for turno_obj in db["turni_partite"]:
        for m in turno_obj["partite"]:
            totale_partite += 1
            if m.get("giocata", False):
                partite_giocate += 1
                
    if partite_giocate == 0:
        return "In attesa di dati..."
        
    if partite_giocate >= totale_partite:
        return "Completato ✅"
        
    partite_mancanti = totale_partite - partite_giocate
    t_attuale = datetime.now()
    
    # Stimiamo 5 minuti (300 secondi) a partita in modo stabile
    durata_media_sec = 300 

    giri_rimanenti = partite_mancanti / num_tavoli
    tempo_rimanente_sec = giri_rimanenti * durata_media_sec
    
    orario_stimato = t_attuale + timedelta(seconds=tempo_rimanente_sec)
    return orario_stimato.strftime("%H:%M")
