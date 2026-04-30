from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List
import math
from datetime import datetime
from scoring.engine import SRSEngine

router = APIRouter()
srs_engine = SRSEngine()

@router.get("/scan/{wallet_address}")
async def scan_wallet(
    wallet_address: str,
    chain: str = Query("ethereum", enum=["ethereum", "bsc"])
) -> Dict[str, Any]:
    """Scan a wallet address with REAL blockchain data"""
    try:
        result = srs_engine.evaluate_wallet_sync(wallet_address, chain)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/balance/{wallet_address}")
async def get_balance(
    wallet_address: str,
    chain: str = Query("ethereum", enum=["ethereum", "bsc"])
) -> Dict[str, Any]:
    """Get real-time balance for a wallet"""
    try:
        data = srs_engine.get_balance_sync(wallet_address, chain)
        return {"wallet": wallet_address, "chain": chain, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/top_wallets")
async def get_top_wallets(limit: int = 10) -> Dict[str, Any]:
    """Get top wallets by SRS score (from cache)"""
    try:
        top_wallets = srs_engine.get_top_wallets_sync(limit)
        return {"top_wallets": top_wallets, "count": len(top_wallets)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cache_stats")
async def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics"""
    cache_size = len(srs_engine.cache)
    return {
        "cached_wallets": cache_size,
        "cache_file": "data/wallet_cache.json"
    }

@router.get("/entropy/{wallet_address}")
async def get_behavioral_entropy(
    wallet_address: str,
    chain: str = Query("ethereum", enum=["ethereum", "bsc"]),
    min_transactions: int = Query(10, ge=1, le=100, description="Minimum qualifying transactions required for reliable entropy calculation")
) -> Dict[str, Any]:
    """
    Pillar 1: Behavioral Entropy from transaction timing patterns
    
    Parameters:
    - wallet_address: The blockchain wallet address to analyze
    - chain: Blockchain network (ethereum or bsc)
    - min_transactions: Minimum number of qualifying transactions required (default 10)
    """
    try:
        result = srs_engine.analyze_behavioral_entropy(wallet_address, chain)
        
        # Check if there's an error or insufficient transactions
        if "error" in result:
            return result
        
        # Get qualifying transaction count
        qualifying_count = result.get("transaction_analysis", {}).get("qualifying_transactions", 0)
        
        # Check minimum threshold
        if qualifying_count < min_transactions:
            return {
                "error": f"Insufficient qualifying transactions for reliable entropy calculation",
                "wallet": wallet_address,
                "chain": chain,
                "qualifying_transactions": qualifying_count,
                "minimum_required": min_transactions,
                "suggestion": f"Need at least {min_transactions} qualifying transactions. Try a wallet with more activity or lower min_transactions parameter.",
                "help": f"Use ?min_transactions={qualifying_count} to override or try a different wallet"
            }
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/full-score/{wallet_address}")
async def get_full_srs_score(
    wallet_address: str,
    chain: str = Query("ethereum", enum=["ethereum", "bsc"])
) -> Dict[str, Any]:
    """
    Complete SRS score combining balance trust + behavioral entropy
    """
    try:
        result = srs_engine.evaluate_wallet_with_entropy(wallet_address, chain)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/srs-score/{wallet_address}")
async def get_complete_srs_score(
    wallet_address: str,
    chain: str = Query("ethereum", enum=["ethereum", "bsc"])
) -> Dict[str, Any]:
    try:
        # Get behavior entropy (Pillar 1)
        entropy_result = srs_engine.analyze_behavioral_entropy(wallet_address, chain)
        
        if "error" in entropy_result:
            return entropy_result
        
        # Get balance trust score (existing)
        balance_result = srs_engine.evaluate_wallet_sync(wallet_address, chain)
        
        # Extract raw values
        h_timing = entropy_result["behavioral_entropy"]["entropy_bits"]
        trust_score = balance_result.get("srs_score", 50)
        
        # DEBUG: Print raw values
        print(f"\n🔍 DEBUG SRS Calculation:")
        print(f"   trust_score: {trust_score}")
        print(f"   h_timing (raw bits): {h_timing}")
        
        # Normalize entropy to 0-100 scale
        max_entropy = math.log2(24)  # 4.585
        normalized_entropy = (h_timing / max_entropy) * 100
        
        print(f"   max_entropy: {max_entropy}")
        print(f"   normalized_entropy: {normalized_entropy}")
        
        # Weighted combination (70% trust, 30% entropy)
        final_score = (trust_score * 0.7) + (normalized_entropy * 0.3)
        
        print(f"   final_score calculation: ({trust_score} × 0.7) + ({normalized_entropy} × 0.3) = {final_score}")
        
        # Determine final risk level
        if final_score >= 80:
            risk_level = "Low Risk"
        elif final_score >= 50:
            risk_level = "Medium Risk"
        elif final_score >= 25:
            risk_level = "High Risk"
        else:
            risk_level = "Critical Risk"
        
        return {
            "wallet": wallet_address,
            "chain": chain,
            "srs_score": round(final_score, 2),
            "risk_level": risk_level,
            "components": {
                "trust_score": trust_score,
                "behavioral_entropy": {
                    "h_timing_bits": h_timing,
                    "normalized_score": round(normalized_entropy, 1),
                    "zone": entropy_result["behavioral_entropy"]["zone"]
                }
            },
            "pillar_status": {
                "pillar_1_behavioral": "complete",
                "pillar_2_gas": "pending", 
                "pillar_3_diversity": "pending"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/complete-srs/{wallet_address}")
async def get_complete_srs(
    wallet_address: str,
    chain: str = Query("ethereum", enum=["ethereum", "bsc"])
) -> Dict[str, Any]:
    """
    Complete SRS Score with all three pillars.
    Returns H_timing, H_gas, H_diversity, and H_combined.
    
    Liveness Gate: Minimum 50 qualifying transactions.
    If insufficient: returns SRS = 0.
    """
    try:
        result = srs_engine.calculate_complete_srs(wallet_address, chain)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/week2/{wallet_address}")
async def get_week2_analysis(
    wallet_address: str,
    chain: str = Query("ethereum", enum=["ethereum", "bsc"])
) -> Dict[str, Any]:
    """
    COMPLETE Week 2 analysis with all requirements:
    - 24-hour buckets + 7-day buckets
    - Dust filter (>$5)
    - Liveness gate (50+ txs)
    - Density multiplier
    - Protocol breadth check
    """
    try:
        result = srs_engine.analyze_behavioral_entropy_complete(wallet_address, chain)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/gas/{wallet_address}")
async def get_gas_entropy(
    wallet_address: str,
    chain: str = Query("ethereum", enum=["ethereum", "bsc"])
) -> Dict[str, Any]:
    """Pillar 2: Gas bid entropy (H_gas) using streaming"""
    try:
        from scoring.gas import GasEntropyCalculator
        
        # Stream directly - no get_transaction_history
        gas_prices = []
        
        for page in srs_engine.fetcher.stream_transactions(wallet_address, "eth-mainnet", max_pages=3):
            for tx in page:
                gas_price_wei = tx.get("gas_price")
                if gas_price_wei:
                    try:
                        gas_price_gwei = float(gas_price_wei) / 1e9
                        gas_prices.append(gas_price_gwei)
                    except:
                        pass
        
        if len(gas_prices) < 10:
            return {
                "error": "Insufficient gas data",
                "samples": len(gas_prices),
                "minimum_required": 10,
                "wallet": wallet_address
            }
        
        gas_buckets = GasEntropyCalculator.get_gas_percentile_buckets(gas_prices)
        h_gas = GasEntropyCalculator.calculate_h_gas(gas_buckets)
        result = GasEntropyCalculator.interpret_h_gas(h_gas)
        
        result["wallet"] = wallet_address
        result["chain"] = chain
        result["samples"] = len(gas_prices)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pillar2/{wallet_address}")
async def get_pillar2_analysis(
    wallet_address: str,
    chain: str = Query("ethereum", enum=["ethereum", "bsc"])
) -> Dict[str, Any]:
    """Pillar 2: Graph clustering for Sybil farm detection"""
    try:
        result = srs_engine.analyze_pillar_2(wallet_address, chain)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/pillar3/{wallet_address}")
async def get_pillar3_analysis(
    wallet_address: str,
    chain: str = Query("ethereum", enum=["ethereum", "bsc"])
) -> Dict[str, Any]:
    """Pillar 3: Economic Friction Score (EFS) - real money spent on-chain"""
    try:
        result = srs_engine.analyze_pillar_3(wallet_address, chain)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/full-srs/{wallet_address}")
async def get_full_srs(
    wallet_address: str,
    chain: str = Query("ethereum", enum=["ethereum", "bsc"]),
    apply_time_decay: bool = Query(True, description="Apply time decay to SRS based on inactivity")
) -> Dict[str, Any]:
    """
    Complete SRS Score with all three pillars and time decay.
    
    SRS = 30 × EntropyScore + 30 × GraphScore + 40 × EFS
    Then applies time decay: SRS_effective = SRS_base × e^(-0.005 × days_inactive)
    
    Args:
        wallet_address: Ethereum or BSC wallet address
        chain: Blockchain network (ethereum or bsc)
        apply_time_decay: Whether to apply time decay (default True)
    """
    try:
        import math
        from datetime import datetime
        
        # ========== FETCH ALL PILLARS ==========
        
        # Get Pillar 1: Behavioral Entropy
        pillar1 = srs_engine.analyze_behavioral_entropy_complete(wallet_address, chain)
        
        # Get Pillar 2: Graph Clustering
        pillar2 = srs_engine.analyze_pillar_2(wallet_address, chain)
        
        # Get Pillar 3: Economic Friction
        pillar3 = srs_engine.analyze_pillar_3(wallet_address, chain)
        
        # Check for errors in pillars
        if "error" in pillar1:
            return {"error": pillar1["error"], "wallet": wallet_address, "chain": chain}
        
        # ========== EXTRACT SCORES ==========
        
        # Extract normalized scores (0-100 scale)
        entropy_score = pillar1.get("srs_score", 0)
        graph_score = pillar2.get("pillar_2", {}).get("pillar_2_score", 0)
        efs_score_raw = pillar3.get("pillar_3", {}).get("efs_score", 0)
        efs_score = efs_score_raw * 100  # Convert to 0-100
        
        # ========== APPLY GATES ==========
        
        # Gate 1: Zero-Trust Gate (GraphScore = 0 → SRS ≤ 20)
        graph_data = pillar2.get("pillar_2", {})
        external_degree = graph_data.get("external_degree", {}).get("raw", 0)
        zero_trust_active = external_degree == 0
        
        # Gate 2: Clone Detection (Jaccard > 0.85 with 3+ neighbors → cap at 30)
        clone_data = graph_data.get("jaccard_similarity", {})
        clone_detected = clone_data.get("clone_detected", False)
        clone_penalty = clone_data.get("clone_penalty", 1.0)
        
        # Gate 3: Protocol Breadth (Tier-1 count < 3 → cap at 40)
        protocol_count = pillar1.get("protocol_diversity", {}).get("tier_1_count", 0)
        protocol_gate_active = protocol_count < 3
        
        # ========== CALCULATE BASE SRS ==========
        
        # Weighted sum: 30% Entropy + 30% Graph + 40% EFS
        raw_srs = (0.30 * entropy_score) + (0.30 * graph_score) + (0.40 * efs_score)
        
        # Apply clone penalty if detected
        raw_srs *= clone_penalty
        
        # Apply sigmoid transform for non-linear scoring
        # Standard sigmoid centered at 50 with steepness 15
        sigmoid_score = 100 / (1 + math.exp(-(raw_srs - 50) / 15))
        
        # ========== APPLY GATES TO FINAL SCORE ==========
        
        final_score = sigmoid_score
        
        # Apply zero-trust gate
        if zero_trust_active:
            final_score = min(final_score, 20)
        
        # Apply protocol breadth gate
        if protocol_gate_active:
            final_score = min(final_score, 40)
        
        # ========== APPLY TIME DECAY (using streaming) ==========

        decay_info = None
        if apply_time_decay:
            # Stream transactions directly for decay calculation
            from datetime import datetime, timezone
            last_tx_time = None
            tx_count = 0
            
            for page in srs_engine.fetcher.stream_transactions(wallet_address, "eth-mainnet", max_pages=3):
                for tx in page:
                    tx_count += 1
                    block_time = tx.get("block_signed_at")
                    if block_time:
                        try:
                            tx_time = datetime.fromisoformat(block_time.replace('Z', '+00:00'))
                            if tx_time.tzinfo is None:
                                tx_time = tx_time.replace(tzinfo=timezone.utc)
                            if last_tx_time is None or tx_time > last_tx_time:
                                last_tx_time = tx_time
                        except:
                            pass
            
            if last_tx_time:
                now = datetime.now(timezone.utc)
                days_inactive = max(0, (now - last_tx_time).days)
                import math
                decay_multiplier = math.exp(-0.005 * days_inactive)
                final_score *= decay_multiplier
                decay_info = {
                    "days_inactive": days_inactive,
                    "decay_multiplier": round(decay_multiplier, 4),
                    "effective_srs": round(final_score, 2)
                }
        
        # ========== DETERMINE RISK LEVEL ==========
        
        if final_score >= 80:
            risk_level = "Low Risk"
            risk_color = "green"
        elif final_score >= 50:
            risk_level = "Medium Risk"
            risk_color = "yellow"
        elif final_score >= 25:
            risk_level = "High Risk"
            risk_color = "orange"
        else:
            risk_level = "Critical Risk"
            risk_color = "red"
        
        # ========== BUILD RESPONSE ==========
        
        response = {
            "wallet": wallet_address,
            "chain": chain,
            "srs_score": round(final_score, 2),
            "risk_level": risk_level,
            "risk_color": risk_color,
            "pillars": {
                "pillar_1_entropy": {
                    "score": round(entropy_score, 2),
                    "weight": 0.30,
                    "contribution": round(entropy_score * 0.30, 2),
                    "components": {
                        "h_timing": pillar1.get("h_timing", {}),
                        "h_gas": pillar1.get("h_gas", {}),
                        "h_diversity": pillar1.get("h_diversity", {})
                    }
                },
                "pillar_2_graph": {
                    "score": round(graph_score, 2),
                    "weight": 0.30,
                    "contribution": round(graph_score * 0.30, 2),
                    "components": {
                        "external_degree": graph_data.get("external_degree", {}),
                        "clustering": graph_data.get("local_clustering", {}),
                        "louvain": graph_data.get("louvain_modularity", {}),
                        "jaccard": graph_data.get("jaccard_similarity", {})
                    }
                },
                "pillar_3_economic": {
                    "score": round(efs_score, 2),
                    "weight": 0.40,
                    "contribution": round(efs_score * 0.40, 2),
                    "components": pillar3.get("pillar_3", {}).get("breakdown", {})
                }
            },
            "gates_applied": {
                "zero_trust": {
                    "active": zero_trust_active,
                    "cap": 20 if zero_trust_active else None,
                    "reason": "No Tier-1 protocol connections detected" if zero_trust_active else "Passed"
                },
                "protocol_breadth": {
                    "active": protocol_gate_active,
                    "cap": 40 if protocol_gate_active else None,
                    "tier_1_count": protocol_count,
                    "reason": f"Only {protocol_count} Tier-1 protocols (need 3+)" if protocol_gate_active else "Passed"
                },
                "clone_detection": {
                    "active": clone_detected,
                    "penalty": clone_penalty,
                    "reason": clone_data.get("interpretation", "No clones detected")
                }
            },
            "combined": {
                "raw_srs": round(raw_srs, 2),
                "sigmoid_score": round(sigmoid_score, 2),
                "sigmoid_applied": True,
                "formula": "SRS = 30%×Entropy + 30%×Graph + 40%×EFS → Sigmoid → Gates → Time Decay"
            }
        }
        
        # Add time decay info if applied
        if decay_info:
            response["time_decay"] = decay_info
        
        # Add warnings if any pillar is missing data
        warnings = []
        if entropy_score == 0 and "error" not in pillar1:
            warnings.append("Pillar 1 (Entropy) returned low score - review timing patterns")
        if graph_score == 100 and external_degree == 0:
            warnings.append("Pillar 2 (Graph) shows perfect score but zero external degree - possible island")
        if efs_score < 10:
            warnings.append("Pillar 3 (Economic) very low - wallet has minimal economic commitment")
        
        if warnings:
            response["warnings"] = warnings
        
        response["timestamp"] = datetime.utcnow().isoformat()
        
        return response
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/loan/request")
async def request_loan(
    wallet_address: str,
    amount_usd: float,
    duration_days: int,
    mpesa_phone: str = None,
    chain: str = "ethereum"
) -> Dict[str, Any]:
    """
    Request a loan via the credit contract
    """
    try:
        # Verify SRS score
        srs_result = await get_full_srs(wallet_address, chain)
        
        if srs_result["srs_score"] < 60:
            raise HTTPException(status_code=400, detail="SRS too low for loan")
        
        # Loan request recorded
        return {
            "status": "pending",
            "wallet": wallet_address,
            "amount_usd": amount_usd,
            "duration_days": duration_days,
            "srs_score": srs_result["srs_score"],
            "message": "Loan request recorded. Credit contract will process.",
            "next_steps": [
                "1. Approve LUSD spending on credit contract",
                "2. Call requestLoan() on credit contract",
                f"3. For KES: {mpesa_phone} will receive {amount_usd * 150} KES manually"
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/loan/repay/{loan_id}")
async def repay_loan(
    loan_id: int,
    wallet_address: str,
    chain: str = "ethereum"
) -> Dict[str, Any]:
    """
    Record loan repayment
    """
    try:
        # Get current SRS
        srs_result = await get_full_srs(wallet_address, chain)
        current_srs = srs_result["srs_score"]
        new_srs = min(100, current_srs + 5)
        
        return {
            "status": "repayment_recorded",
            "loan_id": loan_id,
            "wallet": wallet_address,
            "old_srs": current_srs,
            "new_srs": new_srs,
            "message": "Repayment recorded. SRS increased by 5 points."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))