import os
import requests
from typing import Dict, Any, List, Optional, Generator
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

class CovalentFetcher:
    """Handles all Covalent API data fetching with memory-efficient streaming"""
    
    def __init__(self):
        self.api_key = os.getenv("COVALENT_API_KEY", "")
        self.base_url = "https://api.covalenthq.com/v1"
        print(f"🔑 API Key loaded: {self.api_key[:20] if self.api_key else 'NOT FOUND'}...")
    
    def stream_transactions(self, address: str, chain: str = "eth-mainnet", max_pages: int = 3, page_size: int = 50) -> Generator[List[Dict], None, None]:
        """
        STREAM transactions page by page - memory efficient!
        Only keeps current page in memory, not all transactions.
        
        Args:
            address: Wallet address
            chain: Blockchain network (eth-mainnet, bsc-mainnet)
            max_pages: Maximum number of pages to fetch
            page_size: Number of transactions per page
        """
        url = f"{self.base_url}/{chain}/address/{address}/transactions_v2/"
        page_number = 0
        
        print(f"📡 Streaming transactions for {address[:10]}... on {chain}")
        
        while page_number < max_pages:
            params = {
                "key": self.api_key,
                "page-size": page_size,
                "page-number": page_number
            }
            
            try:
                response = requests.get(url, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    transactions = data.get("data", {}).get("items", [])
                    
                    if not transactions:
                        break
                    
                    print(f"📡 Page {page_number}: Streaming {len(transactions)} transactions")
                    yield transactions
                    
                    page_number += 1
                else:
                    print(f"❌ API Error: {response.status_code}")
                    break
                    
            except Exception as e:
                print(f"❌ Exception: {e}")
                break
    
    def get_transactions_last_180_days(self, address: str, chain: str = "eth-mainnet", max_pages: int = 3) -> Optional[List[Dict]]:
        """
        Legacy method - collects all transactions (memory heavier).
        Use stream_transactions() for memory efficiency.
        """
        all_transactions = []
        
        for page in self.stream_transactions(address, chain, max_pages):
            all_transactions.extend(page)
        
        # Filter by last 180 days
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=180)
        filtered_transactions = []
        
        for tx in all_transactions:
            block_time = tx.get("block_signed_at")
            if block_time:
                try:
                    tx_date = datetime.fromisoformat(block_time.replace('Z', '+00:00'))
                    if tx_date.tzinfo is None:
                        tx_date = tx_date.replace(tzinfo=timezone.utc)
                    
                    if tx_date > cutoff_date:
                        filtered_transactions.append(tx)
                except:
                    pass
        
        print(f"📡 Final: {len(filtered_transactions)} from last 180 days")
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