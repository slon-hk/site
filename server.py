from flask import Flask, request, jsonify, render_template, redirect, url_for, session, send_from_directory
from flask_cors import CORS
import os
import uuid
from database import db, bcrypt, User, Image, init_app

# Настройки Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
CORS(app, resources={r"/*": {"origins": "*"}})

# Инициализация базы данных
init_app(app)

# Проверка допустимых файлов
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Главная страница (защищена авторизацией)
@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

# Маршрут для загрузки изображений
@app.route('/gallery', methods=['GET'])
def get_gallery():
    images = Image.query.all()
    image_urls = []
    for image in images:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
        if os.path.exists(file_path):
            image_urls.append(url_for('serve_uploaded_file', filename=image.filename))
        else:
            db.session.delete(image)
    db.session.commit()

    return jsonify(image_urls), 200

# Маршрут для отдачи файлов
@app.route('/uploads/<filename>')
def serve_uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Страница логина
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('home'))
        return render_template('login.html', error='Неправильный логин или пароль')
    return render_template('login.html')

# Страница регистрации
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        if User.query.filter_by(username=username).first():
            return render_template('register.html', error='Пользователь уже существует')

        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        session['user_id'] = new_user.id
        return redirect(url_for('home'))
    return render_template('register.html')

# Маршрут для загрузки изображения
@app.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        try:
            extension = file.filename.rsplit('.', 1)[1].lower()
            unique_filename = f"{uuid.uuid4().hex}.{extension}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)

            image_url = f"/uploads/{unique_filename}"
            new_image = Image(filename=unique_filename, url=image_url)
            db.session.add(new_image)
            db.session.commit()

            return jsonify({'message': 'File uploaded successfully', 'url': image_url}), 200
        except Exception as e:
            print("Error saving file:", e)
            return jsonify({'error': 'Internal Server Error'}), 500

    return jsonify({'error': 'Invalid file type'}), 400

# Маршрут для выхода
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

# Запуск приложения
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=2000, debug=True)