"""Gas bid entropy calculation for H_gas (Pillar 2)"""

import math
from collections import Counter
from typing import List, Dict, Any, Optional
from .config import GAS_BUCKETS


class GasEntropyCalculator:
    """
    Calculate H_gas - entropy of gas bid distribution.
    Measures how predictably a wallet bids on gas prices.
    """
    
    @staticmethod
    def extract_gas_prices(transactions: List[Dict]) -> List[float]:
        """
        Extract gas prices from transactions (in Gwei).
        
        Args:
            transactions: List of transaction dicts from Covalent
        
        Returns:
            List of gas prices in Gwei
        """
        gas_prices = []
        
        for tx in transactions:
            # Get gas price in wei
            gas_price_wei = tx.get("gas_price")
            if gas_price_wei:
                try:
                    # Convert wei to Gwei (1 Gwei = 1e9 wei)
                    gas_price_gwei = float(gas_price_wei) / 1e9
                    gas_prices.append(gas_price_gwei)
                except:
                    pass
        
        return gas_prices
    
    @staticmethod
    def get_gas_percentile_buckets(gas_prices: List[float]) -> List[int]:
        """
        Convert gas prices to percentile buckets (0-19) based on distribution.
        
        Creates 20 equal-sized buckets based on the overall distribution.
        A bucket of 0 = lowest gas prices, 19 = highest gas prices.
        
        Args:
            gas_prices: List of gas prices in Gwei
        
        Returns:
            List of bucket indices (0-19)
        """
        if not gas_prices:
            return []
        
        # Sort gas prices to find percentiles
        sorted_prices = sorted(gas_prices)
        n = len(sorted_prices)
        
        # Define bucket boundaries (20 buckets = 5% each)
        # Bucket 0: 0-5th percentile, Bucket 1: 5-10th, ..., Bucket 19: 95-100th
        boundaries = []
        for i in range(GAS_BUCKETS):
            percentile = (i + 1) * (100 / GAS_BUCKETS)
            idx = int((percentile / 100) * n)
            if idx >= n:
                idx = n - 1
            boundaries.append(sorted_prices[idx])
        
        # Assign each gas price to a bucket
        buckets = []
        for price in gas_prices:
            assigned = False
            for i, boundary in enumerate(boundaries):
                if price <= boundary:
                    buckets.append(i)
                    assigned = True
                    break
            if not assigned:
                buckets.append(GAS_BUCKETS - 1)
        
        return buckets
    
    @staticmethod
    def calculate_h_gas(buckets: List[int]) -> float:
        """
        Calculate H_gas using Shannon entropy.
        
        Args:
            buckets: List of bucket indices (0-19)
        
        Returns:
            Entropy in bits (0 to log2(20) ≈ 4.32)
        """
        if not buckets:
            return 0.0
        
        counts = Counter(buckets)
        total = len(buckets)
        
        entropy = 0.0
        for count in counts.values():
            p = count / total
            entropy -= p * math.log2(p)
        
        return entropy
    
    @staticmethod
    def interpret_h_gas(entropy_bits: float, max_buckets: int = GAS_BUCKETS) -> Dict[str, Any]:
        """
        Interpret H_gas score.
        
        Human behavior: high entropy (uses range of gas prices, sometimes overpays)
        Bot behavior: low entropy (perfect optimization, always pays minimum)
        """
        max_entropy = math.log2(max_buckets)  # ~4.32 bits
        normalized = (entropy_bits / max_entropy) * 100 if max_entropy > 0 else 0
        
        if normalized >= 60:
            zone = "Human"
            interpretation = "Varied gas bidding - shows emotional/irrational patterns"
            risk_contribution = 0.15
        elif normalized >= 30:
            zone = "Grey"
            interpretation = "Moderate gas variance - inconclusive"
            risk_contribution = 0.50
        else:
            zone = "Bot"
            interpretation = "Optimized gas bidding - perfect economic efficiency (bot-like)"
            risk_contribution = 0.85
        
        return {
            "type": "H_gas",
            "entropy_bits": round(entropy_bits, 4),
            "max_possible_bits": round(max_entropy, 4),
            "normalized_score": round(normalized, 1),
            "zone": zone,
            "interpretation": interpretation,
            "risk_contribution": risk_contribution
            # REMOVED: "samples": len(buckets) if buckets else 0
        }