from app import app, db, Camera  # Assicurati di importare il tuo oggetto app e il modello Camera
from app import Camera  # Cambia `your_module` con il nome della tua cartella o file contenente il tuo modello

#questa parte di codice mi consente di popolare il db con le camere disponibili in struttura ogni qualvolta avvio l'app se è
# necessario o succede qualche problem col db

# Funzione per inizializzare il database inserendo le camere
def init_db():
    with app.app_context():
        # Assicurati che il database sia stato inizializzato
        db.create_all()

        # Aggiungi alcune camere
        camera1 = Camera(nome='Tripla Deluxe', immagine='images/tripla_deluxe.jpg', descrizione='Una camera spaziosa con letto matrimoniale e due letti singoli.')
        camera2 = Camera(nome='Doppia Deluxe', immagine='images/doppia_deluxe.jpg', descrizione='Una camera doppia costosa')
        camera3 = Camera(nome='Singola Deluxe', immagine='images/singola_deluxe.jpg', descrizione='Una camera singola costosissima')
        camera4 = Camera(nome='Tripla Economica', immagine='images/tripla_economica.jpg', descrizione='Una camera tripla per poveri')
        camera5 = Camera(nome='Doppia Economica', immagine='images/doppia_economica.jpg', descrizione='Una camera doppia per poveri')
        camera6 = Camera(nome='Singola Economica', immagine='images/singola_economica.jpg', descrizione='Una camera singola per poveri')

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
