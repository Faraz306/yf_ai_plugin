import streamlit as st

st.set_page_config(page_title="Hello App", page_icon="👋")

st.title("Welcome!")
name = st.text_input("Enter your name:")

if name and name.strip():
    st.success(f"Hello, {name}!")
else:
    st.info("Please enter your name above to see a personalized greeting.")
