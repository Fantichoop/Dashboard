from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_migrate import Migrate
from datetime import datetime, timedelta
from pyowm import OWM
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import pandas as pd
import sqlite3



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather_data.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)


class WeatherData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    detailed_status = db.Column(db.String(255))
    wind_speed = db.Column(db.Integer)
    humidity = db.Column(db.Integer)
    temperature = db.Column(db.Integer)
    clouds = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime)

    def __init__(self, detailed_status, wind_speed, humidity, temperature, clouds, timestamp):
        self.detailed_status = detailed_status
        self.wind_speed = wind_speed
        self.humidity = humidity
        self.temperature = temperature
        self.clouds = clouds
        self.timestamp = timestamp


last_update_time = datetime.utcnow()


def get_weather():
    global last_update_time
    owm = OWM('8309c7b50d12a283c0df3ed52803ac85')
    mgr = owm.weather_manager()
    observation = mgr.weather_at_place('Tomsk,RU')
    w = observation.weather
    detailed = w.detailed_status
    win = w.wind()
    h = w.humidity
    t = w.temperature('celsius')
    cl = w.clouds
    timestamp = datetime.utcnow() + timedelta(hours=7)
    return detailed, round(win['speed']), h, round(t['temp']), cl, timestamp


# Функция для подключения к базе данных
def connect_db():
    return sqlite3.connect('instance/weather_data.db')


@app.route('/')
def main_page():
    # Тут основные данные
    weather_data = get_weather()
    new_weather_entry = WeatherData(*weather_data)
    db.session.add(new_weather_entry)
    db.session.commit()

    return render_template('main_page.html', weather_data=weather_data)


@app.route('/search_page', methods=['POST', 'GET'])
def search_results():
    selected_date = request.form['selected_date']
    weather_data = get_weather()
    

    # Подключение к базе данных
    conn = connect_db()
    cursor = conn.cursor()

    # Преобразование строки даты в объект datetime
    selected_datetime = datetime.strptime(selected_date, '%Y-%m-%d')

    # Форматирование строки времени для сравнения
    formatted_date = selected_datetime.strftime('%Y-%m-%d')

    # Поиск в базе данных по дню, месяцу и году
    cursor.execute('SELECT * FROM weather_data WHERE timestamp BETWEEN ? AND ?', (formatted_date + " 00:00:00", formatted_date + " 23:59:59"))
    result = cursor.fetchone()

    # Получаем все данные для графика
    data_graph = WeatherData.query.filter(func.date(WeatherData.timestamp) == formatted_date).all()

    # Создаем DataFrame из данных
    df = pd.DataFrame([(data.detailed_status, data.wind_speed, data.humidity, data.temperature, data.clouds, data.timestamp) for data in data_graph], columns=['detailed_status', 'wind_speed', 'humidity', 'temperature','clouds', 'timestamp'])

    # Преобразуем столбец timestamp в формат datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    fig = make_subplots(rows=1, cols=1, subplot_titles=["Temperature over Time"])
    
    fig2 = make_subplots(rows=1, cols=1, subplot_titles=["Wind speed over Time"])
    
    fig3 = make_subplots(rows=1, cols=1, subplot_titles=["Humidity over Time"])
    
    fig4 = make_subplots(rows=1, cols=1, subplot_titles=["Clouds over Time"])

    # Добавляем линии для каждого параметра
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['temperature'], mode='lines+markers', name='Temp °C',text=df['temperature']), row=1, col=1)
    
    fig2.add_trace(go.Scatter(x=df['timestamp'], y=df['wind_speed'], mode='lines+markers', name='Wind km/h',text=df['wind_speed']), row=1, col=1)
    
    fig3.add_trace(go.Histogram(x=df['timestamp'], y=df['humidity'], name='Humidity %', text=df['humidity']), row=1, col=1)
    
    fig4.add_trace(go.Histogram(x=df['timestamp'], y=df['clouds'], name='Clouds %', text=df['clouds']), row=1, col=1)

    # Добавляем аннотации с detailed_status
    for index, row in df.iterrows():
        # Подписываем только часовые и полуторачасовые метки
        if row['timestamp'].minute % 30 == 0:
            annotation_text = f"Temperature: {row['temperature']} °C"
            fig.add_annotation(
                go.layout.Annotation(
                    x=row['timestamp'],
                    y=row['temperature'],
                    text=annotation_text,
                    showarrow=False,
                    font=dict(size=8),
                    xshift=10,
                    yshift=10,
                )
            )
            # Добавьте другие аннотации, как на главной странице

            # Добавляем аннотацию для detailed_status ниже температуры
            detailed_status_text = f"Details: {row['detailed_status']}"
            fig.add_annotation(
                go.layout.Annotation(
                    x=row['timestamp'],
                    y=row['temperature'],
                    text=detailed_status_text,
                    showarrow=False,
                    font=dict(size=8),
                    xshift=10,
                    yshift=-10,  # Перемещаем немного вниз
                )
            )

            annotation_text = f"Wind: {row['wind_speed']} km/h"
            fig2.add_annotation(
                go.layout.Annotation(
                    x=row['timestamp'],
                    y=row['wind_speed'],
                    text=annotation_text,
                    showarrow=False,
                    font=dict(size=8),
                    xshift=10,
                    yshift=10,
                )
            )

            annotation_text = f"Humidity: {row['humidity']} %"
            fig3.add_annotation(
                go.layout.Annotation(
                    x=row['timestamp'],
                    y=row['humidity'],
                    text=annotation_text,
                    showarrow=False,
                    font=dict(size=8),
                    xshift=10,
                    yshift=10,
                )
            )

            annotation_text = f"Clouds: {row['clouds']} %"
            fig4.add_annotation(
                go.layout.Annotation(
                    x=row['timestamp'],
                    y=row['clouds'],
                    text=annotation_text,
                    showarrow=False,
                    font=dict(size=8),
                    xshift=10,
                    yshift=10,
                )
            )

    # Обновляем макет графика с новым положением
    fig.update_layout(
        showlegend=True,
        height=300,
        width=900,
        margin=dict(l=10, r=10, t=30, b=10),
    )
    
    fig2.update_layout(
        showlegend=True,
        height=300,
        width=900,
        margin=dict(l=10, r=10, t=30, b=10),
    )
    
    fig3.update_layout(
        showlegend=True,
        height=300,
        width=900,
        margin=dict(l=10, r=10, t=30, b=10),
    )
    
    fig4.update_layout(
        showlegend=True,
        height=300,
        width=900,
        margin=dict(l=10, r=10, t=30, b=10),
    )

    # Сохраняем график в HTML
    graph_html = fig.to_html(full_html=False)
    
    graph_html2 = fig2.to_html(full_html=False)
    
    graph_html3 = fig3.to_html(full_html=False)
    
    graph_html4 = fig4.to_html(full_html=False)
    
    min_temperature = df['temperature'].min()
    max_temperature = df['temperature'].max()
    min_wind_speed = df['wind_speed'].min()
    max_wind_speed = df['wind_speed'].max()
    min_humidity = df['humidity'].min()
    max_humidity = df['humidity'].max()
    min_clouds = df['clouds'].min()
    max_clouds = df['clouds'].max()

    conn.close()

    if result:
        # Если найдена запись, передайте результаты и график на страницу результатов
        return render_template('search_page.html', selected_date=selected_date, result=result, graph_html=graph_html, graph_html2=graph_html2, graph_html3=graph_html3, graph_html4=graph_html4,weather_data=weather_data, min_temperature=min_temperature, max_temperature=max_temperature,min_wind_speed=min_wind_speed,max_wind_speed=max_wind_speed,min_humidity=min_humidity,max_humidity=max_humidity,min_clouds=min_clouds,max_clouds=max_clouds)
    else:
        # Если запись не найдена, перенаправьте на другую страницу
        return redirect(url_for('not_search_page'))


@app.route('/not_search_page')
def not_search_page():
    return render_template('not_search_page.html')


@app.route('/main_search', methods=['POST', 'GET'])
def page_search():
    # Тут основные данные
    weather_data = get_weather()
    new_weather_entry = WeatherData(*weather_data)
    db.session.add(new_weather_entry)
    db.session.commit()

    return render_template('main_search.html', weather_data=weather_data)


@app.route('/main_table', methods=['POST', 'GET'])
def page_main_table():
    # Тут основные данные
    weather_data = get_weather()
    new_weather_entry = WeatherData(*weather_data)
    db.session.add(new_weather_entry)
    db.session.commit()

    # Дальше график

    # Получаем данные из базы данных
    data_graph = WeatherData.query.all()

    # Создаем DataFrame из данных
    df = pd.DataFrame([(data.detailed_status, data.wind_speed, data.humidity, data.temperature, data.clouds, data.timestamp) for data in data_graph], columns=['detailed_status', 'wind_speed', 'humidity', 'temperature', 'clouds', 'timestamp'])

    # Преобразуем столбец timestamp в формат datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    fig = make_subplots(rows=1, cols=1, subplot_titles=["Temperature over Time"])
    
    fig2 = make_subplots(rows=1, cols=1, subplot_titles=["Wind speed over Time"])
    
    fig3 = make_subplots(rows=1, cols=1, subplot_titles=["Humidity over Time"])
    
    fig4 = make_subplots(rows=1, cols=1, subplot_titles=["Clouds over Time"])

    # Добавляем линии для каждого параметра
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['temperature'], mode='lines+markers', name='Temp °C',text=df['temperature']), row=1, col=1)
    
    fig2.add_trace(go.Scatter(x=df['timestamp'], y=df['wind_speed'], mode='lines+markers', name='Wind km/h',text=df['wind_speed']), row=1, col=1)
    
    fig3.add_trace(go.Histogram(x=df['timestamp'], y=df['humidity'], name='Humidity %', text=df['humidity']), row=1, col=1)
    
    fig4.add_trace(go.Histogram(x=df['timestamp'], y=df['clouds'], name='Clouds %', text=df['clouds']), row=1, col=1)

    # Добавляем аннотации с detailed_status
    for index, row in df.iterrows():
        # Подписываем только часовые и полуторачасовые метки
        if row['timestamp'].minute % 30 == 0:
            annotation_text = f" {row['temperature']} °C"
            fig.add_annotation(
                go.layout.Annotation(
                    x=row['timestamp'],
                    y=row['temperature'],
                    text=annotation_text,
                    showarrow=False,
                    font=dict(size=8),
                    xshift=10,
                    yshift=10,
                )
            )

            # Добавляем аннотацию для detailed_status ниже температуры
            detailed_status_text = f"Details: {row['detailed_status']}"
            fig.add_annotation(
                go.layout.Annotation(
                    x=row['timestamp'],
                    y=row['temperature'],
                    text=detailed_status_text,
                    showarrow=False,
                    font=dict(size=8),
                    xshift=10,
                    yshift=-10,  # Перемещаем немного вниз
                )
            )

            annotation_text = f" {row['wind_speed']} km/h"
            fig2.add_annotation(
                go.layout.Annotation(
                    x=row['timestamp'],
                    y=row['wind_speed'],
                    text=annotation_text,
                    showarrow=False,
                    font=dict(size=8),
                    xshift=10,
                    yshift=10,
                )
            )


    # Обновляем макет графика с новым положением
    fig.update_layout(
        showlegend=True,
        height=300,
        width=900,
        margin=dict(l=10, r=10, t=30, b=10),
    )
    
    fig2.update_layout(
        showlegend=True,
        height=300,
        width=900,
        margin=dict(l=10, r=10, t=30, b=10),
    )
    
    fig3.update_layout(
        showlegend=True,
        height=300,
        width=900,
        margin=dict(l=10, r=10, t=30, b=10),
    )
    
    fig4.update_layout(
        showlegend=True,
        height=300,
        width=900,
        margin=dict(l=10, r=10, t=30, b=10),
    )

    # Сохраняем график в HTML
    graph_html = fig.to_html(full_html=False)
    
    graph_html2 = fig2.to_html(full_html=False)
    
    graph_html3 = fig3.to_html(full_html=False)
    
    graph_html4 = fig4.to_html(full_html=False)
    
    # Получаем минимальные и максимальные значения
    min_temperature = df['temperature'].min()
    max_temperature = df['temperature'].max()
    min_wind_speed = df['wind_speed'].min()
    max_wind_speed = df['wind_speed'].max()
    min_humidity = df['humidity'].min()
    max_humidity = df['humidity'].max()
    min_clouds = df['clouds'].min()
    max_clouds = df['clouds'].max()

    return render_template('main_table.html', weather_data=weather_data, graph_html=graph_html, graph_html2=graph_html2, graph_html3=graph_html3, graph_html4=graph_html4, min_temperature=min_temperature, max_temperature=max_temperature,min_wind_speed=min_wind_speed,max_wind_speed=max_wind_speed,min_humidity=min_humidity,max_humidity=max_humidity,min_clouds=min_clouds,max_clouds=max_clouds)
    


if __name__ == '__main__':
    app.run(debug=True)