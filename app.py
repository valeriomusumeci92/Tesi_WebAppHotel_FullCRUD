from flask import Flask, request, jsonify, redirect, url_for, session, render_template, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import bcrypt
import random
import secrets
from flask_migrate import Migrate
from flask_mail import Mail, Message
import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)


def invia_email(email_destinatario):
    msg = MIMEText("La tua prenotazione è stata effettuata con successo! Ecco il tuo codice prenotazione")
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


class Prenotazione(db.Model):
    __tablename__ = 'prenotazioni'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cognome = db.Column(db.String(100), nullable=False)
    checkin = db.Column(db.DateTime, nullable=False)  # Modificato in DateTime
    checkout = db.Column(db.DateTime, nullable=False)  # Modificato in DateTime
    data_nascita = db.Column(db.DateTime, nullable=False)  # Modificato in DateTime se necessario
    numero_persone = db.Column(db.Integer, nullable=False)
    codice_prenotazione = db.Column(db.String(10), unique=True, nullable=False)
    camera_id = db.Column(db.Integer, db.ForeignKey('camera.id'), nullable=False)
    email = db.Column(db.String(150))
    prezzo_totale = db.Column(db.Integer, nullable=False)  # Include il prezzo totale
    data_prenotazione = db.Column(db.DateTime, default=datetime.utcnow)

    camera = db.relationship('Camera', back_populates='prenotazioni')

class Camera(db.Model):
    __tablename__ = 'camera'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    immagine = db.Column(db.String(200), nullable=False)
    descrizione = db.Column(db.Text, nullable=True)
    prezzo = db.Column(db.Integer, nullable=False)  # Prezzo per notte della camera
    disponibile = db.Column(db.Boolean, default=True)
    max_persone = db.Column(db.Integer, nullable=False)

    prenotazioni = db.relationship('Prenotazione', back_populates='camera')


class ModificaPrenotazioneLog(db.Model):
    __tablename__ = 'modifica_prenotazione_log'

    id = db.Column(db.Integer, primary_key=True)
    codice_prenotazione = db.Column(db.String(10), db.ForeignKey(
        'prenotazioni.codice_prenotazione'), nullable=False)  # Fix here
    nome_originario = db.Column(db.String(100), nullable=True)
    cognome_originario = db.Column(db.String(100), nullable=False)
    checkin_originario = db.Column(db.String(10), nullable=False)
    checkout_originario = db.Column(db.String(10), nullable=False)
    numero_persone_originario = db.Column(db.Integer, nullable=False)
    email_originaria = db.Column(db.String(150), nullable=True)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f'<ModificaPrenotazioneLog {self.codice_prenotazione} - {self.timestamp}>'


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)  # Required for Flask-Login


@app.cli.command('create-admin')
def create_admin():
    """Crea un admin."""
    username = input("Inserisci il nome utente per l'admin: ")
    password = input("Inserisci la password per l'admin: ")

    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    new_user = User(username=username, password=hashed_pw, is_admin=True)

    db.session.add(new_user)
    db.session.commit()
    print(f"Admin {username} creato!")


# Rotte
@app.route('/')
def home():
    return render_template('homepage.html')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


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


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/prenota')
def prenota():
    camere_disponibili = Camera.query.filter_by(disponibile=True).all()
    return render_template('prenota_generale.html', camere=camere_disponibili)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/admin')
@login_required
def admin_page():
    return render_template('admin.html')


@app.route('/prenota/<int:camera_id>', methods=['GET', 'POST'])
def prenota_camera(camera_id):
    camera = Camera.query.get(camera_id)
    if not camera:
        return "Camera non trovata", 404
    return render_template('camera_specifica.html', camera=camera, camera_id=camera.id)


@app.route('/verifica_prenotazione', methods=['GET', 'POST'])
def check_prenotazione():
    if request.method == 'POST':
        codice_prenotazione = request.form.get('codice_prenotazione')
        prenotazione = Prenotazione.query.filter_by(
            codice_prenotazione=codice_prenotazione).first()
        if prenotazione:
            # Reindirizza alla pagina di conferma della prenotazione
            return redirect(url_for('pagina_conferma', codice_prenotazione=prenotazione.codice_prenotazione))
        else:
            flash('Prenotazione non trovata. Verifica il codice e riprova.', 'danger')
            return redirect(url_for('check_prenotazione'))
    return render_template('verifica_prenotazione.html')


def genera_codice_prenotazione():
    return f'{random.randint(10000, 99999)}'


@app.route('/invia_prenotazione/<int:camera_id>', methods=['POST'])
def invia_prenotazione(camera_id):
    nome = request.form.get('nome')
    cognome = request.form.get('cognome')
    checkin = request.form.get('checkin')
    checkout = request.form.get('checkout')
    data_nascita = request.form.get('data_nascita')  # Se desideri convertirlo in datetime, fallo qui
    numero_persone = request.form.get('numero_persone')
    email = request.form.get('email')

    camera = Camera.query.get(camera_id)  # Ottieni i dettagli della camera
    if not camera:
        return "Camera non trovata", 404

    # Calcola il prezzo totale
    checkin_date = datetime.strptime(checkin, '%Y-%m-%d')
    checkout_date = datetime.strptime(checkout, '%Y-%m-%d')
    numero_notti = (checkout_date - checkin_date).days

    if numero_notti <= 0:
        flash('La data di check-out deve essere successiva alla data di check-in.', 'danger')
        return redirect(url_for('prenota_camera', camera_id=camera_id))

    prezzo_totale = numero_notti * camera.prezzo

    codice_prenotazione = genera_codice_prenotazione()

    nuova_prenotazione = Prenotazione(
        nome=nome,
        cognome=cognome,
        checkin=checkin_date,  # Usare oggetto datetime
        checkout=checkout_date,  # Usare oggetto datetime
        data_nascita=datetime.strptime(data_nascita, '%Y-%m-%d'),  # Convertito in oggetto datetime
        numero_persone=numero_persone,
        codice_prenotazione=codice_prenotazione,
        email=email,
        camera_id=camera_id,
        prezzo_totale=prezzo_totale  # Include il prezzo totale
    )

    db.session.add(nuova_prenotazione)
    db.session.commit()

    flash('Prenotazione completata con successo!', 'success')
    return redirect(url_for('pagina_conferma', codice_prenotazione=codice_prenotazione))


@app.route('/api/disponibilita_camera/<int:camera_id>', methods=['GET'])
def check_disponibilita_camera(camera_id):
    checkin = request.args.get('checkin')
    checkout = request.args.get('checkout')

    # Esegui una query per trovare tutte le prenotazioni di questa camera
    prenotazioni = Prenotazione.query.filter(
        Prenotazione.camera_id == camera_id,
        or_(
            and_(Prenotazione.checkin < checkout, Prenotazione.checkout > checkin)
        )
    ).all()

    # Se ci sono prenotazioni che sovrappongono le date, ritorna queste date come non disponibili
    unavailable_dates = []
    if prenotazioni:
        unavailable_dates.append({
            "checkin": prenotazione.checkin,
            "checkout": prenotazione.checkout
        } for prenotazione in prenotazioni)

    return jsonify(unavailable_dates)

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
    # Recupera la prenotazione dal database usando il codice
    prenotazione = Prenotazione.query.filter_by(codice_prenotazione=codice_prenotazione).first()

    # Controlla se la prenotazione esiste
    if not prenotazione:
        return "Prenotazione non trovata", 404

    # Recupera la camera associata alla prenotazione
    camera = Camera.query.filter_by(id=prenotazione.camera_id).first()  # Assicurati che prenotazione.camera_id esista
    if not camera:
        return "Camera non trovata", 404

    if request.method == 'POST':
        # Verifica il token di modifica per sicurezza
        token = session.get('modifica_token')
        if token != request.form.get('token'):
            flash('Token non valido o scaduto.', 'danger')
            return redirect(url_for('home'))

        # Log delle modifiche
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

        # Recupera i dati dal form
        checkin = request.form.get('checkin')  # Resta una stringa 'YYYY-MM-DD'
        checkout = request.form.get('checkout')  # Resta una stringa 'YYYY-MM-DD'
        data_nascita = request.form.get('data_nascita')  # Resta una stringa 'YYYY-MM-DD'
        numero_persone = int(request.form.get('numero_persone'))

        # Calcola e controlla le nuove date
        checkin_date = datetime.strptime(checkin, '%Y-%m-%d')  # Converti in datetime
        checkout_date = datetime.strptime(checkout, '%Y-%m-%d')  # Converti in datetime
        numero_notti = (checkout_date - checkin_date).days

        if numero_notti <= 0:
            flash('La data di check-out deve essere successiva alla data di check-in.', 'danger')
            return redirect(url_for('modifica_prenotazione', codice_prenotazione=codice_prenotazione))

        # Controllo della data di nascita
        data_nascita_date = datetime.strptime(data_nascita, '%Y-%m-%d').date()  # Converti in date
        eta = (datetime.now().date() - data_nascita_date).days // 365  # Calcolo dell'età
        if eta < 18:
            flash('Devi avere almeno 18 anni per effettuare una prenotazione.', 'danger')
            return redirect(url_for('modifica_prenotazione', codice_prenotazione=codice_prenotazione))

        # Controllo sul numero di persone basato sull'ID della camera
        if camera.id in [1, 4]:  # Tripla Deluxe or Tripla Economica
            if numero_persone < 1 or numero_persone > 3:
                flash('Nella camera può esserci da 1 a 3 persone.', 'danger')
                return redirect(url_for('modifica_prenotazione', codice_prenotazione=codice_prenotazione))
        elif camera.id in [2, 5]:  # Doppia Deluxe or Doppia Economica
            if numero_persone < 1 or numero_persone > 2:
                flash('Nella camera può esserci da 1 a 2 persone.', 'danger')
                return redirect(url_for('modifica_prenotazione', codice_prenotazione=codice_prenotazione))
        elif camera.id in [3, 6]:  # Singola Deluxe or Singola Economica
            if numero_persone != 1:
                flash('Nella camera può esserci solo 1 persona.', 'danger')
                return redirect(url_for('modifica_prenotazione', codice_prenotazione=codice_prenotazione))

        # Aggiorna i campi della prenotazione
        prenotazione.nome = request.form.get('nome', prenotazione.nome)
        prenotazione.cognome = request.form.get('cognome', prenotazione.cognome)
        prenotazione.checkin = checkin_date  # Assicurati di assegnare l'oggetto datetime
        prenotazione.checkout = checkout_date  # Assicurati di assegnare l'oggetto datetime
        prenotazione.data_nascita = data_nascita_date  # Assicurati di assegnare l'oggetto date
        prenotazione.numero_persone = numero_persone
        prenotazione.email = request.form.get('email', prenotazione.email)

        # Ricalcola il prezzo totale
        prenotazione.prezzo_totale = numero_notti * camera.prezzo

        # Salva le modifiche nel database
        db.session.commit()
        flash('Prenotazione aggiornata con successo!', 'success')
        return redirect(url_for('pagina_conferma', codice_prenotazione=prenotazione.codice_prenotazione))

    # Genera un nuovo token di sessione per la modifica
    session['modifica_token'] = secrets.token_urlsafe(16)

    # Ritorna il template con i dati della prenotazione e della camera
    return render_template(
        'modifica_prenotazione.html',
        prenotazione=prenotazione,
        token=session['modifica_token'],
        camera=camera
    )



@app.route('/conferma_eliminazione')
def conferma_eliminazione():
    return render_template('conferma_eliminazione.html')


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
            # Nuovo campo restituito solo per l'admin
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

# rotte per admin


@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    user = User.query.filter_by(username=username).first()

    if user and bcrypt.checkpw(password.encode('utf-8'), user.password):
        login_user(user)
        return jsonify(success=True), 200
    else:
        return jsonify(success=False, message='Credenziali errate'), 401


@app.route('/admin/gestione')
@login_required
def gestione():
    prenotazioni = Prenotazione.query.all()
    camere = Camera.query.all()
    return render_template('gestione.html', prenotazioni=prenotazioni, camere=camere)


@app.route('/admin/camera/<int:camera_id>/non_disponibile', methods=['POST'])
@login_required
def elimina_disponibilita(camera_id):
    camera = Camera.query.get(camera_id)
    if camera:
        camera.disponibile = False  # Imposta la camera come non disponibile
        db.session.commit()  # Salva le modifiche nel database
        flash('La camera è stata rimossa dalla disponibilità.', 'success')
    else:
        flash('Camera non trovata.', 'danger')
    return redirect(url_for('gestione'))


@app.route('/admin/camera/<int:camera_id>/disponibile', methods=['POST'])
@login_required
def rendi_disponibile(camera_id):
    camera = Camera.query.get(camera_id)
    if camera:
        camera.disponibile = True  # Imposta la camera come disponibile
        db.session.commit()  # Salva le modifiche nel database
        flash('La camera è stata resa disponibile.', 'success')
    else:
        flash('Camera non trovata.', 'danger')
    return redirect(url_for('gestione'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
