"""Shannon entropy calculations for timing patterns"""

import math
from collections import Counter
from typing import List, Dict, Any, Optional
from .config import HOUR_BUCKETS, DAY_BUCKETS


class EntropyCalculator:
    """Calculate Shannon entropy for various distributions"""
    
    @staticmethod
    def compute_entropy(values: List[int], max_buckets: Optional[int] = None) -> float:
        """Standard Shannon entropy in bits (log2)"""
        if not values:
            return 0.0
        
        counts = Counter(values)
        total = len(values)
        
        entropy = 0.0
        for count in counts.values():
            p = count / total
            entropy -= p * math.log2(p)
        
        return entropy
    
    # ============ YOUR EXISTING METHODS (KEEP) ============
    
    @staticmethod
    def shannon_entropy(timestamps: List[int]) -> float:
        """Alias for compute_entropy - maintains backward compatibility"""
        return EntropyCalculator.compute_entropy(timestamps)
    
    @staticmethod
    def normalize_entropy(entropy: float, max_buckets: int = 24) -> float:
        """Normalize entropy to 0-100 scale"""
        max_entropy = math.log2(max_buckets)
        if max_entropy == 0:
            return 0.0
        normalized = (entropy / max_entropy) * 100
        return min(100.0, max(0.0, normalized))
    
    @staticmethod
    def interpret_timing_entropy(entropy_bits: float) -> Dict[str, Any]:
        """Interpret H_timing based on hour-of-day distribution (24 buckets)"""
        max_bits = math.log2(24)
        
        if entropy_bits > 4.5:
            zone = "Human"
            interpretation = "Transaction timing resembles human activity patterns"
            risk_contribution = 0.15
            action = "Low risk behavior - proceed with normal analysis"
        elif entropy_bits < 2.0:
            zone = "Bot"
            interpretation = "Transaction timing follows automated, predictable patterns"
            risk_contribution = 0.85
            action = "High risk - requires additional verification (Pillar 2 & 3)"
        else:
            zone = "Grey"
            interpretation = "Inconclusive timing patterns"
            risk_contribution = 0.50
            action = "Needs Pillar 2 (gas) and Pillar 3 (protocol) corroboration"
        
        return {
            "type": "H_timing",
            "entropy_bits": round(entropy_bits, 4),
            "max_possible_bits": round(max_bits, 4),
            "normalized_score": round((entropy_bits / max_bits) * 100, 1),
            "zone": zone,
            "interpretation": interpretation,
            "action": action,
            "risk_contribution": risk_contribution
        }
    
    @staticmethod
    def get_h_timing_from_hours(hours: List[int]) -> Dict[str, Any]:
        """Complete H_timing calculation from hour-of-day list"""
        entropy = EntropyCalculator.compute_entropy(hours)
        return EntropyCalculator.interpret_timing_entropy(entropy)
    
    @staticmethod
    def get_entropy_score(entropy: float) -> Dict[str, Any]:
        """Legacy method - returns normalized score and category"""
        normalized = EntropyCalculator.normalize_entropy(entropy)
        
        if normalized >= 70:
            category = "High Randomness / Bot-like"
        elif normalized >= 40:
            category = "Medium Randomness / Human-like"
        else:
            category = "Low Randomness / Routine"
        
        return {
            "raw_entropy": round(entropy, 4),
            "normalized_score": round(normalized, 2),
            "behavior_category": category,
            "max_possible_entropy": round(math.log2(24), 4)
        }
    
    @staticmethod
    def compute_combined_score(h_timing: float, h_gas: float = None, h_diversity: float = None) -> Dict[str, Any]:
        """Combine all three entropy pillars with weights"""
        weights = {"timing": 0.35, "gas": 0.30, "diversity": 0.35}
        
        if h_gas is None or h_diversity is None:
            max_bits = math.log2(24)
            normalized = (h_timing / max_bits) * 100
            return {
                "combined_entropy": round(h_timing, 4),
                "normalized_score": round(normalized, 1),
                "weights": weights,
                "components": {"h_timing": round(h_timing, 4)},
                "note": "Pillar 2 (gas) and Pillar 3 (diversity) not yet implemented"
            }
        
        combined = (weights["timing"] * h_timing + weights["gas"] * h_gas + weights["diversity"] * h_diversity)
        max_possible = math.log2(24)
        normalized = (combined / max_possible) * 100
        
        return {
            "combined_entropy": round(combined, 4),
            "normalized_score": round(normalized, 1),
            "weights": weights,
            "components": {
                "h_timing": round(h_timing, 4),
                "h_gas": round(h_gas, 4),
                "h_diversity": round(h_diversity, 4)
            }
        }
    
    # ============ NEW METHODS (ADD FROM MY VERSION) ============
    
    @staticmethod
    def get_h_timing_with_days(hours: List[int], days: List[int]) -> Dict[str, Any]:
        """
        Calculate combined timing entropy from hours (24) + days (7)
        This gives 31 total buckets (24 + 7)
        """
        if not hours or not days:
            return EntropyCalculator.get_h_timing_from_hours(hours)
        
        # Calculate separate entropies
        h_hours = EntropyCalculator.compute_entropy(hours, 24)
        h_days = EntropyCalculator.compute_entropy(days, 7)
        
        # Combined (average of normalized scores)
        max_hours = math.log2(24)
        max_days = math.log2(7)
        
        norm_hours = (h_hours / max_hours) * 100 if max_hours > 0 else 0
        norm_days = (h_days / max_days) * 100 if max_days > 0 else 0
        
        combined_norm = (norm_hours + norm_days) / 2
        combined_bits = (h_hours + h_days) / 2
        
        # Zone determination uses normalized score
        if combined_norm >= 75:
            zone = "Human"
        elif combined_norm < 35:
            zone = "Bot"
        else:
            zone = "Grey"
        
        return {
            "type": "H_timing",
            "entropy_bits": round(combined_bits, 4),
            "normalized_score": round(combined_norm, 1),
            "zone": zone,
            "components": {
                "hour_entropy": round(h_hours, 4),
                "hour_normalized": round(norm_hours, 1),
                "day_entropy": round(h_days, 4),
                "day_normalized": round(norm_days, 1)
            }
        }