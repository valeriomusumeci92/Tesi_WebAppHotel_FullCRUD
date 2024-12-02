from flask import Flask, request, jsonify, redirect, url_for, session, render_template, flash , abort  # Assicurati di includere flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import bcrypt, random, secrets
from flask_migrate import Migrate


app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)  # Associa Migrate all'app e al db
login_manager = LoginManager()
login_manager.init_app(app)


# Modelli
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))



class Prenotazione(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    data = db.Column(db.String(10), nullable=False)
    ora = db.Column(db.String(5), nullable=False)
    numero_persone = db.Column(db.Integer, nullable=False)
    codice_prenotazione = db.Column(db.String(10), unique=True, nullable=False)
    camera_id = db.Column(db.Integer, db.ForeignKey('camera.id'), nullable=False)  # Nuovo campo




class Camera(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    immagine = db.Column(db.String(200), nullable=False)  # Path per l'immagine
    descrizione = db.Column(db.Text, nullable=True)  # Cambiato a nullable=True


class ModificaPrenotazioneLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codice_prenotazione = db.Column(db.String(10), db.ForeignKey('prenotazione.codice_prenotazione'), nullable=False)
    nome_modificato = db.Column(db.String(100), nullable=True)
    data_modificata = db.Column(db.String(10), nullable=True)
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
    return f'#{random.randint(10000, 99999)}'  # Genera un codice casuale


@app.route('/invia_prenotazione/<int:camera_id>', methods=['POST'])
def invia_prenotazione(camera_id):  # Mantieni camera_id come parametro
    nome = request.form.get('nome')
    data = request.form.get('data')
    ora = request.form.get('ora')
    numero_persone = request.form.get('numero_persone')

    # Genera il codice di prenotazione
    codice_prenotazione = genera_codice_prenotazione()

    # Crea una nuova prenotazione
    nuova_prenotazione = Prenotazione(
        nome=nome,
        data=data,
        ora=ora,
        numero_persone=numero_persone,
        codice_prenotazione=codice_prenotazione,
        camera_id=camera_id  # Assicurati di assegnare camera_id qui
    )

    db.session.add(nuova_prenotazione)
    db.session.commit()

    flash('Prenotazione completata con successo!', 'success')
    # Reindirizza alla pagina di conferma prenotazione
    return redirect(url_for('pagina_conferma', codice_prenotazione=codice_prenotazione))





@app.route('/conferma_prenotazione/<codice_prenotazione>')
def pagina_conferma(codice_prenotazione):
    # Recupera la prenotazione usando il codice
    prenotazione = Prenotazione.query.filter_by(codice_prenotazione=codice_prenotazione).first()
    if not prenotazione:
        return "Prenotazione non trovata", 404

    # Recupera la camera associata alla prenotazione
    camera = Camera.query.get(prenotazione.camera_id)

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
    # Controlla il token di sicurezza
    token = request.json.get('token')  # Usa request.json per ottenere il token dal body
    if token != session.get('elimina_token'):
        return jsonify({'message': 'Token non valido'}), 403  # Restituisci un errore 403

    # Prova a trovare la prenotazione
    prenotazione = Prenotazione.query.filter_by(codice_prenotazione=codice_prenotazione).first()

    if prenotazione:  # Se la prenotazione è stata trovata
        db.session.delete(prenotazione)  # Elimina la prenotazione
        db.session.commit()  # Applica le modifiche
        return redirect(url_for('conferma_eliminazione.html'))  # Reindirizza alla pagina di conferma eliminazione
    else:
        return jsonify({'message': 'Prenotazione non trovata'}), 404  # Restituisci un errore 404




if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
