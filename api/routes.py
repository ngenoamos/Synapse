from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from scoring.engine import SRSEngine

router = APIRouter()
srs_engine = SRSEngine()

@router.get("/scan/{wallet_address}")
async def scan_wallet(wallet_address: str) -> Dict[str, Any]:
    try:
        result = srs_engine.evaluate_wallet(wallet_address)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/score/{wallet_address}")
async def get_score(wallet_address: str) -> Dict[str, Any]:
    try:
        score = srs_engine.get_score(wallet_address)
        return {"wallet": wallet_address, "score": score}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cache/{wallet_address}")
async def cache_wallet_data(wallet_address: str, data: Dict[str, Any]) -> Dict[str, str]:
    srs_engine.cache_data(wallet_address, data)
    return {"status": "cached", "wallet": wallet_address}
