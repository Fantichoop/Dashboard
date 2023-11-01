import streamlit as st
import pandas as pd

# Загрузка данных
data = pd.read_csv('your_data.csv')

# Установика заголовка страницы
st.title('Data Monitoring Dashboard')

# Отображение данных
st.subheader('Data Overview')
st.write(data.head())

# Показ статистики данных
st.subheader('Data Statistics')
st.write(data.describe())

# Визуализация данных при помощи диаграм
st.subheader('Data Visualization')

# Диаграмма - столбы
st.subheader('Bar Chart')
bar_chart_data = data['column_name'].value_counts()
st.bar_chart(bar_chart_data)

# Диаграмма - линейная
st.subheader('Line Chart')
line_chart_data = data['column_name']
st.line_chart(line_chart_data)

# Диаграмма площади
st.subheader('Area Chart')
area_chart_data = data['column_name']
st.area_chart(area_chart_data)

# Точечный график
st.subheader('Scatter Plot')
scatter_plot_data = data[['column_name_1', 'column_name_2']]
st.scatterplot(scatter_plot_data['column_name_1'], scatter_plot_data['column_name_2'])

# Добавление других визуализаций по мере необходимости

# Показывает необработанные данные
st.subheader('Raw Data')
st.write(data)

# Добавляет интерактивность(необязательно)
# Интерактивность - степень взаимодействия между субъектами и объектами
# Пример: Фильтрация данных на основе определенного условия
st.sidebar.title('Filter Data')
selected_category = st.sidebar.selectbox('Select Category', data['category'].unique())
filtered_data = data[data['category'] == selected_category]
st.write(filtered_data)


