
# importo varie librerie e moduli di flask necessarie per far funzionare l'applicativo
from flask import Flask, request, jsonify, redirect, url_for, session, render_template, flash
# import dell'ORM di flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
# import della libreria relativa per l'hashing delle password
import bcrypt
# import della libreria relativa per la funzione di generazione numeri casuali(mi serve per il codice prenotazione)
import random
# import della libreria secrets per generare numeri o stringhe sicuri per l'uso in contesti critici(mi serve per le generazione di tokens)
import secrets
# import della libreria relativa per effettuare le migrazioni al db
from flask_migrate import Migrate
# import libreria di python che mi consente di connettermi ad un server per inviare email
# il simple mail transfer protocol è parte della libreria standard di Python per la manipolazione e l'invio di email.
import smtplib
# import di libreria e moduli che mi agevolano nella creazione del corpo della funzione per inviare la mail e per il suo contento
from flask_mail import Mail, Message
from email.mime.text import MIMEText
# import della libreria relativa per poter manipolare i dati di tipo datetime
from datetime import datetime

# settaggio base di flask
app = Flask(__name__)
app.secret_key = 'mia_chiave_esempio'
# connessione al db in uso
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
# inizializza SQLAlchemy con l'app flask
db = SQLAlchemy(app)
# modulo di flask per gestire le migrazioni del database
migrate = Migrate(app, db)
# moduli di flask per la gestione ed accesso dell'utente che deve autenticarsi
login_manager = LoginManager()
login_manager.init_app(app)

# funzione dedita all'invio della mail prendie in input email destinatario e il codice prenotazione che verrà usato nel corpo della mail
# con la f-string che mi consente di includere e richiamare tale codice per poi così ritornarlo all'utente
def invia_email(email_destinatario, codice_prenotazione):
    msg = MIMEText(
        f"La tua prenotazione è stata effettuata con successo! Ecco il tuo codice prenotazione: {codice_prenotazione}")
    msg['Subject'] = 'Conferma Prenotazione'
    msg['From'] = 'tesimusumeci@gmail.com'
    msg['To'] = email_destinatario

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login('tesimusumeci@gmail.com', 'ignjiuwgurgptfvb')
            server.send_message(msg)

        print(f"Email inviata a {email_destinatario}!")
    except Exception as e:
        print(f"Si è verificato un errore nell'invio dell'email: {e}")


# Modelli
# di seguito vengono definiti i modelli i lori attributi ed i tipi di dato con cui voglio siano salvati nel db poi esser mappati e passati tramite ORM al database
class Prenotazione(db.Model):
    __tablename__ = 'prenotazioni'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cognome = db.Column(db.String(100), nullable=False)
    checkin = db.Column(db.DateTime, nullable=False)
    checkout = db.Column(db.DateTime, nullable=False)
    data_nascita = db.Column(db.DateTime, nullable=False)
    numero_persone = db.Column(db.Integer, nullable=False)
    codice_prenotazione = db.Column(db.String(10), unique=True, nullable=False)
    camera_id = db.Column(db.Integer, db.ForeignKey(
        'camera.id'), nullable=False)
    email = db.Column(db.String(150))
    prezzo_totale = db.Column(db.Integer, nullable=False)
    data_prenotazione = db.Column(db.DateTime, default=datetime.utcnow)

    camera = db.relationship('Camera', back_populates='prenotazioni')


class Camera(db.Model):
    __tablename__ = 'camera'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    immagine = db.Column(db.String(200), nullable=False)
    descrizione = db.Column(db.Text, nullable=True)
    prezzo = db.Column(db.Integer, nullable=False)
    disponibile = db.Column(db.Boolean, default=True)
    max_persone = db.Column(db.Integer, nullable=False)

    prenotazioni = db.relationship('Prenotazione', back_populates='camera')

# modello per il log delle prenotazioni modificate,queste saranno le originali che resteranno salvate nel db
class ModificaPrenotazioneLog(db.Model):
    __tablename__ = 'modifica_prenotazione_log'

    id = db.Column(db.Integer, primary_key=True)
    codice_prenotazione = db.Column(db.String(10), db.ForeignKey(
        'prenotazioni.codice_prenotazione'), nullable=False)
    nome_originario = db.Column(db.String(100), nullable=True)
    cognome_originario = db.Column(db.String(100), nullable=False)
    checkin_originario = db.Column(db.String(10), nullable=False)
    checkout_originario = db.Column(db.String(10), nullable=False)
    numero_persone_originario = db.Column(db.Integer, nullable=False)
    email_originaria = db.Column(db.String(150), nullable=True)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())


# uso UserMixin per gestire le logiche di login e logout , il modello user estende questa classe della libreria
# Flask-login imcludendo alcuni metodi già predefiniti che aiutano nel definire la logica per l'autenticazione
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)

# funzione per creare l'admin da terminal con hashing della password crea il record nel db ed effettuare il commit


@app.cli.command('create-admin')
def create_admin():
    """Crea un admin."""
    username = input("Inserisci il nome utente per l'admin: ")
    password = input("Inserisci la password per l'admin: ")

    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    new_user = User(username=username, password=hashed_pw, is_admin=True)

    db.session.add(new_user)
    db.session.commit()
    print(f"Admin {username} creato")


# Rotte

# rotta che mi ritorna l'homepage del sito
@app.route('/')
def home():
    return render_template('homepage.html')

# decoratore della libreria Flask-log in per gestire la sessione dell'utente che si autentica
# la funzione prende come parametro proprio l'id legato alla registrazione dello User , attributo definito nel modello

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# rotta per la funzione di log in dell'admin
# metodi sia get che post in quanto alla def login dico, se la richiesta è di tipo post allora ritorna i dati compilati del form dopo verifica
# che quello user sia un user presente nel db, dato che l'unico auth che ho fatto è per l'admin e l'unico user sarà l'admin qualora ci siano user registrati saranno admin
# quindi fai un query filtra e se i dati sono presenti e corrispondono (passowrd hashata nel db)
# allora chiama la funzione login_user effettua il login e vai alla pagina dell'admin
# se user e password  tra dati inserite e dati presenti nel db non matchano ritornami al form di login presente in admin.html


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.form
        user = User.query.filter_by(username=data['username']).first()
        if user and bcrypt.checkpw(data['password'].encode('utf-8'), user.password):
            login_user(user)
            return redirect(url_for('admin_page'))
        return "Credenziali errate."
    return render_template('admin.html')

# rotta di logout per l'admin


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


# rotta connessa con la pagina di prenotazione generale delle camera, una sorta di pagina di presentazione delle camere disponibili
# effettua una query e mostra appunto tutte le camere presenti nel database con valore settato a true, quelle settate a false saranno
# quelle rese non disponibili nella pagina di gestione admin, ho impostato cosi la logica.
@app.route('/prenota')
def prenota():
    camere_disponibili = Camera.query.filter_by(disponibile=True).all()
    return render_template('prenota_generale.html', camere=camere_disponibili)

# rotta della triste ma comunque meritevole di diritti pagina about


@app.route('/about')
def about():
    return render_template('about.html')

# rotta col form per il login admin
# username e passowrd admin root:root
@app.route('/admin')
@login_required
def admin_page():
    return render_template('admin.html')


# rotta parametrica , prende in input l'id specifico di ogni camera cosi da dispormi le info specifiche della camera selezionata una volta che vado
# nella pagina di prenotazione, ogni camera per esempio ha un numero massimo di persone consentito, un suo prezzo per notte,può essere libera o prenotata in specifiche date
# relative proprio a quella camera (camere_id)
@app.route('/prenota/<int:camera_id>', methods=['GET', 'POST'])
def prenota_camera(camera_id):

    # alla variabile camera assegno una query che mi ritorna la camera con lo specifico ID salvato nel db
    # e ritornami il template di camera_specifica.html con ciò che voglio visualizzare(si vede nel frontend)di quella specifica camera (camera_id)
    camera = Camera.query.get(camera_id)

    # a meno chè questo id quindi questa camera non è presente nel DB allora
    if not camera:
        return "Camera non trovata", 404


    return render_template('camera_specifica.html', camera=camera, camera_id=camera.id)

# la funzione random.randint genera un numero intero casuale compreso tra 10000 e 99999
# il risultato avrà quindi 5 cifre (saranno il codice prenotazione come la funzione suggerisce) poiché il valore minimo è 10000 e il valore massimo è 99999.


def genera_codice_prenotazione():
    return f'{random.randint(10000, 99999)}'


# rotta parametrica con funzione che al submit invia(method post) i dati della prenotazione al db
# nel frontend sono implementati dei controlli ,se non si passano i controlli non si consente l'invio del modulo

@app.route('/invia_prenotazione/<int:camera_id>', methods=['POST'])
def invia_prenotazione(camera_id):
    # qua ce la parte connessa ai campi/attributi dichiarati nel modello prenotazione che poi si rispecchiano con quelli presenti nel form richiesti nei campi di input
    nome = request.form.get('nome')
    cognome = request.form.get('cognome')
    checkin = request.form.get('checkin')
    checkout = request.form.get('checkout')
    data_nascita = request.form.get('data_nascita')
    numero_persone = request.form.get('numero_persone')
    email = request.form.get('email')

    # nella variabile camera salvo la query che mi ritorna la camera il cui id ho passato alla rotta parametrica
    # se la camera non viene trovata ritornami il messaggio e lo status code 404
    camera = Camera.query.get(camera_id)
    if not camera:
        return "Camera non trovata", 404

# qui calcolo e controllo le nuove date e converto le stringe in oggetti datetime che il è tipo di formato che si aspetta di ricevere il db sennò mi da errore
    checkin_date = datetime.strptime(checkin, '%Y-%m-%d')
    checkout_date = datetime.strptime(checkout, '%Y-%m-%d')
    data_nascita_date = datetime.strptime(data_nascita, '%Y-%m-%d').date()
    numero_notti = (checkout_date - checkin_date).days


# calcolo il prezzo totale mettendo dentro questa variabile il numero notti calcolato su e il prezzo della camera campo prensete nel modello
    prezzo_totale = numero_notti * camera.prezzo
# genero il codice prenotazione e lo salvo nella variabile
    codice_prenotazione = genera_codice_prenotazione()
# elaboro la nuova prenotazione con i dati inseriti
    nuova_prenotazione = Prenotazione(
        nome=nome,
        cognome=cognome,
        checkin=checkin_date,
        checkout=checkout_date,
        data_nascita=datetime.strptime(data_nascita, '%Y-%m-%d'),
        numero_persone=numero_persone,
        codice_prenotazione=codice_prenotazione,
        email=email,
        camera_id=camera_id,
        prezzo_totale=prezzo_totale
    )
# se tutto va bene e si superano i controlli allora procede con aggiungere il nuovo record ed effettua il commit al db
    db.session.add(nuova_prenotazione)
    db.session.commit()
# e procede anche all'invio della mail
    invia_email(email, codice_prenotazione)

    flash('Prenotazione completata con successo!', 'success')
    return redirect(url_for('pagina_conferma', codice_prenotazione=codice_prenotazione))


# nel frontend eseguo una fetch per inviare una richiesta al db che mi restituisse le date di prenotazione di una specifica camera qualora sia prenotata
# ecco a cosa serve queste API, la fetch è presente sia nel file html camera_specifica.html sia ovviamente nel file modifica_prenotazione.html
@app.route('/api/disponibilita_camera/<int:camera_id>', methods=['GET'])
def check_disponibilita_camera(camera_id):

    # per prima cosa richiedo i valori inseriti dall'utente nei campi check in e check out per poterli confrontare dopo
    # quindi request.args.get mi ritorna le date di check in e check out dai parametri di query specificati nella richiesta.
    checkin = request.args.get('checkin')
    checkout = request.args.get('checkout')

    if not checkin or not checkout:
        return jsonify({"error": "Invalid dates."}), 400

# nella variabile prenotazioni effettuo una query che filtra le prenotazioni della camera con quel specifico id
# le query controlla se ci sono prenotazioni esistenti per una camera specifica che sovrappongono le date di check-in e check-out fornite

    prenotazioni = Prenotazione.query.filter(
        Prenotazione.camera_id == camera_id,
        Prenotazione.checkin < checkout,
        Prenotazione.checkout > checkin).all()

# se non ci sono date che si sovrappogono va tutto bene e mi restituisce lo status 200
    if not prenotazioni:
        return jsonify([]), 200

# e per ogni prenotazione trovata restituisce al frontend le date non disponibili cosi da non rendere possibile la prenotazione
# nelle date già prenotate da altri utenti
# in questa variabile inserisco infatti una lista di dizionari dove i valori di checkin e checkout sono resi come stringe nel formato specificato
    unavailable_dates = [{
        "checkin": prenotazione.checkin.strftime('%Y-%m-%d'),
        "checkout": prenotazione.checkout.strftime('%Y-%m-%d')
    } for prenotazione in prenotazioni]

# e ritorno le info con un json che mi restituisce la variabile con dentro quindi le date non disponibili con un status code 200
    return jsonify(unavailable_dates), 200


# rotta che mi consenete di inserire il codice prenotazione e ricevere i dettagli delle prenotazione effettuata
# con un redirect alla pagina di conferma della prenotazione effettuata dove appunto sono presenti tutti i dettagli
@app.route('/verifica_prenotazione', methods=['GET', 'POST'])
def check_prenotazione():
    if request.method == 'POST':
        codice_prenotazione = request.form.get('codice_prenotazione')
        prenotazione = Prenotazione.query.filter_by(
            codice_prenotazione=codice_prenotazione).first()
        if prenotazione:
            return redirect(url_for('pagina_conferma', codice_prenotazione=prenotazione.codice_prenotazione))
        else:
            flash('Prenotazione non trovata. Verifica il codice e riprova.', 'danger')
            return redirect(url_for('check_prenotazione'))
    return render_template('verifica_prenotazione.html')


# in questa rotta ho la pagina di conferma anch'essa parametrica in quanto si aspetta un codice_prenotazione passato come parametro
# nella funzione pagine_conferma effettuo una query filtrata dal codice prenotazione se non lo trova mi da il 404
# altrimenti se la prenotazione è trovata recupera i dettagli della camera utilizzando il 'camera_id' dalla prenotazione
# generami un token per la sessione in corso e rendimi il template 'conferma_prenotazione.html' passando i dati della prenotazione e della camera per la visualizzazione
@app.route('/conferma_prenotazione/<codice_prenotazione>')
def pagina_conferma(codice_prenotazione):
    prenotazione = Prenotazione.query.filter_by(
        codice_prenotazione=codice_prenotazione).first()
    if not prenotazione:
        return "Prenotazione non trovata", 404

    camera = Camera.query.get(prenotazione.camera_id)
    session['elimina_token'] = secrets.token_urlsafe(16)
    return render_template('conferma_prenotazione.html', prenotazione=prenotazione, camera=camera)


@app.route('/modifica_prenotazione/<codice_prenotazione>', methods=['GET', 'POST'])
def modifica_prenotazione(codice_prenotazione):
    # in/con questa variabile reupero la prenotazione dal database usando il codice prenotazione
    prenotazione = Prenotazione.query.filter_by(
        codice_prenotazione=codice_prenotazione).first()


# se la prenotazione non è presente allora
    if not prenotazione:
        return "Prenotazione non trovata", 404

    camera = Camera.query.filter_by(id=prenotazione.camera_id).first()

    # se la camera non è presente allora
    if not camera:
        return "Camera non trovata", 404

    if request.method == 'POST':
        # quando l'utente invia un modulo per modificare la prenotazione,con questa parte di codice
        # verifico che il token fornito nel modulo corrisponda a quello memorizzato nella sessione
        token = session.get('modifica_token')
        if token != request.form.get('token'):
            flash('Token non valido o scaduto.', 'danger')
            return redirect(url_for('home'))

        # qua effettuo il log delle modifiche
        modifica_log = ModificaPrenotazioneLog(
            codice_prenotazione=prenotazione.codice_prenotazione,
            nome_originario=prenotazione.nome,
            cognome_originario=prenotazione.cognome,
            checkin_originario=prenotazione.checkin,
            checkout_originario=prenotazione.checkout,
            numero_persone_originario=prenotazione.numero_persone,
            email_originaria=prenotazione.email
        )
        db.session.add(modifica_log)

        checkin = request.form.get('checkin')
        checkout = request.form.get('checkout')
        data_nascita = request.form.get('data_nascita')
        numero_persone = int(request.form.get('numero_persone'))

        checkin_date = datetime.strptime(checkin, '%Y-%m-%d')
        checkout_date = datetime.strptime(checkout, '%Y-%m-%d')
        numero_notti = (checkout_date - checkin_date).days
        data_nascita_date = datetime.strptime(data_nascita, '%Y-%m-%d').date()

        # aggiorno i campi della prenotazione con i nuovi dati
        prenotazione.nome = request.form.get('nome', prenotazione.nome)
        prenotazione.cognome = request.form.get(
            'cognome', prenotazione.cognome)
        prenotazione.checkin = checkin_date
        prenotazione.checkout = checkout_date
        prenotazione.data_nascita = data_nascita_date
        prenotazione.numero_persone = numero_persone
        prenotazione.email = request.form.get('email', prenotazione.email)

        # ricalcolo il prezzo totale
        prenotazione.prezzo_totale = numero_notti * camera.prezzo

        # e poi salvo le modifiche facendo il commit al db
        db.session.commit()
        flash('Prenotazione aggiornata con successo!', 'success')
        return redirect(url_for('pagina_conferma', codice_prenotazione=prenotazione.codice_prenotazione))

    # genero un nuovo token di sessione per la modifica
    session['modifica_token'] = secrets.token_urlsafe(16)

    # e ritorno il template con i dati della prenotazione e della camera ed il token generato per garantire la persistenza della sessione
    return render_template(
        'modifica_prenotazione.html',
        prenotazione=prenotazione,
        token=session['modifica_token'],
        camera=camera
    )


@app.route('/conferma_eliminazione')
def conferma_eliminazione():
    return render_template('conferma_eliminazione.html')


# in questa rotta parametrica nella funzione che prende in input il codice prenotazione dico :
# ridammi il token generato al momento della prenotazione quindi relativo a quellospecifico codice prenotazione se il token è diverso dalla sessione eliminalo
# e ritornami un errore di non validità del token altrimenti procedi col retrieving della prenotazione e se è true /esiste allora effettua l'eliminazione dal db
# ed effettua il commit disponendo un messaggio con status 200, che conferma l'eliminazione avvenuta con successo.
@app.route('/elimina_prenotazione/<codice_prenotazione>', methods=['GET', 'DELETE'])
def elimina_prenotazione(codice_prenotazione):
    token = request.json.get('token')
    if token != session.get('elimina_token'):
        return jsonify({'message': 'Token non valido'}), 403

    prenotazione = Prenotazione.query.filter_by(
        codice_prenotazione=codice_prenotazione).first()

    if prenotazione:
        db.session.delete(prenotazione)
        db.session.commit()
        return jsonify({'message': 'Prenotazione eliminata con successo.'}), 200
    else:
        return jsonify({'message': 'Prenotazione non trovata'}), 404


# rotte per admin


# nella pagina frontend di log-ing admin tramite JS faccio una fetch per inviare a questo endpoint in formato json le credenziali di accesso admin
@app.route('/api/login', methods=['POST'])
def api_login():
    # ottengo i dati inviati dal client (dal front-end) in formato JSON utilizzando `request.json`
    # e li salvo nella variabile data
    data = request.json
    # ritornami username e password da questi dati salvati nella variabile
    username = data.get('username')
    password = data.get('password')
    # ed effettua una query ritornandomi dove username è uguale all'username passato
    user = User.query.filter_by(username=username).first()
    # se lo user e la password hashata esistono tutto ok ritornami lo status 200
    if user and bcrypt.checkpw(password.encode('utf-8'), user.password):
        login_user(user)
        return jsonify(success=True), 200
    # altrimenti
    else:
        return jsonify(success=False, message='Credenziali errate'), 401



# rotta eslcusiva per l'admin , vediamo infatti il login required che consente il rendering della pagina solo se l'user è autenticato
# mi ritorna tutte le prenotazione presenti nel db più tutto le camere presenti nel db
@app.route('/admin/gestione')
@login_required
def gestione():
    prenotazioni = Prenotazione.query.all()
    camere = Camera.query.all()
    # e mi rendirizza alla pagina gestione.html ritornandomi appunto le prenotazione risultati dalla query e presenti nel db e stessa cosa per le camere
    return render_template('gestione.html', prenotazioni=prenotazioni, camere=camere)



# in questa rotta invio la richiesta dal frontend per settare lo stato della camera a false
@app.route('/admin/camera/<int:camera_id>/non_disponibile', methods=['POST'])
@login_required
def elimina_disponibilita(camera_id):
    camera = Camera.query.get(camera_id)
    if camera:
        camera.disponibile = False
        db.session.commit()
        flash('La camera è stata rimossa dalla disponibilità.', 'success')
    else:
        flash('Camera non trovata.', 'danger')
    return redirect(url_for('gestione'))



# in questa rotta invio la richiesta dal frontend per resettare lo stato della camera a true
@app.route('/admin/camera/<int:camera_id>/disponibile', methods=['POST'])
@login_required
def rendi_disponibile(camera_id):
    camera = Camera.query.get(camera_id)
    if camera:
        camera.disponibile = True
        db.session.commit()
        flash('La camera è stata resa disponibile.', 'success')
    else:
        flash('Camera non trovata.', 'danger')
    return redirect(url_for('gestione'))


# In questa sezione ho incluso API con tutti i tipi di richieste oltre alle route flask per rendere l'applicativo più versatile in termini
# di integrazione con altri servizi ed interoperbilità può sembrare rindondante ma ci sono varii vantaggi come
# sviluppare un'app mobile che utilizza la stessa logica di prenotazione di questa applicazione web
# senza ddover duplicare la logica di gestione delle prenotazioni
# l'utilizzo del formato JSON per comunicare tra il frontend e il backend ottimizza quindi
# il processo di scambio dati tra diverse tecnologie e piattaforme

@app.route('/api/prenotazione', methods=['POST'])
def crea_prenotazione_api():
    data = request.json
    nome = data.get('nome')
    cognome = data.get('cognome')
    checkin = data.get('checkin')
    checkout = data.get('checkout')
    data_nascita = data.get('data_nascita')
    numero_persone = data.get('numero_persone')
    email = data.get('email')
    camera_id = data.get('camera_id')

    if not nome or not cognome or not checkin or not checkout or not data_nascita or not numero_persone or not camera_id:
        return jsonify({'message': 'Tutti i campi devono essere compilati.'}), 400

    codice_prenotazione = genera_codice_prenotazione()

    nuova_prenotazione = Prenotazione(
        nome=nome,
        cognome=cognome,
        checkin=checkin,
        checkout=checkout,
        data_nascita=data_nascita,
        numero_persone=numero_persone,
        email=email,
        codice_prenotazione=codice_prenotazione,
        camera_id=camera_id
    )

    db.session.add(nuova_prenotazione)
    db.session.commit()

    return jsonify({'message': 'Prenotazione creata con successo', 'codice_prenotazione': codice_prenotazione}), 201


@app.route('/api/prenotazione/<codice_prenotazione>', methods=['GET'])
def leggi_prenotazione_api(codice_prenotazione):
    prenotazione = Prenotazione.query.filter_by(
        codice_prenotazione=codice_prenotazione).first()
    if prenotazione:
        return jsonify({
            'nome': prenotazione.nome,
            'cognome': prenotazione.cognome,
            'checkin': prenotazione.checkin,
            'checkout': prenotazione.checkout,
            'numero_persone': prenotazione.numero_persone,
            'email': prenotazione.email,
            'codice_prenotazione': prenotazione.codice_prenotazione,
            'camera_id': prenotazione.camera_id,
            'data_prenotazione': prenotazione.data_prenotazione.isoformat()
        }), 200
    else:
        return jsonify({'message': 'Prenotazione non trovata'}), 404


@app.route('/api/prenotazione/<codice_prenotazione>', methods=['PUT'])
def modifica_prenotazione_api(codice_prenotazione):
    prenotazione = Prenotazione.query.filter_by(
        codice_prenotazione=codice_prenotazione).first()
    if not prenotazione:
        return jsonify({'message': 'Prenotazione non trovata'}), 404

    data = request.json
    prenotazione.nome = data.get('nome', prenotazione.nome)
    prenotazione.cognome = data.get('cognome', prenotazione.cognome)
    prenotazione.checkin = data.get('checkin', prenotazione.checkin)
    prenotazione.checkout = data.get('checkout', prenotazione.checkout)
    prenotazione.numero_persone = data.get(
        'numero_persone', prenotazione.numero_persone)
    prenotazione.email = data.get('email', prenotazione.email)

    db.session.commit()
    return jsonify({'message': 'Prenotazione aggiornata con successo!'}), 200


@app.route('/api/prenotazione/<codice_prenotazione>', methods=['DELETE'])
def elimina_prenotazione_api(codice_prenotazione):
    prenotazione = Prenotazione.query.filter_by(
        codice_prenotazione=codice_prenotazione).first()

    if not prenotazione:
        return jsonify({'message': 'Prenotazione non trovata'}), 404

    db.session.delete(prenotazione)
    db.session.commit()
    return jsonify({'message': 'Prenotazione eliminata con successo.'}), 200


# parte del settaggio standanrd di flask con app.run con debug settato a true che mi fa vedere le modifiche effettuate
# senza dover chiudere/fare un re start del server
if __name__ == '__main__':
    with app.app_context():
        app.run(debug=True)
