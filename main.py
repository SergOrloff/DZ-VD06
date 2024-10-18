from flask import Flask, render_template, request, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker

# Создаем Flask приложение
app = Flask(__name__)

# Настройки приложения
app.config['SECRET_KEY'] = 'your_secret_key'  # Ключ для сессий и флеш-сообщений
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # База данных SQLite

# Инициализация базы данных
db = SQLAlchemy(app)

# Замените ниже строку подключения на вашу
engine = create_engine('sqlite:///instance/users.db')
# engine = create_engine('postgresql+psycopg2://username:password@localhost/mydatabase')

# Создаем сессию
Session = sessionmaker(bind=engine)
session = Session()

# Отражаем таблицу User
metadata = MetaData()
user_table = Table('User', metadata, autoload_with=engine)

# Выполняем запрос для получения всех записей из таблицы User
with engine.connect() as connection:
    result = connection.execute(user_table.select())
    users = result.fetchall()

# Выводим данные
for user in users:
    print(user)

# Определение модели пользователя
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Идентификатор (первичный ключ)
    name = db.Column(db.String(50), nullable=False)  # Имя пользователя (обязательно для заполнения)
    city = db.Column(db.String(50), nullable=True)  # Город пользователя
    hobby = db.Column(db.String(50), nullable=True)  # Хобби пользователя
    age = db.Column(db.Integer, nullable=False)  # Возраст пользователя (обязательно для заполнения)
    email = db.Column(db.String(50), nullable=True)  # Email пользователя

    # Метод для удобного отображения объектов User
    def __repr__(self):
        return f'<User {self.name}>'

# Главная страница с формой
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Получаем данные из формы
        name = request.form.get('name')
        city = request.form.get('city')
        hobby = request.form.get('hobby')
        age = request.form.get('age')
        email = request.form.get('email')
        # Проверка на дубли
        duplicate_user = User.query.filter(
            (User.name == name) & (User.email == email)
        ).first()
        # Проверка данных: имя не пустое, возраст — это число
        if not name or not age.isdigit():
            flash('Имя и возраст обязательны. Возраст должен быть числом.', 'danger')  # Показать ошибку
        elif duplicate_user:
            flash('Пользователь с таким именем и email уже существует! Исправьте данные!', 'danger')
        else:
            # Сохраняем пользователя в базу данных
            user = User(name=name, city=city, hobby=hobby, age=int(age), email=email)
            db.session.add(user)  # Добавляем нового пользователя
            db.session.commit()  # Сохраняем изменения
            flash('Данные успешно сохранены!', 'success')  # Показать сообщение об успехе
            return redirect(url_for('index'))  # Перенаправляем на главную страницу для обновления формы

    # Извлекаем всех пользователей из базы данных для отображения на странице
    users = User.query.all()
    return render_template('index.html', users=users)

@app.route('/check_duplicates', methods=['POST'])
def check_duplicates():
    duplicates = db.session.query(User.name, User.email).group_by(User.name, User.email).having(db.func.count() > 1).all()
    if duplicates:
        for name, email in duplicates:
            users = User.query.filter_by(name=name, email=email).all()
            if len(users) > 1:
                for user in users[1:]:
                    # Добавьте логику подтверждения перед удалением
                    db.session.delete(user)
                db.session.commit()
                flash(f"Удалены дубли для {name} с email {email}", 'success')
    else:
        flash('Дубли не найдены', 'info')

    return redirect(url_for('index'))

# Основной блок для запуска приложения
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Создаем таблицы в базе данных, если они еще не существуют
    app.run(debug=True)  # Запускаем приложение с режимом отладки
