# 🏛️ Cathedral Scanner

### Enterprise-Grade Sybil-Resistance Scoring Engine (SRS)

[![Deployed on Render](https://img.shields.io/badge/Deployed%20on-Render-46E3B7?logo=render)](https://cathedral-scanner-api.onrender.com)
[![API Status](https://img.shields.io/website?url=https%3A%2F%2Fcathedral-scanner-api.onrender.com%2Fhealth&label=API%20Status&color=green)](https://cathedral-scanner-api.onrender.com/health)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.6-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-Private-red.svg)](https://github.com/ngenoamos/Synapse)

---

## 🚀 Live Demo

| Service | URL | Status |
|---------|-----|--------|
| **API Root** | [cathedral-scanner-api.onrender.com](https://cathedral-scanner-api.onrender.com) | 🟢 Online |
| **Interactive API Docs** | [cathedral-scanner-api.onrender.com/docs](https://cathedral-scanner-api.onrender.com/docs) | 🟢 Online |
| **Health Check** | [cathedral-scanner-api.onrender.com/health](https://cathedral-scanner-api.onrender.com/health) | 🟢 Online |
| **Frontend UI** | [ngenoamos.github.io/cathedral-scanner-frontend](https://ngenoamos.github.io/cathedral-scanner-frontend) | 🟢 Online |

**Try these live queries in your browser:**
- 🧠 [Full SRS Analysis (Binance Wallet)](https://cathedral-scanner-api.onrender.com/api/complete-srs/0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8?chain=ethereum)
- 📊 [Behavioral Entropy (Vitalik)](https://cathedral-scanner-api.onrender.com/api/entropy/0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045?chain=ethereum)
- 🔍 [Quick Scan (BNB Bridge)](https://cathedral-scanner-api.onrender.com/api/scan/0x0000000000000000000000000000000000001004?chain=bsc)
- 🏆 [Top 10 Wallets by Trust Score](https://cathedral-scanner-api.onrender.com/api/top_wallets?limit=10)

---

## 📊 SRS Scoring System (Week 2 Complete)

Our proprietary **Scoring & Ranking System** uses Shannon entropy across three pillars:

| Pillar | Weight | Description | Status |
|--------|--------|-------------|--------|
| **H_timing** | 35% | Transaction time-of-day entropy (24-hour buckets) | ✅ Complete |
| **H_gas** | 30% | Gas price percentile distribution | 🔄 Week 3 |
| **H_diversity** | 35% | Protocol interaction diversity | 🔄 Week 3 |

**Formula:** `H_combined = 0.35×H_timing + 0.30×H_gas + 0.35×H_diversity`

### Liveness Gate
- **Minimum threshold:** 50 qualifying transactions
- **SRS = 0** for wallets with insufficient activity
- Filters: Self-transfers, zero-value, token approvals removed

### Zone Interpretation (H_timing)
| Zone | Entropy Range | Interpretation |
|------|---------------|----------------|
| 🟢 **Human** | > 4.5 bits | Random, human-like timing |
| 🟡 **Grey** | 2.0 - 4.5 bits | Needs corroboration |
| 🔴 **Bot** | < 2.0 bits | Automated, predictable patterns |

---

## 🌐 Frontend (SPA with 4 Tabs)

**Live URL:** https://ngenoamos.github.io/cathedral-scanner-frontend

The frontend is a modern Single Page Application with:

| Tab | Function | Endpoint |
|-----|----------|----------|
| 🔍 **Quick Scan** | Balance + trust score | `/api/scan/{wallet}` |
| 📊 **SRS Analysis** | Complete three-pillar score | `/api/complete-srs/{wallet}` |
| 🧠 **Behavioral Entropy** | H_timing only | `/api/entropy/{wallet}` |
| 🏆 **Top Wallets** | Leaderboard | `/api/top_wallets` |

**Technology:** HTML5 + Tailwind CSS + Chart.js + Vanilla JavaScript

---

## 🛠️ Tech Stack

```yaml
Backend:
  - Python 3.11
  - FastAPI (async web framework)
  - Web3.py (blockchain interaction)
  - Uvicorn (ASGI server)
  - Covalent API (transaction history)

Blockchain:
  - Ethereum (via multiple RPC fallbacks)
  - BSC (Binance Smart Chain)
  - Covalent (historical transactions)

Data Processing:
  - Shannon entropy calculation (log2)
  - 24-hour bucket distribution
  - Transaction filtering (self-transfer, zero-value, approvals)

Frontend:
  - Tailwind CSS (styling)
  - Chart.js (visualizations)
  - Vanilla JavaScript (SPA)

Infrastructure:
  - Render.com (cloud deployment)
  - GitHub (private repository)
  - GitHub Pages (frontend hosting)
📈 Real-World Test Results
Wallet	Qualifying TXs	H_timing	Zone	SRS Score
Binance Hot Wallet	70	2.94 bits	Grey	89.26
Vitalik Buterin	16	2.78 bits	Grey	N/A*
Low-activity wallet	3	N/A	Failed	0 (liveness gate)
Vitalik's wallet is a contract, limiting qualifying transactions

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

# Set up environment variables
echo "COVALENT_API_KEY=your_key_here" > .env

# Run the server
uvicorn main:app --reload --port 8000
Test the API
bash
# Health check
curl http://localhost:8000/health

# Full SRS analysis
curl "http://localhost:8000/api/complete-srs/0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8?chain=ethereum"

# Behavioral entropy only
curl "http://localhost:8000/api/entropy/0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8?chain=ethereum"

# Quick scan
curl "http://localhost:8000/api/scan/0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8?chain=ethereum"

# Top wallets
curl "http://localhost:8000/api/top_wallets?limit=5"
📡 API Endpoints
Method	Endpoint	Description
GET	/	API information
GET	/health	Health check
GET	/docs	Interactive Swagger docs
GET	/api/scan/{wallet}	Quick scan (balance + trust)
GET	/api/entropy/{wallet}	Behavioral entropy (H_timing)
GET	/api/complete-srs/{wallet}	Full three-pillar SRS score
GET	/api/top_wallets	Top wallets by trust score
GET	/api/cache_stats	Cache performance
🎯 Roadmap
Status	Feature	Target
✅	FastAPI backend	Week 1
✅	Covalent API integration	Week 1
✅	24-hour bucket entropy (H_timing)	Week 2
✅	Liveness gate (50+ transactions)	Week 2
✅	SPA frontend with 4 tabs	Week 2
✅	Multi-chain support (ETH, BSC)	Week 2
🔄	Gas entropy (H_gas - Pillar 2)	Week 3
🔄	Protocol diversity (H_diversity - Pillar 3)	Week 3
⏳	Solana integration	Q2 2026
⏳	Machine learning scoring	Q3 2026
🔒 Security & Privacy
✅ Private GitHub repository

✅ No sensitive data exposure

✅ API keys stored as environment variables

✅ CORS configured for security

✅ Rate limiting ready

👥 For Co-Founders
Investment Highlights
✅ Working Product: Live API scanning real blockchain data

✅ Proprietary Algorithm: Shannon entropy-based SRS scoring

✅ Liveness Gate: 50+ transaction minimum prevents gaming

✅ Multi-Chain: ETH + BSC live, more coming

✅ Cloud Deployed: Accessible anywhere

✅ Git History: Development tracked from Day 1

Key Metrics
TAM: $2.4T cryptocurrency market

Target Users: Traders, analysts, compliance teams

Competitive Edge: Behavioral entropy + multi-chain + proprietary scoring

Live Demo
API: https://cathedral-scanner-api.onrender.com

Frontend: https://ngenoamos.github.io/cathedral-scanner-frontend

Docs: https://cathedral-scanner-api.onrender.com/docs

📞 Contact
GitHub: github.com/ngenoamos

Project: github.com/ngenoamos/Synapse

Live API: cathedral-scanner-api.onrender.com

Frontend: ngenoamos.github.io/cathedral-scanner-frontend

📄 License
Private Repository - All Rights Reserved

text

## Key Changes to Make:

1. **Update API URLs:** `web-production-22abf.up.railway.app` → `cathedral-scanner-api.onrender.com`
2. **Add Week 2 features:** H_timing, entropy, liveness gate, 24-hour buckets
3. **Update frontend URL:** Add your GitHub Pages frontend
4. **Add test results table** with actual data
5. **Update roadmap** to reflect Week 2 completion

## Update your README on GitHub:

```bash
cd /home/amos/Desktop/TheCathedral/cathedral-scanner
nano README.md
# Paste the updated content above

git add README.md
git commit -m "Update README with Week 2 features and correct API URLs"
git push