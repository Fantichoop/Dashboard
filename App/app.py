from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from pyowm import OWM
from flask_migrate import Migrate
from datetime import datetime, timedelta


app = Flask(__name__)
# Настраиваем наш Flask
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Это наша база данных
db = SQLAlchemy(app)

# Это нужно для решения проблемы с разными видами базы данных.(добавить или удалить новую колону можно)
migrate = Migrate(app, db)


# Сама база данных
class WeatherData(db.Model):
    # .Column - создаём для каждой переменной свою колонку с данными
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    detailed_status = db.Column(db.String(50))
    wind = db.Column(db.String(50))
    humidity = db.Column(db.Integer)
    temperature = db.Column(db.Float)
    rain = db.Column(db.String(50))
    heat_index = db.Column(db.Float)
    clouds = db.Column(db.Integer)


# Добавляем глобальную переменную для хранения времени последнего успешного обновления
last_update_time = datetime.utcnow()


# Это функция запроса данных о погоде в Томске при помощи OWM, который напрямую связан с сайтом Weather API
def get_weather():
    # Делаем так, чтобы переменная последнего обновления была доступная всегда и везде
    global last_update_time

    owm = OWM('8309c7b50d12a283c0df3ed52803ac85')
    mgr = owm.weather_manager()

    observation = mgr.weather_at_place('Tomsk,RU')
    w = observation.weather

    detailed = w.detailed_status
    win = w.wind()
    h = w.humidity
    t = w.temperature('celsius')
    r = w.rain
    heat = w.heat_index
    cl = w.clouds

    timestamp = datetime.utcnow() + timedelta(hours=7)

    # Обновляем данные только после прошествия минуты с момента последнего успешного обновления
    if timestamp >= last_update_time + timedelta(minutes=1):
        save_to_db(detailed, round(win['speed']), h, round(t['temp']), r, heat, cl, timestamp, )
        last_update_time = timestamp

    return detailed, round(win['speed']), h, round(t['temp']), r, heat, cl, timestamp


# Функция сохранения полученных данных в базу данных
def save_to_db(detailed, wind, humidity, temperature, rain, heat_index, clouds, timestamp):
    weather_data = WeatherData(
        detailed_status=detailed,
        wind=str(wind),
        humidity=humidity,
        temperature=temperature,
        rain=str(rain),
        heat_index=heat_index,
        clouds=clouds,
        timestamp=timestamp
    )
    db.session.add(weather_data)
    db.session.commit()


# Функция создания сайта
@app.route('/')
def main_page():
    weather_data = get_weather()
    # render_template - генерирует HTML документ
    return render_template('main_page.html', weather_data=weather_data)


if __name__ == '__main__':
    migrate.init_app(app)
    # debug=True - показывает на ошибки прям на веб-странице
    app.run(debug=True)
