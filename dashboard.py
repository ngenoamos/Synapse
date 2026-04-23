import streamlit as st
import requests
import plotly.graph_objects as go

st.title("Cathedral Scanner - Live Blockchain Analytics")
wallet = st.text_input("Enter Wallet Address")
chain = st.selectbox("Blockchain", ["ethereum", "bsc"])

if wallet:
    data = requests.get(f"http://localhost:8000/api/scan/{wallet}?chain={chain}").json()
    st.json(data)
    
    # Show balance chart
    if "wallet_data" in data:
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = data['srs_score'],
            title = {'text': "SRS Risk Score"},
            domain = {'x': [0, 1], 'y': [0, 1]}
        ))
        st.plotly_chart(fig)
