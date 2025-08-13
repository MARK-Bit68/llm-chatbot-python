import streamlit as st
from ui_theme import apply_global_theme

st.set_page_config(
    page_title="Hello",
    page_icon="👋",
)
apply_global_theme()

st.write("# Welcome to Streamlit! 👋")

st.markdown("""
This component supports **markdown formatting**.

[Check out their documentation](https://docs.streamlit.io) for more information on how to get started.
""")

st.write('updated')