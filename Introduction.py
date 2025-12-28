import streamlit as st

# 1. Настройка названия страницы (вкладки браузера)
# Внимание: эта команда должна быть САМОЙ ПЕРВОЙ командой Streamlit в коде
st.set_page_config(
    page_title="data blessing by Novvi",
    page_icon="⚽",  # Можно поменять иконку на другую
    layout="wide"
)

# 2. Скрытие "водяных знаков" (меню, футера и хедера)
hide_streamlit_style = """
<style>
/* Скрывает гамбургер-меню справа сверху */
#MainMenu {visibility: hidden;}

/* Скрывает футер "Made with Streamlit" */
footer {visibility: hidden;}

/* Скрывает верхнюю полосу (где кнопка Deploy) для более чистого вида */
header {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# 3. Если вы хотите добавить заголовок прямо на страницу текстом:
st.title("data blessing by Novvi")

# --- Ниже должен идти ваш основной код приложения ---
