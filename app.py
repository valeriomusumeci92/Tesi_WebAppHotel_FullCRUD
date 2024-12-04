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
    msg = MIMEText("La tua prenotazione è stata effettuata con successo!")
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


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))


class Prenotazione(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cognome = db.Column(db.String(100), nullable=False)
    checkin = db.Column(db.String(10), nullable=False)
    checkout = db.Column(db.String(10), nullable=False)
    data_nascita = db.Column(db.String(10), nullable=False)
    numero_persone = db.Column(db.Integer, nullable=False)
    codice_prenotazione = db.Column(db.String(10), unique=True, nullable=False)
    camera_id = db.Column(db.Integer, db.ForeignKey(
        'camera.id'), nullable=False)
    email = db.Column(db.String(150))
    # Nuovo campo per data e ora di prenotazione
    data_prenotazione = db.Column(db.DateTime, default=datetime.utcnow)


class Camera(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    immagine = db.Column(db.String(200), nullable=False)
    descrizione = db.Column(db.Text, nullable=True)


class ModificaPrenotazioneLog(db.Model):
    # Assicurati che questo sia il nome corretto della tabella
    __tablename__ = 'modifica_prenotazione_log'

    id = db.Column(db.Integer, primary_key=True)
    codice_prenotazione = db.Column(db.String(10), db.ForeignKey(
        'prenotazione.codice_prenotazione'), nullable=False)
    nome_modificato = db.Column(db.String(100), nullable=True)
    cognome_modificato = db.Column(db.String(100), nullable=False)
    # Aggiornato per match con tipo di dato
    checkin_modificato = db.Column(db.String(10), nullable=False)
    # Aggiornato per match con tipo di dato
    checkout_modificato = db.Column(db.String(10), nullable=False)
    # Aggiunto per registrare il numero di persone
    numero_persone_modificato = db.Column(db.Integer, nullable=False)
    # Aggiunto per registrare il nuovo email
    email_modificato = db.Column(db.String(150), nullable=True)
    # Tempo della modifica
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f'<ModificaPrenotazioneLog {self.codice_prenotazione} - {self.timestamp}>'


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
    camere = Camera.query.all()
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
    camera = Camera.query.get(camera_id)
    if not camera:
        return "Camera non trovata", 404
    return render_template('camera_specifica.html', camera=camera, camera_id=camera.id)


def genera_codice_prenotazione():
    return f'{random.randint(10000, 99999)}'


@app.route('/invia_prenotazione/<int:camera_id>', methods=['POST'])
def invia_prenotazione(camera_id):
    nome = request.form.get('nome')
    cognome = request.form.get('cognome')
    checkin = request.form.get('checkin')
    checkout = request.form.get('checkout')
    data_nascita = request.form.get('data_nascita')
    numero_persone = request.form.get('numero_persone')
    email = request.form.get('email')

    codice_prenotazione = genera_codice_prenotazione()

    nuova_prenotazione = Prenotazione(
        nome=nome,
        cognome=cognome,
        checkin=checkin,
        checkout=checkout,
        data_nascita=data_nascita,
        numero_persone=numero_persone,
        codice_prenotazione=codice_prenotazione,
        email=email,
        camera_id=camera_id
    )

    db.session.add(nuova_prenotazione)
    db.session.commit()

    invia_email(email)
    flash('Prenotazione completata con successo!', 'success')
    return redirect(url_for('pagina_conferma', codice_prenotazione=codice_prenotazione))


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
    prenotazione = Prenotazione.query.filter_by(
        codice_prenotazione=codice_prenotazione).first()
    if not prenotazione:
        return "Prenotazione non trovata", 404

    if request.method == 'POST':
        token = session.get('modifica_token')
        if token != request.form.get('token'):
            flash('Token non valido o scaduto.', 'danger')
            return redirect(url_for('home'))

        # Log delle modifiche
        modifica_log = ModificaPrenotazioneLog(
            codice_prenotazione=prenotazione.codice_prenotazione,
            nome_modificato=prenotazione.nome,
            cognome_modificato=prenotazione.cognome,
            checkin_modificato=prenotazione.checkin,  # Aggiunto per registrare il check-in
            # Aggiunto per registrare il check-out
            checkout_modificato=prenotazione.checkout,
            numero_persone_modificato=prenotazione.numero_persone,
            email_modificato=prenotazione.email
        )
        db.session.add(modifica_log)

        # Aggiornare tutti i campi pertinenti
        prenotazione.nome = request.form.get('nome', prenotazione.nome)
        prenotazione.cognome = request.form.get(
            'cognome', prenotazione.cognome)
        prenotazione.checkin = request.form.get(
            'checkin', prenotazione.checkin)
        prenotazione.checkout = request.form.get(
            'checkout', prenotazione.checkout)
        prenotazione.data_nascita = request.form.get(
            'data_nascita', prenotazione.data_nascita)
        prenotazione.numero_persone = request.form.get(
            'numero_persone', prenotazione.numero_persone)
        prenotazione.email = request.form.get('email', prenotazione.email)

        db.session.commit()
        flash('Prenotazione aggiornata con successo!', 'success')
        return redirect(url_for('pagina_conferma', codice_prenotazione=prenotazione.codice_prenotazione))

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


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
