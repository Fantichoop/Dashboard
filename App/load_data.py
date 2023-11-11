import streamlit as st
import pandas as pd

# Загрузка данных
data = pd.read_csv('your_data.csv')

# Отображение данных
st.subheader('Data Overview')
st.write(data.head())

# Показ статистики данных
st.subheader('Data Statistics')
st.write(data.describe())