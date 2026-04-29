import os
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

class CovalentFetcher:
    """Handles all Covalent API data fetching"""
    
    def __init__(self):
        self.api_key = os.getenv("COVALENT_API_KEY", "")
        self.base_url = "https://api.covalenthq.com/v1"
        print(f"🔑 API Key loaded: {self.api_key[:20] if self.api_key else 'NOT FOUND'}...")
        
    def get_transactions_last_180_days(self, address: str, chain: str = "eth-mainnet") -> Optional[List[Dict]]:
        """
        Fetch transactions - gets multiple pages to ensure we have recent transactions.
        """
        all_transactions = []
        page_number = 0
        max_pages = 5  # Get up to 500 transactions
        
        print(f"📡 Fetching transactions for {address[:10]}... on {chain}")
        
        while page_number < max_pages:
            url = f"{self.base_url}/{chain}/address/{address}/transactions_v2/"
            params = {
                "key": self.api_key,
                "page-size": 100,
                "page-number": page_number
            }
            
            try:
                response = requests.get(url, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    transactions = data.get("data", {}).get("items", [])
                    
                    if not transactions:
                        break
                    
                    all_transactions.extend(transactions)
                    print(f"📡 Page {page_number}: Got {len(transactions)} transactions (total: {len(all_transactions)})")
                    
                    page_number += 1
                else:
                    print(f"❌ API Error: {response.status_code}")
                    break
                    
            except Exception as e:
                print(f"❌ Exception: {e}")
                break
        
        # Filter by last 180 days - FIX TIMEZONE ISSUE
        from datetime import timezone, timedelta
        
        # Make cutoff timezone-aware
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=180)
        filtered_transactions = []
        
        for tx in all_transactions:
            block_time = tx.get("block_signed_at")
            if block_time:
                try:
                    # Parse and make timezone-aware
                    tx_date = datetime.fromisoformat(block_time.replace('Z', '+00:00'))
                    # Ensure tx_date is timezone-aware
                    if tx_date.tzinfo is None:
                        tx_date = tx_date.replace(tzinfo=timezone.utc)
                    
                    if tx_date > cutoff_date:
                        filtered_transactions.append(tx)
                except Exception as e:
                    print(f"⚠️ Error parsing date: {e}")
                    pass
        
        print(f"📡 Final: {len(all_transactions)} total, {len(filtered_transactions)} from last 180 days")
        return filtered_transactions
    
    def get_wallet_balance(self, address: str, chain: str = "eth-mainnet") -> Optional[float]:
        """Fetch current wallet balance"""
        url = f"{self.base_url}/{chain}/address/{address}/balances_v2/"
        params = {"key": self.api_key}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                items = data.get("data", {}).get("items", [])
                if items:
                    balance = float(items[0].get("balance", "0")) / 1e18
                    return balance
            return 0.0
        except:
            return 0.0