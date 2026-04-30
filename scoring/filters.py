"""Transaction filtering logic - self-transfers, dust, approvals"""

from datetime import datetime
from typing import Dict, Any, List, Tuple
from .config import MIN_USD_VALUE, ETH_PRICE_USD, BNB_PRICE_USD


class TransactionFilter:
    """Filter qualifying transactions for entropy calculation"""
    
    @staticmethod
    def is_self_transfer(tx: Dict, wallet_address: str) -> bool:
        """Check if transaction is a self-transfer"""
        from_addr = (tx.get("from_address") or "").lower()
        to_addr = (tx.get("to_address") or "").lower()
        wallet_lower = wallet_address.lower()
        return from_addr == wallet_lower and to_addr == wallet_lower
    
    @staticmethod
    def get_transaction_value_eth(tx: Dict) -> float:
        """Extract ETH/BNB value from transaction"""
        try:
            value_str = tx.get("value", "0")
            return float(value_str) / 1e18
        except:
            return 0.0
    
    @staticmethod
    def is_dust_transaction(value_eth: float, chain: str = "ethereum") -> bool:
        """Check if transaction value is below dust threshold ($5)"""
        if chain == "ethereum":
            usd_value = value_eth * ETH_PRICE_USD
        else:
            usd_value = value_eth * BNB_PRICE_USD
        return usd_value < MIN_USD_VALUE
    
    @staticmethod
    def is_qualifying(tx: Dict, wallet_address: str, chain: str = "ethereum") -> Tuple[bool, str]:
        """Determine if transaction qualifies for entropy calculation."""
        # Check self-transfer
        if TransactionFilter.is_self_transfer(tx, wallet_address):
            return False, "self_transfer"
        
        # Get value
        value_eth = TransactionFilter.get_transaction_value_eth(tx)
        
        # DEBUG: Print values for first few transactions
        import random
        if random.random() < 0.01:  # Print 1% of transactions
            print(f"DEBUG: value_eth={value_eth}, chain={chain}")
        
        # Check dust (pass chain parameter)
        if TransactionFilter.is_dust_transaction(value_eth, chain):
            return False, "dust"
        
        # Check zero-value
        if value_eth == 0:
            if TransactionFilter.is_token_approval(tx):
                return False, "token_approval"
            return False, "zero_value"
        
        return True, "qualifying"
    
    @staticmethod
    def is_token_approval(tx: Dict) -> bool:
        """Check if transaction is a token approval"""
        # Check method_id for approve() (0x095ea7b3)
        method_id = tx.get("method_id", "")
        if method_id and method_id.lower() == "0x095ea7b3":
            return True
        
        # Check logs for Approval event
        log_events = tx.get("log_events", [])
        for log in log_events:
            decoded = log.get("decoded") or {}
            if decoded.get("name") == "Approval":
                return True
        return False
    
    @staticmethod
    def is_qualifying(tx: Dict, wallet_address: str, chain: str = "ethereum") -> Tuple[bool, str]:
        """
        Determine if transaction qualifies for entropy calculation.
        Returns: (is_qualifying, reason)
        """
        # Check self-transfer
        if TransactionFilter.is_self_transfer(tx, wallet_address):
            return False, "self_transfer"
        
        # Get value
        value_eth = TransactionFilter.get_transaction_value_eth(tx)
        
        # Check dust (pass chain parameter)
        if TransactionFilter.is_dust_transaction(value_eth, chain):
            return False, "dust"
        
        # Check zero-value (which implies dust)
        if value_eth == 0:
            if TransactionFilter.is_token_approval(tx):
                return False, "token_approval"
            return False, "zero_value"
        
        return True, "qualifying"