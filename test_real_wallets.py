import requests
import json

# Test real wallets
wallets = {
    "ethereum": [
        "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",  # Vitalik
        "0xbe0eB53F46cd790Cd13851d5EFf43D12404d33E8",  # Binance
        "0x28C6c06298d514Db089934071355E5743bf21d60"   # DEX aggregator
    ],
    "bsc": [
        "0x10ED43C718714eb63d5aA57B78B54704E256024E",  # PancakeSwap
        "0x0000000000000000000000000000000000001004",  # BNB Bridge
        "0x2170Ed0880ac89A755fd29B2688956BD959F933F"   # ETH on BSC
    ]
}

for chain, addresses in wallets.items():
    print(f"\n=== Testing {chain.upper()} wallets ===")
    for wallet in addresses:
        response = requests.get(f"http://localhost:8000/api/scan/{wallet}?chain={chain}")
        data = response.json()
        if "wallet_data" in data:
            balance_key = f"balance_{chain}"
            balance = data["wallet_data"].get(balance_key, 0)
            print(f"✅ {wallet[:10]}... - Balance: {balance} {chain.upper()} - Score: {data['srs_score']}")
        else:
            print(f"❌ {wallet[:10]}... - Error: {data.get('error', 'Unknown')}")

# Check cache stats
stats = requests.get("http://localhost:8000/api/cache_stats")
print(f"\n📊 Cache Stats: {stats.json()}")
