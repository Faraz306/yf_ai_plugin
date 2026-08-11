import streamlit as st

st.title("Welcome!")

name = st.text_input("What is your name?")

if name:
    st.write(f"Hello, {name}!")
