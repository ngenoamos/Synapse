# 🏛️ Cathedral Scanner

### Enterprise-Grade Blockchain Analytics Platform

[![Deployed on Railway](https://img.shields.io/badge/Deployed%20on-Railway-FFB4B4?logo=railway)](https://web-production-22abf.up.railway.app)
[![API Status](https://img.shields.io/website?url=https%3A%2F%2Fweb-production-22abf.up.railway.app%2Fhealth&label=API%20Status&color=green)](https://web-production-22abf.up.railway.app/health)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.6-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-Private-red.svg)]()

---

## 🚀 Live Demo

| Service                    | URL | Status |
|----------------------------|-----|--------|
| **Landing Page**           | [cathedral-scanner.up.railway.app](https://web-production-22abf.up.railway.app)        | 🟢 Online |
| **Interactive API Docs**   | [web-production-22abf.up.railway.app/docs](https://web-production-22abf.up.railway.app/docs)   | 🟢 Online |
| **Health Check**           | [web-production-22abf.up.railway.app/health](https://web-production-22abf.up.railway.app/health) | 🟢 Online |

**Try these live queries in your browser:**
- 💰 [Scan $7B Binance Wallet](https://web-production-22abf.up.railway.app/api/scan/0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8?chain=ethereum)
- 👤 [Scan Vitalik Buterin](https://web-production-22abf.up.railway.app/api/scan/0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045?chain=ethereum)
- 🔗 [Scan $7.8B BSC Bridge](https://web-production-22abf.up.railway.app/api/scan/0x0000000000000000000000000000000000001004?chain=bsc)
- 🏆 [View Top 10 Wallets](https://web-production-22abf.up.railway.app/api/top_wallets?limit=10)

---

## 📊 Platform Capabilities

| Feature                  | Status  | Description                 |
|--------------------------|---------|-----------------------------|
| **Real Blockchain Data** | ✅ Live | Ethereum + BSC mainnet      |
| **Multi-Chain Support**  | ✅ Live | ETH, BSC (more coming)      |
| **SRS Risk Scoring**     | ✅ Live | 0-100 proprietary algorithm |
| **Transaction Analysis** | ✅ Live | Counts, contract detection  |
| **USD Conversion**       | ✅ Live | Real-time prices            |
| **Caching Layer**        | ✅ Live | Performance optimized       |
| **REST API**             | ✅ Live | FastAPI with auto-docs      |
| **Web Dashboard**        | ✅ Live | Streamlit UI                |

---

## 🎯 SRS Scoring System

Our proprietary **Scoring & Ranking System** evaluates wallets on:

| Factor              | Weight                | Description            |
|---------------------|-----------------------|------------------------|
| Balance Size        | 30%                   | Total value held       |
| Transaction History | 25%                   | Activity and age       |
| Contract Risk       | 20%                   | Smart contract vs EOA  |
| On-chain Behavior   | 25%                   | Patterns and anomalies |

**Risk Categories:**
- 🟢 **Low Risk** (80-100): High-value, active, verified wallets
- 🟡 **Medium Risk** (50-79): Moderate activity, some concerns
- 🟠 **High Risk** (25-49): Suspicious patterns
- 🔴 **Critical Risk** (0-24): High-risk or malicious wallets

---

## 🛠️ Tech Stack

```yaml
Backend:
  - Python 3.11
  - FastAPI (async web framework)
  - Web3.py (blockchain interaction)
  - Uvicorn (ASGI server)

Blockchain:
  - Ethereum (via public RPC + fallbacks)
  - BSC (Binance Smart Chain)
  - Multi-provider redundancy

Frontend:
  - Streamlit (dashboard)
  - HTML/CSS/JS (landing page)
  - Plotly (visualizations)

Infrastructure:
  - Railway (cloud deployment)
  - Git (version control)
  - GitHub (private repository)


🚀 Quick Start
Clone & Run Locally
bash
# Clone the repository
git clone https://github.com/ngenoamos/Synapse.git
cd Synapse

# Create virtual environment with Python 3.11
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn main:app --reload --port 8000
Test the API
bash
# Health check
curl http://localhost:8000/health

# Scan a wallet
curl "http://localhost:8000/api/scan/0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8?chain=ethereum"

# Get top wallets
curl "http://localhost:8000/api/top_wallets?limit=5"
📡 API Endpoints
Method	Endpoint	Description
GET	/	Landing page
GET	/health	Health check
GET	/docs	Interactive Swagger docs
GET	/api/scan/{wallet}?chain={chain}	Scan wallet address
GET	/api/score/{wallet}	Get SRS score only
GET	/api/top_wallets?limit={n}	Top wallets by score
GET	/api/cache_stats	Cache performance
POST	/api/cache/{wallet}	Cache wallet data
