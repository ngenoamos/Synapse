from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List
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
        # Use sync version
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