from app import app, db, Camera  # Assicurati di importare il tuo oggetto app e il modello Camera # Cambia `your_module` con il nome della tua cartella o file contenente il tuo modello

#questa parte di codice mi consente di popolare il db con le camere disponibili in struttura ogni qualvolta avvio l'app se è
# necessario o succede qualche problem col db

# Funzione per inizializzare il database inserendo le camere
def init_db():
    with app.app_context():
        # Assicurati che il database sia stato inizializzato
        db.create_all()

        # Aggiungi alcune camere
        camera1 = Camera(nome='Tripla Deluxe', immagine='images/tripla_deluxe.jpg', descrizione='Una camera tripla molto costosa', disponibile=True, prezzo = 100, max_persone = 3)
        camera2 = Camera(nome='Doppia Deluxe', immagine='images/doppia_deluxe.jpg', descrizione='Una camera doppia tanto costosa', disponibile=True, prezzo=80, max_persone = 2)
        camera3 = Camera(nome='Singola Deluxe', immagine='images/singola_deluxe.jpg', descrizione='Una camera singola costosissima', disponibile=True, prezzo=60, max_persone = 1)
        camera4 = Camera(nome='Tripla Economica', immagine='images/tripla_economica.jpg', descrizione='Una camera tripla per poveri', disponibile=True,prezzo=40, max_persone = 3)
        camera5 = Camera(nome='Doppia Economica', immagine='images/doppia_economica.jpg', descrizione='Una camera doppia per poveri', disponibile=True,prezzo=25, max_persone = 2)
        camera6 = Camera(nome='Singola Economica', immagine='images/singola_economica.jpg', descrizione='Una camera singola per poveri', disponibile=True,prezzo=15 , max_persone = 1)

        # Aggiungi altre camere come necessario
        db.session.add(camera1)
        db.session.add(camera2)
        db.session.add(camera3)
        db.session.add(camera4)
        db.session.add(camera5)
        db.session.add(camera6)
        # Commetti le modifiche al database
        db.session.commit()
        print("Database inizializzato e popolato con camere.")
# Esegui l'inizializzazione
if __name__ == '__main__':
    init_db()
