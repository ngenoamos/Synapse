"""Pillar 3: Economic Friction Score (EFS) - Real money spent on-chain"""

import math
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from collections import defaultdict
import requests


class EconomicFrictionEngine:
    """
    Pillar 3: Economic Friction Score
    Measures real money spent on gas fees, bridging, and failed transactions.
    """
    
    # Chain weighting multipliers (prevents L2 cost arbitrage)
    CHAIN_WEIGHTS = {
        "ethereum": 1.0,
        "bsc": 0.5,  # BSC is cheaper
        "polygon": 0.0002,  # Polygon is very cheap
        "arbitrum": 0.1,
        "optimism": 0.1,
        "base": 0.05,
        "avalanche": 0.3,
    }
    
    # Known bridge contract prefixes (simplified detection)
    BRIDGE_CONTRACT_PATTERNS = [
        "0x0",  # Will match specific addresses in real implementation
    ]
    
    def __init__(self):
        self.cache = {}
        self.eth_price_history = {}
            # Decay constant: 0.005 = ~40% loss after 100 days
        self.DECAY_CONSTANT = 0.005
        self.RESET_THRESHOLD_USD = 50.0
        self.SEASONAL_BUFFER_DAYS = 30

    def get_eth_price_at_timestamp(self, timestamp: str) -> float:
        """
        Get ETH price at transaction time.
        For prototype, use current price or hardcoded.
        In production, use Covalent's pricing endpoint.
        """
        # Simplified: use current ETH price
        # In production, query Covalent's /pricing/historical endpoint
        return 3500.0  # $3500 per ETH
    
    def calculate_gas_fee_usd(self, tx: Dict, eth_price_usd: float) -> float:
        """
        Calculate gas fee in USD for a transaction.
        
        Gas fee (USD) = (gas_used * gas_price) / 1e18 * ETH_PRICE
        """
        try:
            gas_used = tx.get("gas_spent", 0)
            gas_price_wei = tx.get("gas_price", 0)
            
            if gas_used and gas_price_wei:
                # Gas fee in ETH
                gas_fee_eth = (gas_used * gas_price_wei) / 1e18
                # Convert to USD
                return gas_fee_eth * eth_price_usd
            return 0.0
        except:
            return 0.0
    
    def detect_bridge_fee(self, tx: Dict) -> float:
        """
        Detect bridging fees from transaction logs.
        Simplified for prototype - checks for bridge contract calls.
        """
        # Simplified: check if transaction involves known bridge addresses
        to_addr = tx.get("to_address", "").lower()
        from_addr = tx.get("from_address", "").lower()
        
        # This is a placeholder - would check against bridge registry in production
        return 0.0
    
    def calculate_days_inactive(self, transactions: List[Dict], current_time: datetime = None) -> int:
        """
        Calculate days since last qualifying transaction.
        
        Qualifying transactions that reset the decay clock:
        - Value > $50 USD equivalent
        - Direct interaction with Tier-1 verified protocol
        """
        from datetime import timezone
        
        if current_time is None:
            current_time = datetime.utcnow().replace(tzinfo=timezone.utc)
        
        if not transactions:
            return 365  # Max days if no transactions
        
        # Get latest transaction timestamp
        latest_tx_time = None
        for tx in transactions:
            block_time = tx.get("block_signed_at")
            if block_time:
                try:
                    # Parse and make timezone-aware
                    tx_time = datetime.fromisoformat(block_time.replace('Z', '+00:00'))
                    if tx_time.tzinfo is None:
                        tx_time = tx_time.replace(tzinfo=timezone.utc)
                    
                    # Check if transaction qualifies to reset clock
                    if self._qualifies_for_reset(tx):
                        if latest_tx_time is None or tx_time > latest_tx_time:
                            latest_tx_time = tx_time
                except:
                    pass
        
        if latest_tx_time is None:
            return 365
        
        days_inactive = (current_time - latest_tx_time).days
        return max(0, days_inactive)

    def _qualifies_for_reset(self, tx: Dict) -> bool:
        """
        Determine if transaction resets the decay clock.
        
        Conditions:
        1. Value > $50 USD equivalent, OR
        2. Direct interaction with Tier-1 verified protocol
        """
        # Check value
        try:
            value_eth = float(tx.get("value", "0")) / 1e18
            eth_price = self.get_eth_price_at_timestamp(tx.get("block_signed_at", ""))
            value_usd = value_eth * eth_price
            
            if value_usd > self.RESET_THRESHOLD_USD:
                return True
        except:
            pass
        
        # Check if interacting with Tier-1 protocol
        to_addr = tx.get("to_address", "").lower()
        from_addr = tx.get("from_address", "").lower()
        
        from .config import ALL_TIER_1_ADDRESSES
        if to_addr in ALL_TIER_1_ADDRESSES or from_addr in ALL_TIER_1_ADDRESSES:
            return True
        
        return False
    
    def get_seasonal_activity_pattern(self, transactions: List[Dict], days_window: int = 90) -> Dict[str, Any]:
        """
        Detect seasonal activity patterns for farmers and cyclical users.
        
        Returns dict with predicted active periods and current season status.
        """
        from datetime import timezone
    
        if not transactions:
            return {"has_seasonal_pattern": False, "currently_in_season": False}
        
        # Group transactions by month
        monthly_counts = defaultdict(int)
        monthly_values = defaultdict(float)
        
        for tx in transactions:
            block_time = tx.get("block_signed_at")
            if block_time:
                try:
                    dt = datetime.fromisoformat(block_time.replace('Z', '+00:00'))
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    month_key = f"{dt.year}-{dt.month:02d}"
                    monthly_counts[month_key] += 1
                    
                    # Get value
                    value_eth = float(tx.get("value", "0")) / 1e18
                    monthly_values[month_key] += value_eth
                except:
                    pass
        
        # Detect pattern: are there regular active months?
        months = sorted(monthly_counts.keys())
        if len(months) < 3:
            return {"has_seasonal_pattern": False, "currently_in_season": False}
        
        # Check if activity is concentrated in specific months (e.g., harvest cycles)
        avg_count = sum(monthly_counts.values()) / len(months)
        std_count = (sum((c - avg_count) ** 2 for c in monthly_counts.values()) / len(months)) ** 0.5
        
        # High standard deviation indicates seasonal concentration
        has_seasonal_pattern = std_count > avg_count
        
        # Check if currently in predicted active season
        current_month = datetime.utcnow().strftime("%Y-%m")
        currently_in_season = monthly_counts.get(current_month, 0) > avg_count * 0.5
        
        return {
            "has_seasonal_pattern": has_seasonal_pattern,
            "currently_in_season": currently_in_season,
            "monthly_avg": round(avg_count, 1),
            "monthly_std": round(std_count, 1),
            "active_months": [m for m, c in monthly_counts.items() if c > avg_count]
        }

    def calculate_time_decay_multiplier(self, days_inactive: int, seasonal_pattern: Dict[str, Any]) -> float:
        """
        Calculate SRS_effective multiplier based on inactivity.
        
        Formula: SRS_effective = SRS_base × e^(-λ × days_inactive)
        Where λ = 0.005
        
        Seasonal exception: decay only triggers if wallet has zero qualifying
        transactions in past 30 days after its predicted seasonal cycle.
        """
        # Seasonal exception: if wallet is expected to be active now
        if seasonal_pattern.get("currently_in_season", False):
            # Check last 30 days for activity
            if days_inactive <= self.SEASONAL_BUFFER_DAYS:
                return 1.0  # No decay during expected active period
        
        # Apply decay formula
        import math
        decay_multiplier = math.exp(-self.DECAY_CONSTANT * days_inactive)
        
        # Cap at reasonable range
        return max(0.05, min(1.0, decay_multiplier))
    
    def get_effective_srs(self, srs_score: float, transactions: List[Dict]) -> Dict[str, Any]:
        """
        Calculate effective SRS with time decay applied.
        
        This is the score used for credit decisions, not the stored base score.
        """
        # Calculate days inactive
        days_inactive = self.calculate_days_inactive(transactions)
        
        # Detect seasonal patterns
        seasonal_pattern = self.get_seasonal_activity_pattern(transactions)
        
        # Calculate decay multiplier
        decay_multiplier = self.calculate_time_decay_multiplier(days_inactive, seasonal_pattern)
        
        # Apply decay
        effective_srs = srs_score * decay_multiplier
        
        # Determine status based on inactivity
        if days_inactive <= 30:
            status = "Active — marginal decay only"
            status_level = "active"
        elif days_inactive <= 60:
            status = "Caution — some drift"
            status_level = "caution"
        elif days_inactive <= 100:
            status = "Warning — approaching threshold"
            status_level = "warning"
        elif days_inactive <= 200:
            status = "Critical — likely below credit eligibility"
            status_level = "critical"
        else:
            status = "Dormant — effectively ineligible"
            status_level = "dormant"
        
        return {
            "base_srs": round(srs_score, 2),
            "effective_srs": round(effective_srs, 2),
            "days_inactive": days_inactive,
            "decay_multiplier": round(decay_multiplier, 4),
            "decay_constant": self.DECAY_CONSTANT,
            "formula": f"SRS_effective = {srs_score:.2f} × e^(-{self.DECAY_CONSTANT} × {days_inactive}) = {effective_srs:.2f}",
            "status": status,
            "status_level": status_level,
            "resets_available": self._get_reset_info(transactions),
            "seasonal_exception_applied": seasonal_pattern["currently_in_season"] and days_inactive <= self.SEASONAL_BUFFER_DAYS
        }

    def _get_reset_info(self, transactions: List[Dict]) -> Dict[str, Any]:
        """Get information about transactions that reset the decay clock."""
        from datetime import timezone
        
        reset_count = 0
        last_reset_time = None
        
        for tx in transactions:
            if self._qualifies_for_reset(tx):
                reset_count += 1
                block_time = tx.get("block_signed_at")
                if block_time:
                    try:
                        tx_time = datetime.fromisoformat(block_time.replace('Z', '+00:00'))
                        if tx_time.tzinfo is None:
                            tx_time = tx_time.replace(tzinfo=timezone.utc)
                        if last_reset_time is None or tx_time > last_reset_time:
                            last_reset_time = tx_time
                    except:
                        pass
        
        return {
            "total_reset_transactions": reset_count,
            "last_reset_date": last_reset_time.isoformat() if last_reset_time else None,
            "reset_threshold_usd": self.RESET_THRESHOLD_USD,
            "explanation": f"Transactions > ${self.RESET_THRESHOLD_USD} or interacting with Tier-1 protocols reset the decay clock"
        }
    
    def is_transaction_successful(self, tx: Dict) -> bool:
        """Check if transaction succeeded (didn't revert)"""
        return tx.get("successful", True)
    
    def calculate_sunk_costs(self, transactions: List[Dict], chain: str = "ethereum") -> Dict[str, Any]:
        """
        Calculate total sunk costs:
        - Gas fees (USD)
        - Bridge fees (USD)
        - Failed transaction penalty (1.5x multiplier)
        """
        total_gas_usd = 0.0
        total_bridge_usd = 0.0
        total_failed_count = 0
        total_successful_count = 0
        
        # Get ETH price (simplified)
        eth_price_usd = self.get_eth_price_at_timestamp(str(datetime.utcnow()))
        
        for tx in transactions:
            # Calculate gas fee
            gas_fee = self.calculate_gas_fee_usd(tx, eth_price_usd)
            
            # Detect bridge fee
            bridge_fee = self.detect_bridge_fee(tx)
            
            # Check if transaction succeeded
            is_success = self.is_transaction_successful(tx)
            
            if is_success:
                total_successful_count += 1
                total_gas_usd += gas_fee
                total_bridge_usd += bridge_fee
            else:
                total_failed_count += 1
                # Failed transactions count 1.5x (human retry signal)
                total_gas_usd += gas_fee * 1.5
                total_bridge_usd += bridge_fee * 1.5
        
        # Apply chain weighting
        chain_weight = self.CHAIN_WEIGHTS.get(chain, 1.0)
        
        weighted_gas = total_gas_usd * chain_weight
        weighted_bridge = total_bridge_usd * chain_weight
        weighted_total = weighted_gas + weighted_bridge
        
        return {
            "total_gas_usd": round(total_gas_usd, 4),
            "total_bridge_usd": round(total_bridge_usd, 4),
            "total_failed_count": total_failed_count,
            "total_successful_count": total_successful_count,
            "chain_weight": chain_weight,
            "weighted_gas_usd": round(weighted_gas, 4),
            "weighted_bridge_usd": round(weighted_bridge, 4),
            "weighted_total_usd": round(weighted_total, 4),
            "failure_rate": round(total_failed_count / (len(transactions) or 1), 4)
        }
    
    def calculate_efs(self, weighted_total_usd: float) -> float:
        """
        Calculate Economic Friction Score (EFS).
        
        Formula: EFS = log₁₀(1 + weighted_sunk_costs)
        
        Returns value between 0 and infinity.
        Normalized later to 0-1 scale.
        """
        if weighted_total_usd <= 0:
            return 0.0
        
        return math.log10(1 + weighted_total_usd)
    
    def normalize_efs(self, efs_raw: float, percentile_95: float = 100.0) -> float:
        """
        Normalize EFS to 0-1 scale against 95th percentile.
        
        Args:
            efs_raw: Raw EFS score from log10 formula
            percentile_95: 95th percentile of sample population (to be calibrated)
        """
        if efs_raw <= 0:
            return 0.0
        
        normalized = min(1.0, efs_raw / percentile_95)
        return round(normalized, 4)
    
    def calculate_complete_efs(self, transactions: List[Dict], chain: str = "ethereum") -> Dict[str, Any]:
        """
        Complete Pillar 3 analysis with EFS score.
        """
        # Calculate sunk costs
        sunk_costs = self.calculate_sunk_costs(transactions, chain)
        
        # Calculate raw EFS
        efs_raw = self.calculate_efs(sunk_costs["weighted_total_usd"])
        
        # Normalize (using placeholder 95th percentile, to be calibrated with real data)
        efs_normalized = self.normalize_efs(efs_raw, percentile_95=50.0)
        
        # Determine tier
        if efs_normalized >= 0.7:
            tier = "High Economic Activity"
            interpretation = "Substantial real money spent on-chain - high trust"
        elif efs_normalized >= 0.3:
            tier = "Medium Economic Activity"
            interpretation = "Moderate on-chain spending - normal user"
        else:
            tier = "Low Economic Activity"
            interpretation = "Minimal spent - possible low-trust or new wallet"
        
        return {
            "pillar_3": {
                "efs_score": round(efs_normalized, 4),
                "raw_efs": round(efs_raw, 4),
                "economic_activity_tier": tier,
                "interpretation": interpretation,
                "breakdown": {
                    "gas_fees_usd": sunk_costs["total_gas_usd"],
                    "bridge_fees_usd": sunk_costs["total_bridge_usd"],
                    "failed_transactions": sunk_costs["total_failed_count"],
                    "successful_transactions": sunk_costs["total_successful_count"],
                    "failure_rate": sunk_costs["failure_rate"],
                    "chain_weight": sunk_costs["chain_weight"],
                    "weighted_total_usd": sunk_costs["weighted_total_usd"]
                },
                "formula": f"EFS = log₁₀(1 + {sunk_costs['weighted_total_usd']:.2f}) = {efs_raw:.4f} → normalized: {efs_normalized:.4f}"
            }
        }
    
    def get_efs_for_wallet(self, wallet_address: str, transactions: List[Dict], chain: str = "ethereum") -> Dict[str, Any]:
        """Get EFS for wallet with caching."""
        cache_key = f"efs_{wallet_address}_{chain}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        result = self.calculate_complete_efs(transactions, chain)
        self.cache[cache_key] = result
        return result
