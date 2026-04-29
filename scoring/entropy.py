import math
from collections import Counter
from typing import List, Dict, Any

class EntropyCalculator:
    """
    Shannon entropy calculator for behavioral patterns.
    Supports timing, gas, and diversity entropy for SRS scoring.
    """
    
    @staticmethod
    def compute_entropy(values: List[int]) -> float:
        """
        Standard Shannon entropy in bits (log2)
        
        Args:
            values: List of discrete values (hours 0-23, gas percentiles, protocol IDs)
        
        Returns:
            Entropy in bits (0 to log2(number_of_unique_values))
        """
        if not values:
            return 0.0
        
        counts = Counter(values)
        total = len(values)
        
        entropy = 0.0
        for count in counts.values():
            p = count / total
            entropy -= p * math.log2(p)
        
        return entropy
    
    @staticmethod
    def shannon_entropy(timestamps: List[int]) -> float:
        """
        Alias for compute_entropy - maintains backward compatibility
        """
        return EntropyCalculator.compute_entropy(timestamps)
    
    @staticmethod
    def normalize_entropy(entropy: float, max_buckets: int = 24) -> float:
        """
        Normalize entropy to 0-100 scale.
        
        Args:
            entropy: Raw entropy in bits
            max_buckets: Number of possible values (24 for hours, 48 for half-hours)
        """
        max_entropy = math.log2(max_buckets)
        if max_entropy == 0:
            return 0.0
        normalized = (entropy / max_entropy) * 100
        return min(100.0, max(0.0, normalized))
    
    @staticmethod
    def interpret_timing_entropy(entropy_bits: float) -> Dict[str, Any]:
        """
        Interpret H_timing based on hour-of-day distribution (24 buckets)
        
        Zones:
        - Human: > 4.5 bits (very random, human-like behavior)
        - Bot: < 2.0 bits (highly predictable, automated behavior)
        - Grey: 2.0 - 4.5 bits (needs corroboration)
        """
        max_bits = math.log2(24)  # 4.585 bits
        
        if entropy_bits > 4.5:
            zone = "Human"
            interpretation = "Transaction timing resembles human activity patterns"
            risk_contribution = 0.15  # Low risk
            action = "Low risk behavior - proceed with normal analysis"
        elif entropy_bits < 2.0:
            zone = "Bot"
            interpretation = "Transaction timing follows automated, predictable patterns"
            risk_contribution = 0.85  # High risk
            action = "High risk - requires additional verification (Pillar 2 & 3)"
        else:
            zone = "Grey"
            interpretation = "Inconclusive timing patterns"
            risk_contribution = 0.50  # Medium risk
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
        """
        Complete H_timing calculation from hour-of-day list
        """
        entropy = EntropyCalculator.compute_entropy(hours)
        return EntropyCalculator.interpret_timing_entropy(entropy)
    
    @staticmethod
    def get_entropy_score(entropy: float) -> Dict[str, Any]:
        """
        Legacy method - returns normalized score and category
        """
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
        """
        Combine all three entropy pillars with weights:
        H_combined = 0.35 × H_timing + 0.30 × H_gas + 0.35 × H_diversity
        
        For now, returns timing-only score until Pillar 2 & 3 are implemented
        """
        weights = {
            "timing": 0.35,
            "gas": 0.30,
            "diversity": 0.35
        }
        
        # If only timing available, return normalized timing score
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
        
        # Full combined score
        combined = (
            weights["timing"] * h_timing +
            weights["gas"] * h_gas +
            weights["diversity"] * h_diversity
        )
        
        max_possible = math.log2(24)  # Assumes same scale
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