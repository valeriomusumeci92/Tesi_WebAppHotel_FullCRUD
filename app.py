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
# Inizializza l'app Flask
app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)  # Associa Migrate all'app e al db
login_manager = LoginManager()
login_manager.init_app(app)

def invia_email(email_destinatario):
    msg = MIMEText("La tua prenotazione è stata effettuata con successo!")
    msg['Subject'] = 'Conferma Prenotazione'
    msg['From'] = 'tesimusumeci@gmail.com'  # Inserisci qui la tua email Gmail
    msg['To'] = email_destinatario

    try:
        # Configurazione del server
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()  # Attiva TLS
            server.login('tesimusumeci@gmail.com', 'ignjiuwgurgptfvb')  # Login con password
            server.send_message(msg)  # Invia l'email

        print(f"Email inviata a {email_destinatario}!")
    except Exception as e:
        print(f"Si è verificato un errore nell'invio dell'email: {e}")


# Modelli
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))

class Prenotazione(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cognome = db.Column(db.String(100), nullable=False)  # Nuovo campo Cognome
    checkin = db.Column(db.String(10), nullable=False)  # Nuovo campo Check-in
    checkout = db.Column(db.String(10), nullable=False)  # Nuovo campo Check-out
    data_nascita = db.Column(db.String(10), nullable=False)  # Campo per la data di nascita
    numero_persone = db.Column(db.Integer, nullable=False)
    codice_prenotazione = db.Column(db.String(10), unique=True, nullable=False)
    camera_id = db.Column(db.Integer, db.ForeignKey('camera.id'), nullable=False)
    email = db.Column(db.String(150))  # Campo Email


class Camera(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    immagine = db.Column(db.String(200), nullable=False)  # Path per l'immagine
    descrizione = db.Column(db.Text, nullable=True)  # Cambiato a nullable=True

class ModificaPrenotazioneLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codice_prenotazione = db.Column(db.String(10), db.ForeignKey('prenotazione.codice_prenotazione'), nullable=False)
    nome_modificato = db.Column(db.String(100), nullable=True)
    cognome_modificato = db.Column(db.String(100), nullable=False)  # Nuovo campo Cognome
    ora_modificata = db.Column(db.String(5), nullable=True)
    numero_persone_modificato = db.Column(db.Integer, nullable=True)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

# Rotte
@app.route('/')
def home():
    return render_template('homepage.html')  # Cambiato a homepage.html

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
    return render_template('admin.html')  # Cambiato a admin.html

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/prenota')
def prenota():
    camere = Camera.query.all()  # Recupera tutte le camere dal database
    return render_template('prenota_generale.html', camere=camere)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/admin')
@login_required
def admin_page():
    return render_template('admin.html')

@app.route('/prenota/<int:camera_id>', methods=['GET', 'POST'])
def prenota_camera(camera_id):
    # Recupera la camera specifica dal database usando l'id
    camera = Camera.query.get(camera_id)
    if not camera:
        return "Camera non trovata", 404
    return render_template('camera_specifica.html', camera=camera, camera_id=camera.id)

def genera_codice_prenotazione():
    return f'{random.randint(10000, 99999)}'  # Genera un codice casuale
@app.route('/invia_prenotazione/<int:camera_id>', methods=['POST'])
def invia_prenotazione(camera_id):
    nome = request.form.get('nome')
    cognome = request.form.get('cognome')  # Recupera il cognome
    checkin = request.form.get('checkin')  # Recupera la data di check-in
    checkout = request.form.get('checkout')  # Recupera la data di check-out
    data_nascita = request.form.get('data_nascita')  # Recupera la data di nascita
    numero_persone = request.form.get('numero_persone')
    email = request.form.get('email')  # Recupera l'email dal modulo

    # Genera il codice di prenotazione
    codice_prenotazione = genera_codice_prenotazione()

    # Crea una nuova prenotazione
    nuova_prenotazione = Prenotazione(
        nome=nome,
        cognome=cognome,  # Salva il cognome
        checkin=checkin,  # Salva la data di check-in
        checkout=checkout,  # Salva la data di check-out
        data_nascita=data_nascita,  # Salva la data di nascita
        numero_persone=numero_persone,
        codice_prenotazione=codice_prenotazione,
        email=email,  # Salva l'email
        camera_id=camera_id
    )

    db.session.add(nuova_prenotazione)
    db.session.commit()

    # Invia l'email di conferma (se implementata precedentemente)
    invia_email(email)
    flash('Prenotazione completata con successo!', 'success')
    return redirect(url_for('pagina_conferma', codice_prenotazione=codice_prenotazione))


@app.route('/conferma_prenotazione/<codice_prenotazione>')
def pagina_conferma(codice_prenotazione):
    # Recupera la prenotazione usando il codice
    prenotazione = Prenotazione.query.filter_by(codice_prenotazione=codice_prenotazione).first()
    if not prenotazione:
        return "Prenotazione non trovata", 404

    # Recupera la camera associata alla prenotazione
    camera = Camera.query.get(prenotazione.camera_id)
    session['elimina_token'] = secrets.token_urlsafe(16)  # Genera e salva il token
    return render_template('conferma_prenotazione.html', prenotazione=prenotazione, camera=camera)

@app.route('/modifica_prenotazione/<codice_prenotazione>', methods=['GET', 'POST'])
def modifica_prenotazione(codice_prenotazione):
    # Recupera la prenotazione dal database
    prenotazione = Prenotazione.query.filter_by(codice_prenotazione=codice_prenotazione).first()
    if not prenotazione:
        return "Prenotazione non trovata", 404

    if request.method == 'POST':
        # Verifica il token nella sessione
        token = session.get('modifica_token')
        if token != request.form.get('token'):
            flash('Token non valido o scaduto.', 'danger')
            return redirect(url_for('home'))

        # Log delle modifiche prima di modificare la prenotazione
        modifica_log = ModificaPrenotazioneLog(
            codice_prenotazione=prenotazione.codice_prenotazione,
            nome_modificato=prenotazione.nome,
            data_modificata=prenotazione.data,
            ora_modificata=prenotazione.ora,
            numero_persone_modificato=prenotazione.numero_persone,
        )
        db.session.add(modifica_log)  # Aggiungi il log alla sessione

        # Effettua le modifiche alla prenotazione
        prenotazione.nome = request.form.get('nome')
        prenotazione.data = request.form.get('data')
        prenotazione.ora = request.form.get('ora')
        prenotazione.numero_persone = request.form.get('numero_persone')

        db.session.commit()  # Salva tutte le modifiche nel database
        flash('Prenotazione aggiornata con successo!', 'success')
        return redirect(url_for('pagina_conferma', codice_prenotazione=prenotazione.codice_prenotazione))

    # Se il metodo è GET, genera un nuovo token e rispondi con il modulo di modifica
    session['modifica_token'] = secrets.token_urlsafe(16)
    return render_template('modifica_prenotazione.html', prenotazione=prenotazione, token=session['modifica_token'])

@app.route('/conferma_eliminazione')
def conferma_eliminazione():
    return render_template('conferma_eliminazione.html')

@app.route('/elimina_prenotazione/<codice_prenotazione>', methods=['DELETE'])
def elimina_prenotazione(codice_prenotazione):
    token = request.json.get('token')
    if token != session.get('elimina_token'):
        return jsonify({'message': 'Token non valido'}), 403

    prenotazione = Prenotazione.query.filter_by(codice_prenotazione=codice_prenotazione).first()

    if prenotazione:
        db.session.delete(prenotazione)
        db.session.commit()
        return jsonify({'message': 'Prenotazione eliminata con successo.'}), 200
    else:
        return jsonify({'message': 'Prenotazione non trovata'}), 404

# Nuove API per le prenotazioni
@app.route('/api/prenotazione', methods=['POST'])
def crea_prenotazione_api():
    data = request.json
    nome = data.get('nome')
    data_prenotazione = data.get('data')
    ora = data.get('ora')
    numero_persone = data.get('numero_persone')
    camera_id = data.get('camera_id')

    # Validazione dei dati
    if not nome or not data_prenotazione or not ora or not numero_persone or not camera_id:
        return jsonify({'message': 'Tutti i campi devono essere compilati.'}), 400

    codice_prenotazione = genera_codice_prenotazione()

    nuova_prenotazione = Prenotazione(
        nome=nome,
        data=data_prenotazione,
        ora=ora,
        numero_persone=numero_persone,
        codice_prenotazione=codice_prenotazione,
        camera_id=camera_id
    )

    db.session.add(nuova_prenotazione)
    db.session.commit()

    return jsonify({'message': 'Prenotazione creata con successo', 'codice_prenotazione': codice_prenotazione}), 201

@app.route('/api/prenotazione/<codice_prenotazione>', methods=['GET'])
def leggi_prenotazione_api(codice_prenotazione):
    prenotazione = Prenotazione.query.filter_by(codice_prenotazione=codice_prenotazione).first()
    if prenotazione:
        return jsonify({
            'nome': prenotazione.nome,
            'data': prenotazione.data,
            'ora': prenotazione.ora,
            'numero_persone': prenotazione.numero_persone,
            'codice_prenotazione': prenotazione.codice_prenotazione,
            'camera_id': prenotazione.camera_id
        }), 200
    else:
        return jsonify({'message': 'Prenotazione non trovata'}), 404

@app.route('/api/prenotazione/<codice_prenotazione>', methods=['PUT'])
def modifica_prenotazione_api(codice_prenotazione):
    prenotazione = Prenotazione.query.filter_by(codice_prenotazione=codice_prenotazione).first()
    if not prenotazione:
        return jsonify({'message': 'Prenotazione non trovata'}), 404

    data = request.json
    prenotazione.nome = data.get('nome', prenotazione.nome)
    prenotazione.data = data.get('data', prenotazione.data)
    prenotazione.ora = data.get('ora', prenotazione.ora)
    prenotazione.numero_persone = data.get('numero_persone', prenotazione.numero_persone)

    db.session.commit()
    return jsonify({'message': 'Prenotazione aggiornata con successo!'}), 200

@app.route('/api/prenotazione/<codice_prenotazione>', methods=['DELETE'])
def elimina_prenotazione_api(codice_prenotazione):
    prenotazione = Prenotazione.query.filter_by(codice_prenotazione=codice_prenotazione).first()

    if not prenotazione:
        return jsonify({'message': 'Prenotazione non trovata'}), 404

    db.session.delete(prenotazione)
    db.session.commit()
    return jsonify({'message': 'Prenotazione eliminata con successo.'}), 200

#rotte per admin


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
