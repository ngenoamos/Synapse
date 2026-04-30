"""Liveness gate and density verification"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from .config import (
    MIN_QUALIFYING_TXS,
    MIN_TX_PER_WEEK_DENSE,
    SPARSE_DENSITY_MULTIPLIER,
    FULL_DENSITY_MULTIPLIER,
    STANDARD_WINDOW_DAYS
)


def _get_liveness_recommendation(filtered_stats: Dict) -> str:
    """
    Generate actionable recommendation based on filter statistics.
    """
    total_tx = filtered_stats.get("total_transactions", 0)
    dust = filtered_stats.get("dust", 0)
    self_transfer = filtered_stats.get("self_transfer", 0)
    token_approval = filtered_stats.get("token_approval", 0)
    qualifying = filtered_stats.get("qualifying", 0)
    
    # Special case: Smart contract wallet detection
    if qualifying == 0 and total_tx > 100:
        if dust > total_tx * 0.8:
            return "This appears to be a smart contract wallet. SRS scoring requires an externally owned account (EOA) with regular transaction activity. Consider using a different wallet."
        if token_approval > total_tx * 0.5:
            return "Wallet has many token approvals without completed swaps. Complete the swaps or use a wallet with actual transaction activity."
        return f"Wallet has {total_tx} total transactions but NONE qualify. Try a wallet with transactions >$5 value."
    
    if dust > 0 and qualifying == 0:
        return "All transactions are dust (<$5). Send transactions with value >$5 to qualify."
    
    if dust > qualifying * 2:
        return f"Most transactions ({dust}) are dust (<$5). Focus on transactions with meaningful value (>$5)."
    
    if self_transfer > qualifying:
        return f"Too many self-transfers ({self_transfer}). Interact with external contracts instead of self-transfers."
    
    if token_approval > qualifying:
        return f"Many token approvals ({token_approval}) without swaps. Complete the swaps for them to count."
    
    if qualifying < 10:
        return "Very low transaction count. Need at least 50 qualifying transactions (>$5) over 180 days."
    
    return "Increase transaction volume and value. Aim for 50+ transactions >$5 over 180 days."


class LivenessGate:
    """Verify wallet meets minimum activity requirements"""
    
    @staticmethod
    def check_liveness(qualifying_txs: List[Dict], days_analyzed: int, filtered_stats: Dict = None) -> Dict[str, Any]:
        """
        Check if wallet passes liveness gate.
        Returns dict with pass/fail and multiplier.
        
        Args:
            qualifying_txs: List of qualifying transactions
            days_analyzed: Number of days analyzed (180)
            filtered_stats: Optional dict with filter breakdown statistics
        """
        tx_count = len(qualifying_txs)
        
        # Hard gate: minimum 50 transactions
        if tx_count < MIN_QUALIFYING_TXS:
            result = {
                "passed": False,
                "reason": f"Insufficient qualifying transactions: {tx_count} < {MIN_QUALIFYING_TXS}",
                "qualifying_transactions": tx_count,
                "minimum_required": MIN_QUALIFYING_TXS,
                "density_multiplier": 0,
                "srs_score": 0
            }
            
            # Add detailed filter breakdown if provided
            if filtered_stats:
                total_tx = filtered_stats.get("total_transactions", 0)
                dust = filtered_stats.get("dust", 0)
                self_transfer = filtered_stats.get("self_transfer", 0)
                zero_value = filtered_stats.get("zero_value", 0)
                token_approval = filtered_stats.get("token_approval", 0)
                
                # Calculate percentages for better understanding
                dust_pct = (dust / total_tx * 100) if total_tx > 0 else 0
                self_pct = (self_transfer / total_tx * 100) if total_tx > 0 else 0
                approval_pct = (token_approval / total_tx * 100) if total_tx > 0 else 0
                
                # Build explanation
                reasons = []
                if dust > 0:
                    reasons.append(f"{dust} dust transactions (<$5) - {dust_pct:.0f}% of total")
                if self_transfer > 0:
                    reasons.append(f"{self_transfer} self-transfers - {self_pct:.0f}% of total")
                if token_approval > 0:
                    reasons.append(f"{token_approval} token approvals without swaps - {approval_pct:.0f}% of total")
                if zero_value > 0:
                    reasons.append(f"{zero_value} zero-value transactions")
                
                # Provide actionable recommendation
                recommendation = _get_liveness_recommendation(filtered_stats)
                
                result["filter_breakdown"] = {
                    "total_transactions_scanned": total_tx,
                    "self_transfers_removed": self_transfer,
                    "dust_transactions_removed": dust,
                    "zero_value_removed": zero_value,
                    "token_approvals_removed": token_approval,
                    "qualifying_remaining": tx_count,
                    "removal_reasons": reasons,
                    "explanation": f"Out of {total_tx} total transactions, {dust} were dust (<$5), {self_transfer} were self-transfers, {token_approval} were token approvals. Only {tx_count} transactions qualified for entropy calculation."
                }
                result["recommendation"] = recommendation
            
            return result
        
        # Calculate density (transactions per week)
        weeks = days_analyzed / 7
        tx_per_week = tx_count / weeks if weeks > 0 else 0
        
        # Apply density discount for sparse activity
        if tx_per_week < MIN_TX_PER_WEEK_DENSE:
            density_multiplier = SPARSE_DENSITY_MULTIPLIER
            density_status = "sparse"
            density_message = f"Low activity: {tx_per_week:.1f} tx/week → {SPARSE_DENSITY_MULTIPLIER}x multiplier"
        else:
            density_multiplier = FULL_DENSITY_MULTIPLIER
            density_status = "dense"
            density_message = f"Healthy activity: {tx_per_week:.1f} tx/week → full weight"
        
        return {
            "passed": True,
            "qualifying_transactions": tx_count,
            "minimum_required": MIN_QUALIFYING_TXS,
            "days_analyzed": days_analyzed,
            "weeks_analyzed": round(weeks, 1),
            "transactions_per_week": round(tx_per_week, 2),
            "density_status": density_status,
            "density_multiplier": density_multiplier,
            "density_message": density_message
        }
    
    @staticmethod
    def calculate_window(start_date: datetime, end_date: datetime = None) -> int:
        """Calculate number of days in analysis window"""
        if end_date is None:
            end_date = datetime.utcnow()
        return (end_date - start_date).days