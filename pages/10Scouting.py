import streamlit as st

# 1. Настройка страницы (должна быть первой)
st.set_page_config(
    page_title="data blessing by Novvi",
    page_icon="⚽",
    layout="wide"
)

# 2. Скрываем водяные знаки и меню
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# 3. Заголовок и ваша фраза
st.title("data blessing by Novvi")
st.caption("uhm, im lazy for scouting frr") # caption делает текст чуть меньше и серым

# --- Дальше идет ваш основной код (графики, таблицы и т.д.) ---