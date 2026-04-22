import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

class SRSEngine:
    def __init__(self):
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        self.cache: Dict[str, Any] = {}
        self._load_cache()
    
    def _load_cache(self):
        cache_file = self.data_dir / "wallet_cache.json"
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                self.cache = json.load(f)
    
    def _save_cache(self):
        cache_file = self.data_dir / "wallet_cache.json"
        with open(cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)
    
    def evaluate_wallet(self, wallet_address: str) -> Dict[str, Any]:
        score = self._calculate_score(wallet_address)
        return {
            "wallet": wallet_address,
            "score": score,
            "risk_level": self._determine_risk_level(score),
            "timestamp": datetime.utcnow().isoformat(),
            "cached": wallet_address in self.cache
        }
    
    def get_score(self, wallet_address: str) -> float:
        if wallet_address in self.cache:
            return self.cache[wallet_address].get("score", 0.0)
        return self._calculate_score(wallet_address)
    
    def cache_data(self, wallet_address: str, data: Dict[str, Any]):
        self.cache[wallet_address] = {
            **data,
            "cached_at": datetime.utcnow().isoformat()
        }
        self._save_cache()
    
    def _calculate_score(self, wallet_address: str) -> float:
        hash_val = abs(hash(wallet_address)) % 100
        score = float(hash_val)
        
        if wallet_address in self.cache:
            cached_data = self.cache[wallet_address]
            if "additional_metrics" in cached_data:
                score = (score + cached_data["additional_metrics"].get("trust_factor", 50)) / 2
        
        return round(score, 2)
    
    def _determine_risk_level(self, score: float) -> str:
        if score >= 80:
            return "Low Risk"
        elif score >= 50:
            return "Medium Risk"
        elif score >= 25:
            return "High Risk"
        else:
            return "Critical Risk"
