from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_sqlalchemy import SQLAlchemy
import os
import uuid
from flask_cors import CORS

# Настройки Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
CORS(app, resources={r"/*": {"origins": "*"}})
# Инициализация базы данных
db = SQLAlchemy(app)

# Модель базы данных для хранения изображений
class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(200), nullable=False)

# Создание базы данных
with app.app_context():
    db.create_all()

# Проверка допустимых файлов
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Главная страница
@app.route('/')
def home():
    return render_template('index.html')

# Маршрут для получения галереи
@app.route('/gallery', methods=['GET'])
def get_gallery():
    images = Image.query.all()
    image_urls = []
    for image in images:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
        if os.path.exists(file_path):
            image_urls.append(image.url)
        else:
            # Если файл отсутствует, удаляем запись из базы данных
            db.session.delete(image)
    db.session.commit()
    return jsonify(image_urls)

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

# Маршрут для отдачи загруженных файлов
@app.route('/uploads/<filename>')
def serve_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Запуск приложения
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=2000, debug=True)