import streamlit as st
import requests
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Cathedral Scanner", layout="wide")

st.title("🏛️ Cathedral Scanner - Enterprise Blockchain Analytics")

# Sidebar
with st.sidebar:
    st.header("Configuration")
    chain = st.selectbox("Blockchain", ["ethereum", "bsc"])
    api_url = st.text_input("API URL", "http://localhost:8000")
    
    st.header("Quick Links")
    st.markdown("""
    - [Binance Hot Wallet](https://etherscan.io/address/0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8)
    - [Vitalik Buterin](https://etherscan.io/address/0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045)
    - [BNB Bridge](https://bscscan.com/address/0x0000000000000000000000000000000000001004)
    """)

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    st.header("🔍 Wallet Scanner")
    wallet_address = st.text_input("Enter Wallet Address", 
                                   placeholder="0x...")
    
    if st.button("Scan Wallet", type="primary"):
        if wallet_address:
            with st.spinner("Fetching blockchain data..."):
                response = requests.get(
                    f"{api_url}/api/scan/{wallet_address}",
                    params={"chain": chain}
                )
                data = response.json()
                
                if "error" in data:
                    st.error(f"Error: {data['error']}")
                else:
                    st.success("✅ Wallet scanned successfully!")
                    
                    # Display metrics
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric("SRS Score", f"{data['srs_score']}/100")
                    with col_b:
                        st.metric("Risk Level", data['risk_level'])
                    with col_c:
                        st.metric("Last Scanned", 
                                 data['timestamp'].split('T')[0])
                    
                    # Wallet data
                    st.subheader("Wallet Data")
                    if "wallet_data" in data:
                        wallet_data = data['wallet_data']
                        balance_key = f"balance_{chain}"
                        usd_key = "balance_usd"
                        
                        metrics = st.columns(4)
                        metrics[0].metric(
                            "Balance", 
                            f"{wallet_data.get(balance_key, 0):,.4f} {chain.upper()}"
                        )
                        metrics[1].metric(
                            "USD Value", 
                            f"${wallet_data.get(usd_key, 0):,.2f}"
                        )
                        metrics[2].metric(
                            "Transactions", 
                            wallet_data.get('transaction_count', 'N/A')
                        )
                        metrics[3].metric(
                            "Trust Score", 
                            f"{wallet_data.get('trust_score', 0)}%"
                        )
                        
                        # Risk gauge
                        fig = go.Figure(go.Indicator(
                            mode = "gauge+number+delta",
                            value = data['srs_score'],
                            title = {'text': "Risk Assessment"},
                            domain = {'x': [0, 1], 'y': [0, 1]},
                            gauge = {
                                'axis': {'range': [None, 100]},
                                'bar': {'color': "darkblue"},
                                'steps': [
                                    {'range': [0, 25], 'color': "red"},
                                    {'range': [25, 50], 'color': "orange"},
                                    {'range': [50, 75], 'color': "yellow"},
                                    {'range': [75, 100], 'color': "green"}
                                ],
                                'threshold': {
                                    'line': {'color': "red", 'width': 4},
                                    'thickness': 0.75,
                                    'value': data['srs_score']
                                }
                            }
                        ))
                        fig.update_layout(height=300)
                        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.header("📊 Top Wallets")
    if st.button("Refresh Rankings"):
        response = requests.get(f"{api_url}/api/top_wallets?limit=10")
        top_wallets = response.json().get('top_wallets', [])
        
        if top_wallets:
            df = pd.DataFrame(top_wallets)
            st.dataframe(
                df,
                column_config={
                    "address": "Wallet Address",
                    "score": st.column_config.NumberColumn("SRS Score", format="%.0f"),
                    "balance": st.column_config.NumberColumn("Balance", format="%.2f"),
                    "chain": "Chain"
                },
                use_container_width=True
            )
        else:
            st.info("No wallets cached yet. Scan some wallets first!")

# Cache stats
st.header("💾 System Status")
response = requests.get(f"{api_url}/api/cache_stats")
cache_stats = response.json()

col1, col2, col3 = st.columns(3)
col1.metric("Cached Wallets", cache_stats.get('cached_wallets', 0))
col2.metric("Cache File", cache_stats.get('cache_file', 'N/A'))
col3.metric("API Status", "🟢 Online")

# Footer
st.markdown("---")
st.markdown("**Cathedral Scanner v1.0** | Real-time Blockchain Analytics")
