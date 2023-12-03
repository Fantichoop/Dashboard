from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from pyowm import OWM

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class WeatherData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    detailed_status = db.Column(db.String(50))
    wind = db.Column(db.String(50))
    humidity = db.Column(db.Integer)
    temperature = db.Column(db.Float)
    rain = db.Column(db.String(50))
    heat_index = db.Column(db.Float)
    clouds = db.Column(db.Integer)

def get_weather():
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

    save_to_db(detailed, win, h, round(t['temp']), r, heat, cl)

    return detailed, win, h, round(t['temp']), r, heat, cl

def save_to_db(detailed, wind, humidity, temperature, rain, heat_index, clouds):
    weather_data = WeatherData(
        detailed_status=detailed,
        wind=str(wind),
        humidity=humidity,
        temperature=temperature,
        rain=str(rain),
        heat_index=heat_index,
        clouds=clouds
    )
    db.session.add(weather_data)
    db.session.commit()

@app.route('/')
def index():
    weather_data = get_weather()
    return render_template('index.html', weather=weather_data)

if __name__ == '__main__':
    app.run(debug=True)