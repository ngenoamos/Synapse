import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import requests
from scoring.entropy import EntropyCalculator
from web3 import Web3
import os
import math
import asyncio
from .fetcher import CovalentFetcher
from .config import STANDARD_WINDOW_DAYS, MIN_QUALIFYING_TXS, MIN_USD_VALUE
from .filters import TransactionFilter
from .liveness import LivenessGate
from .diversity import DiversityTracker
from .gas import GasEntropyCalculator
from .graph import GraphClusteringEngine
from .economic import EconomicFrictionEngine

class SRSEngine:
    """Real SRS Engine with blockchain integration"""
    
    def __init__(self):
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        self.cache: Dict[str, Any] = {}
        self._load_cache()

        # Initialize Covalent fetcher
        self.fetcher = CovalentFetcher()
        self.graph_engine = GraphClusteringEngine()
        self.economic_engine = EconomicFrictionEngine()
        
        # Blockchain providers
        self.eth_provider = "https://cloudflare-eth.com"
        self.w3 = Web3(Web3.HTTPProvider(self.eth_provider))
    
    def _load_cache(self):
        cache_file = self.data_dir / "wallet_cache.json"
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                self.cache = json.load(f)
    
    def _save_cache(self):
        cache_file = self.data_dir / "wallet_cache.json"
        with open(cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)
    
    def cache_data(self, wallet_address: str, data: Dict[str, Any]):
        self.cache[wallet_address] = {
            **data,
            "cached_at": datetime.utcnow().isoformat()
        }
        self._save_cache()

    def get_transaction_history(self, wallet_address: str, chain: str = "ethereum") -> Optional[List[Dict]]:
        """
        NEW METHOD: Fetch full transaction history using Covalent
        This is what you were missing!
        """
        # Map chain names to Covalent format
        chain_map = {
            "ethereum": "eth-mainnet",
            "bsc": "bsc-mainnet"
        }
        covalent_chain = chain_map.get(chain, "eth-mainnet")
        
        # Use your fetcher to get transactions
        transactions = self.fetcher.get_transactions_last_180_days(wallet_address, covalent_chain)
        
        if transactions:
            # Cache the transaction history
            cache_key = f"history_{wallet_address}_{chain}"
            self.cache[cache_key] = {
                "transactions": transactions,
                "count": len(transactions),
                "fetched_at": datetime.utcnow().isoformat()
            }
            self._save_cache()
        
        return transactions
    
    def analyze_behavioral_entropy(self, wallet_address: str, chain: str = "ethereum") -> Dict[str, Any]:
        """
        Calculate Shannon entropy from transaction timing with proper filtering.
        Filters out: self-transfers, zero-value transactions, and token approvals.

        Liveness Gate: Minimum 50 qualifying transactions required.
        """
        # Get transaction history
        transactions = self.get_transaction_history(wallet_address, chain)
        
        if not transactions:
            return {
                "error": "No transaction history found",
                "wallet": wallet_address,
                "suggestion": "Try a wallet with more activity",
                "srs_score": 0,
                "liveness_gate": "FAILED"
            }
        
        # Extract hours from timestamps with filtering
        hours = []
        total_sent = 0
        total_received = 0
        qualifying_count = 0
        filtered_self = 0
        filtered_zero = 0
        filtered_approval = 0
        
        wallet_lower = wallet_address.lower()
        
        for tx in transactions:
            # Get addresses safely
            from_addr = tx.get("from_address") or ""
            to_addr = tx.get("to_address") or ""
            
            # Convert to lowercase
            if from_addr:
                from_addr = from_addr.lower()
            if to_addr:
                to_addr = to_addr.lower()
            
            # FILTER 1: Skip self-transfers
            if from_addr == wallet_lower and to_addr == wallet_lower:
                filtered_self += 1
                continue
            
            # Get transaction value
            try:
                value = float(tx.get("value", "0")) / 1e18
            except:
                value = 0
            
            # FILTER 2: Skip zero-value transactions
            if value == 0:
                if self._is_token_approval(tx):
                    filtered_approval += 1
                    continue
                filtered_zero += 1
                continue
            
            # This is a qualifying transaction
            qualifying_count += 1
            
            # Get timestamp for entropy
            block_time = tx.get("block_signed_at")
            if block_time:
                try:
                    dt = datetime.fromisoformat(block_time.replace('Z', '+00:00'))
                    hours.append(dt.hour)
                except:
                    pass
            
            # Track sent/received
            if from_addr == wallet_lower:
                total_sent += value
            if to_addr == wallet_lower:
                total_received += value
        
        # Debug output
        print(f"🔍 Transactions: {len(transactions)} total")
        print(f"   ├─ Self-transfers filtered: {filtered_self}")
        print(f"   ├─ Zero-value filtered: {filtered_zero}")
        print(f"   ├─ Token approvals filtered: {filtered_approval}")
        print(f"   └─ Qualifying: {qualifying_count}")
        
        # LIVENESS GATE: Minimum 50 qualifying transactions (per spec)
        MIN_QUALIFYING_TXS = 50
        
        if qualifying_count < MIN_QUALIFYING_TXS:
            return {
                "error": f"Insufficient qualifying transactions. Liveness gate requires {MIN_QUALIFYING_TXS}+ transactions.",
                "wallet": wallet_address,
                "chain": chain,
                "qualifying_transactions": qualifying_count,
                "minimum_required": MIN_QUALIFYING_TXS,
                "srs_score": 0,
                "liveness_gate": "FAILED",
                "reason": "Wallet does not meet minimum transaction activity threshold",
                "stats": {
                    "total_transactions": len(transactions),
                    "self_transfers": filtered_self,
                    "zero_value": filtered_zero,
                    "token_approvals": filtered_approval,
                    "qualifying": qualifying_count
                }
            }
        
        # Check if we have qualifying transactions
        if not hours:
            return {
                "error": "No qualifying transactions found in the last 180 days",
                "wallet": wallet_address,
                "suggestion": "Try a wallet with more activity",
                "stats": {
                    "total_transactions": len(transactions),
                    "self_transfers": filtered_self,
                    "zero_value": filtered_zero,
                    "token_approvals": filtered_approval,
                    "qualifying": 0
                }
            }
        
        # Calculate H_timing using EntropyCalculator
        from .entropy import EntropyCalculator
        from collections import Counter
        
        h_timing_result = EntropyCalculator.get_h_timing_from_hours(hours)
        hour_counts = Counter(hours)
        
        # Print hour distribution to console
        print("\n📊 Hour Distribution (24 buckets):")
        for hour in range(24):
            count = hour_counts.get(hour, 0)
            if count > 0:
                bar = "█" * min(count, 50)
                print(f"   Hour {hour:2d}: {bar} ({count} transactions)")
        print(f"\n📈 H_timing: {h_timing_result['entropy_bits']} bits ({h_timing_result['zone']} zone)\n")
        
        return {
            "wallet": wallet_address,
            "chain": chain,
            "behavioral_entropy": h_timing_result,
            "transaction_analysis": {
                "total_transactions_analyzed": len(transactions),
                "qualifying_transactions": qualifying_count,
                "filters_applied": {
                    "self_transfers_removed": filtered_self,
                    "zero_value_removed": filtered_zero,
                    "token_approvals_removed": filtered_approval
                },
                "hour_distribution": {
                    str(hour): hour_counts.get(hour, 0) 
                    for hour in range(24)
                },
                "unique_hours": len(set(hours)),
                "total_sent_eth": round(total_sent, 6),
                "total_received_eth": round(total_received, 6),
                "net_flow_eth": round(total_received - total_sent, 6)
            },
            "period_days": 180,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def calculate_complete_srs(
        self, 
        wallet_address: str, 
        chain: str = "ethereum"
    ) -> Dict[str, Any]:
        """
        Complete SRS Score with all three pillars.
        
        Returns H_timing, H_gas, H_diversity, and H_combined.
        
        Liveness Gate: Minimum 50 qualifying transactions required.
        If liveness gate fails, returns SRS = 0.
        """
        MIN_QUALIFYING_TXS = 50
        
        # Step 1: Get behavioral entropy (timing)
        timing_result = self.analyze_behavioral_entropy(wallet_address, chain)
        
        # Check liveness gate
        if timing_result.get("error") and "Insufficient" in timing_result.get("error", ""):
            return {
                "wallet": wallet_address,
                "chain": chain,
                "srs_score": 0,
                "h_timing": 0,
                "h_gas": 0,
                "h_diversity": 0,
                "h_combined": 0,
                "liveness_gate": "FAILED",
                "message": f"Wallet has insufficient activity. Need {MIN_QUALIFYING_TXS}+ qualifying transactions.",
                "qualifying_transactions": timing_result.get("qualifying_transactions", 0)
            }
        
        # Get H_timing (extract from timing_result)
        h_timing = timing_result.get("behavioral_entropy", {}).get("entropy_bits", 0)
        
        # Step 2: Calculate H_gas (Pillar 2)
        from .gas import GasEntropyCalculator
        
        # Get transactions for gas calculation
        transactions = self.get_transaction_history(wallet_address, chain)
        gas_prices = GasEntropyCalculator.extract_gas_prices(transactions) if transactions else []
        
        if len(gas_prices) >= 10:
            gas_buckets = GasEntropyCalculator.get_gas_percentile_buckets(gas_prices)
            h_gas = GasEntropyCalculator.calculate_h_gas(gas_buckets)
        else:
            h_gas = 0.0
        
        # Step 3: Calculate H_diversity (Pillar 3 - placeholder)
        h_diversity = self._calculate_diversity_entropy(wallet_address, chain) if hasattr(self, '_calculate_diversity_entropy') else 0
        
        # Step 4: Calculate combined score
        weights = {
            "timing": 0.35,
            "gas": 0.30,
            "diversity": 0.35
        }
        
        h_combined = (
            weights["timing"] * h_timing +
            weights["gas"] * h_gas +
            weights["diversity"] * h_diversity
        )
        
        # Normalize H_combined to 0-100 scale for SRS score
        max_entropy = math.log2(24)  # ~4.585 bits
        srs_score = (h_combined / max_entropy) * 100 if h_combined > 0 else 0
        srs_score = min(100, max(0, srs_score))
        
        return {
            "wallet": wallet_address,
            "chain": chain,
            "srs_score": round(srs_score, 2),
            "h_timing": round(h_timing, 4),
            "h_gas": round(h_gas, 4),
            "h_diversity": round(h_diversity, 4),
            "h_combined": round(h_combined, 4),
            "weights": weights,
            "liveness_gate": "PASSED",
            "qualifying_transactions": timing_result.get("transaction_analysis", {}).get("qualifying_transactions", 0),
            "pillar_status": {
                "pillar_1_timing": "complete",
                "pillar_2_gas": "in_progress",
                "pillar_3_diversity": "pending_implementation"
            }
        }

    # Placeholder methods for Pillars 2 and 3
    def _calculate_gas_entropy(self, wallet_address: str, chain: str = "ethereum") -> float:
        """Pillar 2: Gas entropy - to be implemented in Week 3"""
        # TODO: Implement gas percentile entropy
        return 0.0

    def _calculate_diversity_entropy(self, wallet_address: str, chain: str = "ethereum") -> float:
        """Pillar 3: Protocol diversity entropy - to be implemented in Week 3"""
        # TODO: Implement protocol diversity entropy
        return 0.0
    
    def _is_token_approval(self, tx: Dict) -> bool:
        """
        Check if a transaction is a token approval (ERC-20 approve method)
        """
        # Check method_id for approve() function (0x095ea7b3)
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
    
    def evaluate_wallet_with_entropy(self, wallet_address: str, chain: str = "ethereum") -> Dict[str, Any]:
        """
        NEW METHOD: Combine existing score with behavioral entropy
        This gives a more complete SRS score
        """
        # Get basic wallet data (your existing method)
        basic_data = self.evaluate_wallet_sync(wallet_address, chain)
        
        if "error" in basic_data:
            return basic_data
        
        # Get behavioral entropy
        entropy_data = self.analyze_behavioral_entropy(wallet_address, chain)
        
        if "error" in entropy_data:
            # Fall back to basic score only
            return basic_data
        
        # Combine scores (70% basic + 30% entropy)
        basic_score = basic_data.get("srs_score", 50)
        entropy_score = entropy_data["behavioral_entropy"]["normalized_score"]
        
        combined_score = (basic_score * 0.7) + (entropy_score * 0.3)
        
        return {
            "wallet": wallet_address,
            "chain": chain,
            "srs_score": round(combined_score, 2),
            "risk_level": self._determine_risk_level(combined_score),
            "components": {
                "balance_trust_score": basic_score,
                "behavioral_entropy_score": round(entropy_score, 2),
                "weighting": "70% / 30%"
            },
            "behavioral_analysis": entropy_data,
            "basic_wallet_data": basic_data.get("wallet_data"),
            "timestamp": datetime.utcnow().isoformat()
        }

    
    def get_real_wallet_data_sync(self, wallet_address: str, chain: str = "ethereum") -> Dict[str, Any]:
        """Synchronous version to fetch real wallet data"""
        
        # Check cache first
        if wallet_address in self.cache:
            return self.cache[wallet_address]
        
        try:
            if chain == "ethereum":
                return self._get_ethereum_data_sync(wallet_address)
            elif chain == "bsc":
                return self._get_bsc_data_sync(wallet_address)
            else:
                return {"error": f"Chain {chain} not fully implemented yet", "address": wallet_address}
        except Exception as e:
            return {"error": str(e), "address": wallet_address}
    
    def _get_ethereum_data_sync(self, address: str) -> Dict[str, Any]:
        """Fetch real Ethereum wallet data with multiple RPC endpoints"""
    
        try:
            # Fix address checksum
            from web3 import Web3
            
            # Try to normalize address
            try:
                # Convert to checksum address if valid
                if Web3.is_address(address):
                    address = Web3.to_checksum_address(address)
                else:
                    return {"error": f"Invalid Ethereum address format: {address}", "address": address}
            except:
                return {"error": f"Cannot validate address: {address}", "address": address}
            
            # Try multiple RPC endpoints
            rpc_endpoints = [
                "https://eth.llamarpc.com",
                "https://rpc.ankr.com/eth",
                "https://ethereum.publicnode.com",
                "https://cloudflare-eth.com"
            ]
            
            balance_eth = 0
            tx_count = 0
            is_contract = False
            working_rpc = None
            
            for rpc_url in rpc_endpoints:
                try:
                    w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 5}))
                    if w3.is_connected():
                        # Get ETH balance
                        balance_wei = w3.eth.get_balance(address)
                        balance_eth = float(w3.from_wei(balance_wei, 'ether'))
                        
                        # Get transaction count
                        tx_count = w3.eth.get_transaction_count(address)
                        
                        # Check if it's a contract
                        is_contract = len(w3.eth.get_code(address)) > 0
                        
                        working_rpc = rpc_url
                        break  # Success with this RPC
                except:
                    continue  # Try next RPC
            
            if working_rpc is None:
                return {"error": "All Ethereum RPC endpoints failed", "address": address}
            
            wallet_data = {
                "address": address,
                "chain": "ethereum",
                "balance_eth": round(balance_eth, 6),
                "balance_usd": round(balance_eth * 3500, 2),
                "transaction_count": tx_count,
                "is_contract": is_contract,
                "trust_score": self._calculate_trust_score(balance_eth, tx_count),
                "timestamp": datetime.utcnow().isoformat(),
                "rpc_used": working_rpc
            }
            
            # Cache the data
            self.cache_data(address, wallet_data)
            return wallet_data
            
        except Exception as e:
            return {"error": f"Failed to fetch Ethereum data: {str(e)}", "address": address}
    
    def _get_bsc_data_sync(self, address: str) -> Dict[str, Any]:
        """Fetch BSC wallet data"""
        try:
            bsc_provider = "https://bsc-dataseed.binance.org/"
            w3_bsc = Web3(Web3.HTTPProvider(bsc_provider))
            
            balance_wei = w3_bsc.eth.get_balance(address)
            balance_bnb = float(w3_bsc.from_wei(balance_wei, 'ether'))
            
            wallet_data = {
                "address": address,
                "chain": "bsc",
                "balance_bnb": round(balance_bnb, 6),
                "balance_usd": round(balance_bnb * 300, 2),
                "trust_score": self._calculate_trust_score(balance_bnb, 0),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.cache_data(address, wallet_data)
            return wallet_data
            
        except Exception as e:
            return {"error": f"Failed to fetch BSC data: {str(e)}", "address": address}
    
    def analyze_behavioral_entropy_complete(self, wallet_address: str, chain: str = "ethereum") -> Dict[str, Any]:
        """
        COMPLETE Week 2 + Week 3 implementation with:
        - 24-hour buckets + 7-day buckets (H_timing)
        - Gas bid entropy (H_gas)
        - Dust filter (>$5)
        - Liveness gate (50+ txs)
        - Density multiplier (0.7x for sparse)
        - Protocol breadth check
        - Risk level determination
        """
        from collections import Counter
        from datetime import datetime
        
        # Fetch transactions
        transactions = self.get_transaction_history(wallet_address, chain)
        
        if not transactions:
            return {"error": "No transaction history found", "wallet": wallet_address}
        
        # Process transactions with enhanced filters
        qualifying_txs = []
        hours = []
        days = []
        counterparties = set()
        gas_prices = []  # For H_gas
        filtered_stats = {"self_transfer": 0, "dust": 0, "zero_value": 0, "token_approval": 0}
        
        wallet_lower = wallet_address.lower()
        
        for tx in transactions:
            is_qualifying, reason = TransactionFilter.is_qualifying(tx, wallet_address, chain)
            
            if not is_qualifying:
                if reason in filtered_stats:
                    filtered_stats[reason] += 1
                continue
            
            qualifying_txs.append(tx)
            
            # Extract timestamp info for H_timing
            block_time = tx.get("block_signed_at")
            if block_time:
                try:
                    dt = datetime.fromisoformat(block_time.replace('Z', '+00:00'))
                    hours.append(dt.hour)
                    days.append(dt.weekday())
                except:
                    pass
            
            # Extract gas price for H_gas
            gas_price_wei = tx.get("gas_price")
            if gas_price_wei:
                try:
                    gas_price_gwei = float(gas_price_wei) / 1e9
                    gas_prices.append(gas_price_gwei)
                except:
                    pass
            
            # Extract counterparty for diversity
            from_addr = (tx.get("from_address") or "").lower()
            to_addr = (tx.get("to_address") or "").lower()
            
            if from_addr == wallet_lower and to_addr:
                counterparties.add(to_addr)
            elif to_addr == wallet_lower and from_addr:
                counterparties.add(from_addr)
        
        # LIVENESS GATE (HARD - returns error if fails)
        liveness = LivenessGate.check_liveness(qualifying_txs, STANDARD_WINDOW_DAYS)
        if not liveness["passed"]:
            return {
                "error": liveness["reason"],
                "wallet": wallet_address,
                "chain": chain,
                "srs_score": 0,
                "liveness_gate": "FAILED",
                "liveness": liveness,
                "filters_applied": filtered_stats
            }
        
        if not hours:
            return {"error": "No valid timestamps found", "wallet": wallet_address}
        
        # ========== PILLAR 1: H_timing ==========
        h_timing_result = EntropyCalculator.get_h_timing_with_days(hours, days)
        h_timing_value = h_timing_result["entropy_bits"]
        
        # ========== PILLAR 2: H_gas ==========
        if len(gas_prices) >= 10:
            gas_buckets = GasEntropyCalculator.get_gas_percentile_buckets(gas_prices)
            h_gas_value = GasEntropyCalculator.calculate_h_gas(gas_buckets)
            h_gas_result = GasEntropyCalculator.interpret_h_gas(h_gas_value)
        else:
            h_gas_value = 0.0
            h_gas_result = {
                "type": "H_gas",
                "entropy_bits": 0,
                "normalized_score": 0,
                "zone": "Insufficient Data",
                "interpretation": f"Only {len(gas_prices)} gas samples (need 10+)",
                "samples": len(gas_prices)
            }
        
        # ========== PILLAR 3: H_diversity ==========
        diversity_tracker = DiversityTracker()
        counterparty_data = diversity_tracker.classify_counterparties(counterparties)
        h_diversity_value = diversity_tracker.calculate_h_diversity(counterparty_data)
        diversity_interpretation = diversity_tracker.interpret_h_diversity(counterparty_data["tier_1_count"])
        
        # ========== COMBINED SCORE ==========
        weights = {"timing": 0.35, "gas": 0.30, "diversity": 0.35}
        
        h_combined = (
            weights["timing"] * h_timing_value +
            weights["gas"] * h_gas_value +
            weights["diversity"] * h_diversity_value
        )
        
        # Normalize to 0-100 scale
        max_possible = math.log2(24)  # ~4.585 bits
        srs_score = (h_combined / max_possible) * 100 if h_combined > 0 else 0
        srs_score = min(100, max(0, srs_score))
        
        # Apply protocol breadth gate
        srs_score = diversity_tracker.apply_protocol_gate(counterparty_data, srs_score)
        
        # Apply density multiplier
        srs_score *= liveness["density_multiplier"]
        
        # Determine risk level
        if srs_score >= 80:
            risk_level = "Low Risk"
        elif srs_score >= 50:
            risk_level = "Medium Risk"
        elif srs_score >= 25:
            risk_level = "High Risk"
        else:
            risk_level = "Critical Risk"
        
        # Print debug output
        print(f"\n🔍 Complete SRS Analysis for {wallet_address[:10]}...")
        print(f"   ├─ Qualifying transactions: {liveness['qualifying_transactions']}")
        print(f"   ├─ H_timing: {h_timing_value:.4f} bits ({h_timing_result['zone']})")
        print(f"   ├─ H_gas: {h_gas_value:.4f} bits ({h_gas_result.get('zone', 'N/A')})")
        print(f"   ├─ H_diversity: {h_diversity_value:.4f} bits")
        print(f"   ├─ External degree: {counterparty_data['external_degree']}")
        print(f"   ├─ Density multiplier: {liveness['density_multiplier']}x")
        print(f"   └─ Final SRS score: {srs_score:.1f} ({risk_level})")
        
        return {
            "wallet": wallet_address,
            "chain": chain,
            "srs_score": round(srs_score, 2),
            "risk_level": risk_level,
            "h_timing": h_timing_result,
            "h_gas": h_gas_result,
            "h_diversity": diversity_tracker.interpret_h_diversity(counterparty_data["tier_1_count"]),  # ← REPLACE with this
            "combined": {
                "h_combined": round(h_combined, 4),
                "weights": weights,
                "max_possible_bits": round(max_possible, 4),
                "formula": f"0.35×{round(h_timing_value,4)} + 0.30×{round(h_gas_value,4)} + 0.35×{round(h_diversity_value,4)} = {round(h_combined,4)} bits"
            },
            "liveness": liveness,
            "filters_applied": filtered_stats,
            "period_days": STANDARD_WINDOW_DAYS,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _calculate_trust_score(self, balance: float, tx_count: int) -> float:
        """Calculate trust score based on real metrics"""
        score = 50  # Base score
        
        # Balance contributes up to 30 points
        if balance > 100:
            score += 30
        elif balance > 10:
            score += 20
        elif balance > 1:
            score += 10
        elif balance > 0.1:
            score += 5
        
        # Transaction count contributes up to 20 points
        if tx_count > 1000:
            score += 20
        elif tx_count > 100:
            score += 15
        elif tx_count > 10:
            score += 10
        elif tx_count > 0:
            score += 5
        
        return min(100, max(0, score))
    
    def evaluate_wallet_sync(self, wallet_address: str, chain: str = "ethereum") -> Dict[str, Any]:
        """Evaluate wallet with real blockchain data (synchronous)"""
        real_data = self.get_real_wallet_data_sync(wallet_address, chain)
        
        if "error" in real_data:
            return real_data
        
        # Calculate SRS score based on real metrics
        trust_score = real_data.get("trust_score", 50)
        balance = real_data.get("balance_eth", 0)
        
        # Adjust score based on balance
        final_score = trust_score
        if balance > 100:
            final_score += 5
        elif balance > 50:
            final_score += 2
        
        # Penalty for contracts
        if real_data.get("is_contract", False):
            final_score -= 15
        
        final_score = max(0, min(100, final_score))
        
        return {
            "wallet": wallet_address,
            "chain": chain,
            "srs_score": round(final_score, 2),
            "risk_level": self._determine_risk_level(final_score),
            "wallet_data": real_data,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_balance_sync(self, wallet_address: str, chain: str = "ethereum") -> Dict[str, Any]:
        """Get balance for a wallet"""
        return self.get_real_wallet_data_sync(wallet_address, chain)
    
    def get_top_wallets_sync(self, limit: int = 10) -> list:
        """Get top wallets by trust score"""
        scored_wallets = []
        
        for address, data in self.cache.items():
            if isinstance(data, dict) and "trust_score" in data:
                scored_wallets.append({
                    "address": address,
                    "score": data.get("trust_score", 0),
                    "balance": data.get("balance_eth", data.get("balance_bnb", 0)),
                    "chain": data.get("chain", "unknown")
                })
        
        scored_wallets.sort(key=lambda x: x["score"], reverse=True)
        return scored_wallets[:limit]
    
    def analyze_pillar_2(self, wallet_address: str, chain: str = "ethereum") -> Dict[str, Any]:
        """Complete Pillar 2 analysis for Sybil farm detection"""
        
        # Get transactions
        transactions = self.get_transaction_history(wallet_address, chain)
        
        if not transactions:
            return {"error": "No transaction history found", "wallet": wallet_address}
        
        # Extract counterparties
        counterparties = set()
        wallet_lower = wallet_address.lower()
        
        for tx in transactions:
            from_addr = (tx.get("from_address") or "").lower()
            to_addr = (tx.get("to_address") or "").lower()
            
            if from_addr == wallet_lower and to_addr:
                counterparties.add(to_addr)
            elif to_addr == wallet_lower and from_addr:
                counterparties.add(from_addr)
        
        # Run Pillar 2 analysis
        result = self.graph_engine.analyze_pillar_2(wallet_address, transactions, counterparties)
        
        return result
    
    def check_continuity_violation(self, wallet_address: str, historical_data: Dict, current_data: Dict) -> Dict[str, Any]:
        """
        Check if wallet behavior has shifted significantly (potential key sale).
        
        Returns:
            - tier: 0 (no violation), 1 (minor), 2 (major), 3 (burn)
            - penalty: SRS reduction amount
            - recovery_days: days needed for rehabilitation
        """
        violations = []
        
        # Check entropy shift (H_timing)
        historical_entropy = historical_data.get("h_timing", {}).get("entropy_bits", 0)
        current_entropy = current_data.get("h_timing", {}).get("entropy_bits", 0)
        entropy_drop = historical_entropy - current_entropy
        
        if entropy_drop > 1.5:
            violations.append(f"Entropy dropped {entropy_drop:.2f} bits")
        
        # Check protocol shift (Jaccard)
        historical_protocols = set(historical_data.get("protocol_diversity", {}).get("matched_protocols", []))
        current_protocols = set(current_data.get("protocol_diversity", {}).get("matched_protocols", []))
        
        if historical_protocols and current_protocols:
            jaccard = len(historical_protocols & current_protocols) / len(historical_protocols | current_protocols)
            if jaccard < 0.3:
                violations.append(f"Protocol shift detected (Jaccard: {jaccard:.2f})")
        
        # Check gas pattern shift
        historical_gas = historical_data.get("h_gas", {}).get("entropy_bits", 0)
        current_gas = current_data.get("h_gas", {}).get("entropy_bits", 0)
        
        # Determine tier
        if len(violations) == 0:
            return {"tier": 0, "penalty": 0, "recovery_days": 0, "violations": []}
        elif entropy_drop > 0.5 or len(violations) >= 1:
            return {
                "tier": 1,
                "penalty": 15,
                "recovery_days": 7,
                "violations": violations,
                "action": "Suspension: -15 SRS, credit frozen 7 days"
            }
        elif entropy_drop > 1.0 or len(violations) >= 2:
            return {
                "tier": 2,
                "penalty": 40,
                "recovery_days": 30,
                "violations": violations,
                "action": "Slashing: -40 SRS, SBT marked Tainted. Recovery: +5 SRS per 30 clean days"
            }
        else:
            return {
                "tier": 3,
                "penalty": 999,
                "recovery_days": -1,
                "violations": violations,
                "action": "Burn: SRS = 0, SBT permanently revoked. Address blacklisted."
            }

    def analyze_pillar_3(self, wallet_address: str, chain: str = "ethereum") -> Dict[str, Any]:
        """Pillar 3: Economic Friction Score (EFS)"""
        transactions = self.get_transaction_history(wallet_address, chain)
        
        if not transactions:
            return {"error": "No transaction history found", "wallet": wallet_address}
        
        return self.economic_engine.get_efs_for_wallet(wallet_address, transactions, chain)

    def _determine_risk_level(self, score: float) -> str:
        if score >= 80:
            return "Low Risk"
        elif score >= 50:
            return "Medium Risk"
        elif score >= 25:
            return "High Risk"
        else:
            return "Critical Risk"
        
    def get_token_holdings(self, address):
        # Use Moralis or Alchemy API
        pass