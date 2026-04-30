"""Protocol diversity tracking for H_diversity (Pillar 3)"""

import math
from typing import Dict, Any, Set, List
from .config import ALL_TIER_1_ADDRESSES, MIN_DIVERSITY_PROTOCOLS, TARGET_DIVERSITY_PROTOCOLS


class DiversityTracker:
    """Track and score protocol diversity for H_diversity"""
    
    def __init__(self):
        self.tier_1_addresses = ALL_TIER_1_ADDRESSES
    
    def extract_counterparties(self, transactions: List[Dict], wallet_address: str) -> Set[str]:
        """Extract unique counterparty addresses from qualifying transactions"""
        counterparties = set()
        wallet_lower = wallet_address.lower()
        
        for tx in transactions:
            from_addr = (tx.get("from_address") or "").lower()
            to_addr = (tx.get("to_address") or "").lower()
            
            if from_addr == wallet_lower and to_addr:
                counterparties.add(to_addr)
            elif to_addr == wallet_lower and from_addr:
                counterparties.add(from_addr)
        
        return counterparties
    
    def classify_counterparties(self, counterparties: Set[str]) -> Dict[str, Any]:
        """Classify counterparties into categories and count unique protocols"""
        matched_protocols = set()
        
        for cp in counterparties:
            if cp in self.tier_1_addresses:
                matched_protocols.add(cp)
        
        return {
            "total_counterparties": len(counterparties),
            "tier_1_count": len(matched_protocols),
            "tier_0_count": len(counterparties) - len(matched_protocols),
            "external_degree": len(matched_protocols),
            "matched_protocols": list(matched_protocols)
        }
    
    def calculate_h_diversity(self, classification: Dict[str, Any]) -> float:
        """
        Calculate H_diversity using protocol count.
        
        Formula: H_diversity = log2(protocol_count + 1) normalized to 0-4.585 bits
        Returns entropy in bits (0 to 4.585)
        """
        protocol_count = classification.get("tier_1_count", 0)
        
        if protocol_count == 0:
            return 0.0
        
        # Shannon entropy based on protocol count
        # More protocols = higher entropy
        # log2(protocol_count + 1) - adding 1 to handle count=1
        entropy = math.log2(protocol_count + 1)
        
        # Cap at max entropy (log2(25) ≈ 4.64, close to log2(24) for consistency)
        max_entropy = math.log2(TARGET_DIVERSITY_PROTOCOLS + 1)
        entropy = min(entropy, max_entropy)
        
        return entropy
    
    def interpret_h_diversity(self, protocol_count: int) -> Dict[str, Any]:
        """
        Interpret H_diversity score and provide actionable insights.
        """
        max_entropy = math.log2(TARGET_DIVERSITY_PROTOCOLS + 1)
        entropy = math.log2(protocol_count + 1) if protocol_count > 0 else 0
        normalized = (entropy / max_entropy) * 100 if max_entropy > 0 else 0
        
        if protocol_count >= TARGET_DIVERSITY_PROTOCOLS:
            zone = "Human"
            interpretation = f"Excellent protocol diversity: {protocol_count} verified protocols"
            recommendation = "Wallet shows genuine exploratory behavior"
        elif protocol_count >= MIN_DIVERSITY_PROTOCOLS:
            zone = "Grey"
            interpretation = f"Moderate protocol diversity: {protocol_count} verified protocols"
            recommendation = f"Interact with {TARGET_DIVERSITY_PROTOCOLS - protocol_count} more Tier-1 protocols to improve score"
        else:
            zone = "Bot"
            interpretation = f"Low protocol diversity: {protocol_count} verified protocols (need {MIN_DIVERSITY_PROTOCOLS}+)"
            recommendation = "Interact with Uniswap, Aave, ENS, Curve, or other Tier-1 protocols"
        
        return {
            "type": "H_diversity",
            "protocol_count": protocol_count,
            "entropy_bits": round(entropy, 4),
            "max_possible_bits": round(max_entropy, 4),
            "normalized_score": round(normalized, 1),
            "zone": zone,
            "interpretation": interpretation,
            "recommendation": recommendation,
            "target_protocols": TARGET_DIVERSITY_PROTOCOLS,
            "minimum_protocols": MIN_DIVERSITY_PROTOCOLS
        }
    
    def apply_protocol_gate(self, classification: Dict[str, Any], current_score: float) -> float:
        """Apply protocol breadth gate - cap at 40 if <3 protocols"""
        protocol_count = classification.get("tier_1_count", 0)
        
        if protocol_count < MIN_DIVERSITY_PROTOCOLS:
            return min(current_score, 40)
        return current_score
    
    def get_diversity_recommendations(self, protocol_count: int) -> List[str]:
        """Provide specific recommendations to improve diversity score"""
        if protocol_count >= TARGET_DIVERSITY_PROTOCOLS:
            return ["Already meeting target diversity goals"]
        
        missing = TARGET_DIVERSITY_PROTOCOLS - protocol_count
        return [
            f"Add {missing} more Tier-1 protocols to reach target",
            "Try: Uniswap (DEX), Aave (Lending), ENS (Identity)",
            "Also explore: Curve (Stable swaps), Lido (Staking), Maker (CDP)"
        ]