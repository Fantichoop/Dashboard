# Import required modules
# Импорт необходимых модулей
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_migrate import Migrate
from datetime import datetime, timedelta
from pyowm import OWM
import plotly
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import pandas as pd
import sqlite3


# Initializing the Flash application
# Инициализация Flask-приложения
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather_data.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)


# Defining the data model for the WeatherData table
# Определение модели данных для таблицы WeatherData
class WeatherData(db.Model):
    # Defining table fields
    # Определение полей таблицы
    id = db.Column(db.Integer, primary_key=True)
    detailed_status = db.Column(db.String(255))
    wind_speed = db.Column(db.Integer)
    humidity = db.Column(db.Integer)
    temperature = db.Column(db.Integer)
    clouds = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime)

    # Class constructor for creating a new WeatherData object
    # Конструктор класса для создания нового объекта WeatherData
    def __init__(self, detailed_status, wind_speed, humidity, temperature, clouds, timestamp):
        # Assigning the values of the passed arguments to the corresponding fields of the model
        # Присвоение значений переданных аргументов соответствующим полям модели
        self.detailed_status = detailed_status
        self.wind_speed = wind_speed
        self.humidity = humidity
        self.temperature = temperature
        self.clouds = clouds
        self.timestamp = timestamp


# Initialization of the last update time
# Инициализация времени последнего обновления
last_update_time = datetime.utcnow()

# Function for getting the current weather using the pyowm library
# Функция для получения текущей погоды с использованием библиотеки pyowm
def get_weather():
    global last_update_time

    # Initializing an OWM object using an API key
    # Инициализация объекта OWM с использованием API-ключа
    owm = OWM('8309c7b50d12a283c0df3ed52803ac85')
    
    # Initializing the weather manager
    # Инициализация менеджера погоды
    mgr = owm.weather_manager()

    # Getting current weather data for the specified location (Tomsk, RU)
    # Получение данных о текущей погоде для указанного местоположения (Tomsk, RU)
    observation = mgr.weather_at_place('Tomsk,RU')
    w = observation.weather

    # Extraction of various weather parameters
    # Извлечение различных параметров погоды
    detailed = w.detailed_status
    win = w.wind()
    h = w.humidity
    t = w.temperature('celsius')
    cl = w.clouds

    # Calculating the timestamp taking into account the offset of 7 o'clock relative to UTC
    # Вычисление метки времени с учетом смещения в 7 часов относительно UTC
    timestamp = datetime.utcnow() + timedelta(hours=7)

    # Update the time of the last update
    # Обновление времени последнего обновления
    last_update_time = timestamp

    # Return weather parameters as a tuple
    # Возврат параметров погоды в виде кортежа
    return detailed, round(win['speed']), h, round(t['temp']), cl, timestamp


# Function for connecting to SQLite database
# Функция для подключения к базе данных SQLite
def connect_db():
    # Returns a connection to the SQLite database using the 'weather_data.db' file in the 'instance' folder
    # Возвращает соединение с базой данных SQLite, используя файл 'weather_data.db' в папке 'instance'
    return sqlite3.connect('instance/weather_data.db')


# Main route home page display
# Основной маршрут - отображение главной страницы
@app.route('/')
def main_page():
    # Getting current weather data
    # Получение текущих данных о погоде
    weather_data = get_weather()
    
    # Creating a new weather record in the database with the received data
    # Создание новой записи о погоде в базе данных с полученными данными
    new_weather_entry = WeatherData(*weather_data)
    db.session.add(new_weather_entry)
    db.session.commit()

    # Template display 'main_page.html ' with transmitting weather data as a parameter
    # Отображение шаблона 'main_page.html' с передачей данных о погоде в качестве параметра
    return render_template('main_page.html', weather_data=weather_data)


# Route to display a page with a date search field
# Маршрут для отображения страницы с полем для поиска по дате
@app.route('/main_search', methods=['POST', 'GET'])
def page_search():
    # Here is the basic data
    # Тут основные данные
    weather_data = get_weather()
    new_weather_entry = WeatherData(*weather_data)
    db.session.add(new_weather_entry)
    db.session.commit()

    return render_template('main_search.html', weather_data=weather_data)


# Route to display a page with search results by date
# Маршрут для отображения страницы с результатами поиска по дате
@app.route('/search_page', methods=['POST', 'GET'])
def search_results():
    # Getting the selected date from the form data
    # Получение выбранной даты из данных формы
    selected_date = request.form['selected_date']
    
    # Getting current weather data
    # Получение текущих данных о погоде
    weather_data = get_weather()

    # Connecting to the SQLite database
    # Подключение к базе данных SQLite
    conn = connect_db()
    cursor = conn.cursor()

    # Converting a date string to a datetime object
    # Преобразование строки даты в объект datetime
    selected_datetime = datetime.strptime(selected_date, '%Y-%m-%d')

    # Formatting the time string for comparison in the database
    # Форматирование строки времени для сравнения в базе данных
    formatted_date = selected_datetime.strftime('%Y-%m-%d')

    # Search the database of records for the selected date
    # Поиск в базе данных записей за выбранную дату
    cursor.execute('SELECT * FROM weather_data WHERE timestamp BETWEEN ? AND ?', (formatted_date + " 00:00:00", formatted_date + " 23:59:59"))
    result = cursor.fetchone()

    # Getting all the data for plotting
    # Получение всех данных для построения графика
    data_graph = WeatherData.query.filter(func.date(WeatherData.timestamp) == formatted_date).all()

    # Creating a Data Frame from the received data
    # Создание DataFrame из полученных данных
    df = pd.DataFrame([(data.detailed_status, data.wind_speed, data.humidity, data.temperature, data.clouds, data.timestamp) for data in data_graph], columns=['detailed_status', 'wind_speed', 'humidity', 'temperature','clouds', 'timestamp'])

    # Converting a timestamp column to datetime format
    # Преобразование столбца timestamp в формат datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # # Creating graphs using the plotly library
    # Создание графиков с использованием библиотеки plotly
    fig = make_subplots(rows=1, cols=1, subplot_titles=["Temperature over Time"])
    fig2 = make_subplots(rows=1, cols=1, subplot_titles=["Wind speed over Time"])
    fig3 = make_subplots(rows=1, cols=1, subplot_titles=["Humidity over Time"])
    fig4 = make_subplots(rows=1, cols=1, subplot_titles=["Clouds over Time"])

    # Adding lines for each parameter to the charts
    # Добавление линий для каждого параметра на графике
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['temperature'], mode='lines+markers', name='°C',text=df['temperature']), row=1, col=1)
    fig2.add_trace(go.Scatter(x=df['timestamp'], y=df['wind_speed'], mode='lines+markers', name='km/h',text=df['wind_speed']), row=1, col=1)
    fig3.add_trace(go.Histogram(x=df['timestamp'], y=df['humidity'], name='%', text=df['humidity']), row=1, col=1)
    fig4.add_trace(go.Histogram(x=df['timestamp'], y=df['clouds'], name='%', text=df['clouds']), row=1, col=1)

    # Adding annotations to graphs
    # Добавление аннотаций к графикам
    for index, row in df.iterrows():
        # We only sign hour and hour and a half markers
        # Подписываем только часовые и полуторачасовые метки
        if row['timestamp'].minute % 240 == 0:
            annotation_text = f"{row['temperature']} °C"
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

            # Adding an annotation for detailed_status below the temperature
            # Добавляем аннотацию для detailed_status ниже температуры
            detailed_status_text = f"{row['detailed_status']}"
            fig.add_annotation(
                go.layout.Annotation(
                    x=row['timestamp'],
                    y=row['temperature'],
                    text=detailed_status_text,
                    showarrow=False,
                    font=dict(size=8),
                    xshift=10,
                    yshift=-10,  # Перемещаем немного вниз # Move it down a little bit
                )
            )

            annotation_text = f"{row['wind_speed']} km/h"
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

    # Updating graph layouts with new parameters
    # Обновление макетов графиков с новыми параметрами
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

    # Getting HTML code to insert graphs on a page
    # Получение HTML-кода для вставки графиков на страницу
    graph_html = fig.to_html(full_html=False)
    graph_html2 = fig2.to_html(full_html=False)
    graph_html3 = fig3.to_html(full_html=False)
    graph_html4 = fig4.to_html(full_html=False)
    
    
    # Getting the minimum and maximum parameter values to display on the page
    # Получение минимальных и максимальных значений параметров для отображения на странице
    min_temperature = df['temperature'].min()
    max_temperature = df['temperature'].max()
    min_wind_speed = df['wind_speed'].min()
    max_wind_speed = df['wind_speed'].max()
    min_humidity = df['humidity'].min()
    max_humidity = df['humidity'].max()
    min_clouds = df['clouds'].min()
    max_clouds = df['clouds'].max()

    # Closing the database connection
    # Закрытие соединения с базой данных
    conn.close()

    if result:
        # If a record is found, transfer the results and graphs to the results page
        # Если найдена запись, передача результатов и графиков на страницу результатов
        return render_template('search_page.html', selected_date=selected_date, result=result, graph_html=graph_html, graph_html2=graph_html2, graph_html3=graph_html3, graph_html4=graph_html4, weather_data=weather_data, min_temperature=min_temperature, max_temperature=max_temperature, min_wind_speed=min_wind_speed, max_wind_speed=max_wind_speed, min_humidity=min_humidity, max_humidity=max_humidity, min_clouds=min_clouds, max_clouds=max_clouds)
    else:
        # If the record is not found, redirect to the error information page
        # Если запись не найдена, перенаправление на страницу с информацией об ошибке
        return redirect(url_for('not_search_page'))


# The route to display the page if the date search did not yield results
# Маршрут для отображения страницы, если поиск по дате не дал результатов
@app.route('/not_search_page')
def not_search_page():
    return render_template('not_search_page.html')


# Route to display the page with the main table and graphs
# Маршрут для отображения страницы с основной таблицей и графиками
@app.route('/main_table', methods=['POST', 'GET'])
def page_main_table():
    # Getting the current weather
    # Получение текущей погоды
    weather_data = get_weather()
    
    # Create a new weather record in the database
    # Создание новой записи о погоде в базе данных
    new_weather_entry = WeatherData(*weather_data)
    db.session.add(new_weather_entry)
    db.session.commit()

    # Getting data from the database
    # Получение данных из базы данных
    data_graph = WeatherData.query.all()

    # Creating a DataFrame from data
    # Создание DataFrame из данных
    df = pd.DataFrame([(data.detailed_status, data.wind_speed, data.humidity, data.temperature, data.clouds, data.timestamp) for data in data_graph], columns=['detailed_status', 'wind_speed', 'humidity', 'temperature', 'clouds', 'timestamp'])

    # Converting a timestamp column to datetime format
    # Преобразование столбца timestamp в формат datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Creating graphs
    # Создание графиков
    fig = make_subplots(rows=1, cols=1, subplot_titles=["Temperature over Time"])
    fig2 = make_subplots(rows=1, cols=1, subplot_titles=["Wind speed over Time"])
    fig3 = make_subplots(rows=1, cols=1, subplot_titles=["Humidity over Time"])
    fig4 = make_subplots(rows=1, cols=1, subplot_titles=["Clouds over Time"])

    # Adding lines for each parameter
    # Добавление линий для каждого параметра
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['temperature'], mode='lines+markers', name='°C', text=df['temperature']), row=1, col=1)
    fig2.add_trace(go.Scatter(x=df['timestamp'], y=df['wind_speed'], mode='lines+markers', name='km/h', text=df['wind_speed']), row=1, col=1)
    fig3.add_trace(go.Histogram(x=df['timestamp'], y=df['humidity'], name='%', text=df['humidity']), row=1, col=1)
    fig4.add_trace(go.Histogram(x=df['timestamp'], y=df['clouds'], name='%', text=df['clouds']), row=1, col=1)

    # Adding annotations with detailed_status
    # Добавление аннотаций с detailed_status
    for index, row in df.iterrows():
        # We only sign hour and hour and a half markers
        # Подписываем только часовые и полуторачасовые метки
        if row['timestamp'].minute % 240 == 0:
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

            # Adding annotation for detailed_status below temperature
            # Добавление аннотации для detailed_status ниже температуры
            detailed_status_text = f"{row['detailed_status']}"
            fig.add_annotation(
                go.layout.Annotation(
                    x=row['timestamp'],
                    y=row['temperature'],
                    text=detailed_status_text,
                    showarrow=False,
                    font=dict(size=8),
                    xshift=10,
                    yshift=-10,  # Перемещаем немного вниз  # Move it down a little bit
                )
            )

            annotation_text = f"{row['wind_speed']} km/h"
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

    # Updating the graph layout with a new position
    # Обновление макета графика с новым положением
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

    # Saving graphs in HTML
    # Сохранение графиков в HTML
    graph_html = fig.to_html(full_html=False)
    graph_html2 = fig2.to_html(full_html=False)
    graph_html3 = fig3.to_html(full_html=False)
    graph_html4 = fig4.to_html(full_html=False)
    
    # Getting minimum and maximum values
    # Получение минимальных и максимальных значений
    min_temperature = df['temperature'].min()
    max_temperature = df['temperature'].max()
    min_wind_speed = df['wind_speed'].min()
    max_wind_speed = df['wind_speed'].max()
    min_humidity = df['humidity'].min()
    max_humidity = df['humidity'].max()
    min_clouds = df['clouds'].min()
    max_clouds = df['clouds'].max()

    return render_template('main_table.html', weather_data=weather_data, graph_html=graph_html, graph_html2=graph_html2, graph_html3=graph_html3, graph_html4=graph_html4, min_temperature=min_temperature, max_temperature=max_temperature, min_wind_speed=min_wind_speed, max_wind_speed=max_wind_speed, min_humidity=min_humidity, max_humidity=max_humidity, min_clouds=min_clouds, max_clouds=max_clouds)

# Running the application in debug mode
# Запуск приложения в режиме отладки
if __name__ == '__main__':
    app.run(debug=True)
