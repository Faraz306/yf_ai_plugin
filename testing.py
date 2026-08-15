import streamlit as st

st.title('Hello, World!')

username = st.text_input('What is your name?')

if st.button('Say Hello'): 
    st.write(f'Hello, {username}!')
