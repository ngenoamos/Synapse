"""Liveness gate and density verification"""

from datetime import datetime, timedelta
from typing import Dict, Any, List
from .config import (
    MIN_QUALIFYING_TXS,
    MIN_TX_PER_WEEK_DENSE,
    SPARSE_DENSITY_MULTIPLIER,
    FULL_DENSITY_MULTIPLIER,
    STANDARD_WINDOW_DAYS
)


class LivenessGate:
    """Verify wallet meets minimum activity requirements"""
    
    @staticmethod
    def check_liveness(qualifying_txs: List[Dict], days_analyzed: int) -> Dict[str, Any]:
        """
        Check if wallet passes liveness gate.
        Returns dict with pass/fail and multiplier.
        """
        tx_count = len(qualifying_txs)
        
        # Hard gate: minimum 50 transactions
        if tx_count < MIN_QUALIFYING_TXS:
            return {
                "passed": False,
                "reason": f"Insufficient transactions: {tx_count} < {MIN_QUALIFYING_TXS}",
                "qualifying_transactions": tx_count,
                "minimum_required": MIN_QUALIFYING_TXS,
                "density_multiplier": 0,
                "srs_score": 0
            }
        
        # Calculate density (transactions per week)
        weeks = days_analyzed / 7
        tx_per_week = tx_count / weeks if weeks > 0 else 0
        
        # Apply density discount for sparse activity
        if tx_per_week < MIN_TX_PER_WEEK_DENSE:
            density_multiplier = SPARSE_DENSITY_MULTIPLIER
            density_status = "sparse"
        else:
            density_multiplier = FULL_DENSITY_MULTIPLIER
            density_status = "dense"
        
        return {
            "passed": True,
            "qualifying_transactions": tx_count,
            "minimum_required": MIN_QUALIFYING_TXS,
            "days_analyzed": days_analyzed,
            "weeks_analyzed": round(weeks, 1),
            "transactions_per_week": round(tx_per_week, 2),
            "density_status": density_status,
            "density_multiplier": density_multiplier
        }
    
    @staticmethod
    def calculate_window(start_date: datetime, end_date: datetime = None) -> int:
        """Calculate number of days in analysis window"""
        if end_date is None:
            end_date = datetime.utcnow()
        return (end_date - start_date).days  