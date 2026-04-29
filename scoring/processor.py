from typing import List, Dict, Any
from datetime import datetime

class TransactionProcessor:
    """Filters and processes transactions for entropy calculation"""
    
    def filter_qualifying_transactions(self, transactions: List[Dict], address: str) -> List[Dict]:
        """
        Filter out:
        - Self-transfers (to/from same address)
        - Zero-value transactions
        - Token approvals without subsequent swap
        """
        qualified = []
        
        for tx in transactions:
            # Check for self-transfer
            from_addr = tx.get("from_address", "").lower()
            to_addr = tx.get("to_address", "").lower()
            
            if from_addr == address.lower() and to_addr == address.lower():
                continue  # Skip self-transfer
            
            # Check for zero value (convert from wei)
            value = self._parse_value(tx.get("value", "0"))
            if value == 0:
                # Check if it's a token approval
                if self._is_token_approval(tx):
                    continue  # Skip approvals
                continue  # Skip zero value
            
            # Check if token approval without swap (simplified)
            if self._is_token_approval(tx) and not self._has_subsequent_swap(tx, transactions):
                continue
            
            qualified.append(tx)
        
        return qualified
    
    def extract_timestamps(self, transactions: List[Dict]) -> List[int]:
        """
        Extract timestamps (in hours of day, 0-23) from transactions
        For Shannon entropy calculation
        """
        timestamps = []
        
        for tx in transactions:
            block_time = tx.get("block_signed_at")
            if block_time:
                # Parse ISO format time
                dt = datetime.fromisoformat(block_time.replace('Z', '+00:00'))
                hour_of_day = dt.hour  # 0-23
                timestamps.append(hour_of_day)
        
        return timestamps
    
    def _parse_value(self, value_str: str) -> float:
        """Convert wei string to ETH float"""
        try:
            return float(value_str) / 1e18
        except:
            return 0.0
    
    def _is_token_approval(self, tx: Dict) -> bool:
        """Check if transaction is a token approval"""
        # Check logs for approval events
        logs = tx.get("log_events", [])
        for log in logs:
            if log.get("decoded", {}).get("name") == "Approval":
                return True
        return False
    
    def _has_subsequent_swap(self, tx: Dict, all_txs: List[Dict]) -> bool:
        """
        Simplified: Check if approval is followed by a swap within same block
        In production, you'd check method_id or decoded data
        """
        # This is simplified - real implementation would check for swap methods
        tx_hash = tx.get("tx_hash")
        # In a real implementation, check if any transaction after this is a swap
        return False