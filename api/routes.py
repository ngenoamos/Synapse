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