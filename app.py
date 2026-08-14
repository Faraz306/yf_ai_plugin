import streamlit as st
import yfinance as yf

st.title('Stock Portfolio Backtester')

uploaded_file = st.file_uploader('Choose a CSV file', type='csv')

if uploaded_file is not None:
    df = pd.read_csv(upload_file)
    st.write(df)
    st.write(yf.download(df['Stocks'][0], start='2020-01-01', end='2022-12-31'))
