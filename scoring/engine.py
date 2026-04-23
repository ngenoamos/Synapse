import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import requests
from web3 import Web3
import os
import asyncio

class SRSEngine:
    """Real SRS Engine with blockchain integration"""
    
    def __init__(self):
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        self.cache: Dict[str, Any] = {}
        self._load_cache()
        
        # Blockchain providers
        self.eth_provider = "https://cloudflare-eth.com"
        self.w3 = Web3(Web3.HTTPProvider(self.eth_provider))
    
    def _load_cache(self):
        cache_file = self.data_dir / "wallet_cache.json"
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                self.cache = json.load(f)
    
    def _save_cache(self):
        cache_file = self.data_dir / "wallet_cache.json"
        with open(cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)
    
    def cache_data(self, wallet_address: str, data: Dict[str, Any]):
        self.cache[wallet_address] = {
            **data,
            "cached_at": datetime.utcnow().isoformat()
        }
        self._save_cache()
    
    def get_real_wallet_data_sync(self, wallet_address: str, chain: str = "ethereum") -> Dict[str, Any]:
        """Synchronous version to fetch real wallet data"""
        
        # Check cache first
        if wallet_address in self.cache:
            return self.cache[wallet_address]
        
        try:
            if chain == "ethereum":
                return self._get_ethereum_data_sync(wallet_address)
            elif chain == "bsc":
                return self._get_bsc_data_sync(wallet_address)
            else:
                return {"error": f"Chain {chain} not fully implemented yet", "address": wallet_address}
        except Exception as e:
            return {"error": str(e), "address": wallet_address}
    
    def _get_ethereum_data_sync(self, address: str) -> Dict[str, Any]:
        """Fetch real Ethereum wallet data with multiple RPC endpoints"""
    
        try:
            # Fix address checksum
            from web3 import Web3
            
            # Try to normalize address
            try:
                # Convert to checksum address if valid
                if Web3.is_address(address):
                    address = Web3.to_checksum_address(address)
                else:
                    return {"error": f"Invalid Ethereum address format: {address}", "address": address}
            except:
                return {"error": f"Cannot validate address: {address}", "address": address}
            
            # Try multiple RPC endpoints
            rpc_endpoints = [
                "https://eth.llamarpc.com",
                "https://rpc.ankr.com/eth",
                "https://ethereum.publicnode.com",
                "https://cloudflare-eth.com"
            ]
            
            balance_eth = 0
            tx_count = 0
            is_contract = False
            working_rpc = None
            
            for rpc_url in rpc_endpoints:
                try:
                    w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 5}))
                    if w3.is_connected():
                        # Get ETH balance
                        balance_wei = w3.eth.get_balance(address)
                        balance_eth = float(w3.from_wei(balance_wei, 'ether'))
                        
                        # Get transaction count
                        tx_count = w3.eth.get_transaction_count(address)
                        
                        # Check if it's a contract
                        is_contract = len(w3.eth.get_code(address)) > 0
                        
                        working_rpc = rpc_url
                        break  # Success with this RPC
                except:
                    continue  # Try next RPC
            
            if working_rpc is None:
                return {"error": "All Ethereum RPC endpoints failed", "address": address}
            
            wallet_data = {
                "address": address,
                "chain": "ethereum",
                "balance_eth": round(balance_eth, 6),
                "balance_usd": round(balance_eth * 3500, 2),
                "transaction_count": tx_count,
                "is_contract": is_contract,
                "trust_score": self._calculate_trust_score(balance_eth, tx_count),
                "timestamp": datetime.utcnow().isoformat(),
                "rpc_used": working_rpc
            }
            
            # Cache the data
            self.cache_data(address, wallet_data)
            return wallet_data
            
        except Exception as e:
            return {"error": f"Failed to fetch Ethereum data: {str(e)}", "address": address}
    
    def _get_bsc_data_sync(self, address: str) -> Dict[str, Any]:
        """Fetch BSC wallet data"""
        try:
            bsc_provider = "https://bsc-dataseed.binance.org/"
            w3_bsc = Web3(Web3.HTTPProvider(bsc_provider))
            
            balance_wei = w3_bsc.eth.get_balance(address)
            balance_bnb = float(w3_bsc.from_wei(balance_wei, 'ether'))
            
            wallet_data = {
                "address": address,
                "chain": "bsc",
                "balance_bnb": round(balance_bnb, 6),
                "balance_usd": round(balance_bnb * 300, 2),
                "trust_score": self._calculate_trust_score(balance_bnb, 0),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.cache_data(address, wallet_data)
            return wallet_data
            
        except Exception as e:
            return {"error": f"Failed to fetch BSC data: {str(e)}", "address": address}
    
    def _calculate_trust_score(self, balance: float, tx_count: int) -> float:
        """Calculate trust score based on real metrics"""
        score = 50  # Base score
        
        # Balance contributes up to 30 points
        if balance > 100:
            score += 30
        elif balance > 10:
            score += 20
        elif balance > 1:
            score += 10
        elif balance > 0.1:
            score += 5
        
        # Transaction count contributes up to 20 points
        if tx_count > 1000:
            score += 20
        elif tx_count > 100:
            score += 15
        elif tx_count > 10:
            score += 10
        elif tx_count > 0:
            score += 5
        
        return min(100, max(0, score))
    
    def evaluate_wallet_sync(self, wallet_address: str, chain: str = "ethereum") -> Dict[str, Any]:
        """Evaluate wallet with real blockchain data (synchronous)"""
        real_data = self.get_real_wallet_data_sync(wallet_address, chain)
        
        if "error" in real_data:
            return real_data
        
        # Calculate SRS score based on real metrics
        trust_score = real_data.get("trust_score", 50)
        balance = real_data.get("balance_eth", 0)
        
        # Adjust score based on balance
        final_score = trust_score
        if balance > 100:
            final_score += 5
        elif balance > 50:
            final_score += 2
        
        # Penalty for contracts
        if real_data.get("is_contract", False):
            final_score -= 15
        
        final_score = max(0, min(100, final_score))
        
        return {
            "wallet": wallet_address,
            "chain": chain,
            "srs_score": round(final_score, 2),
            "risk_level": self._determine_risk_level(final_score),
            "wallet_data": real_data,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_balance_sync(self, wallet_address: str, chain: str = "ethereum") -> Dict[str, Any]:
        """Get balance for a wallet"""
        return self.get_real_wallet_data_sync(wallet_address, chain)
    
    def get_top_wallets_sync(self, limit: int = 10) -> list:
        """Get top wallets by trust score"""
        scored_wallets = []
        
        for address, data in self.cache.items():
            if isinstance(data, dict) and "trust_score" in data:
                scored_wallets.append({
                    "address": address,
                    "score": data.get("trust_score", 0),
                    "balance": data.get("balance_eth", data.get("balance_bnb", 0)),
                    "chain": data.get("chain", "unknown")
                })
        
        scored_wallets.sort(key=lambda x: x["score"], reverse=True)
        return scored_wallets[:limit]
    
    def _determine_risk_level(self, score: float) -> str:
        if score >= 80:
            return "Low Risk"
        elif score >= 50:
            return "Medium Risk"
        elif score >= 25:
            return "High Risk"
        else:
            return "Critical Risk"
        
    def get_token_holdings(self, address):
        # Use Moralis or Alchemy API
        pass