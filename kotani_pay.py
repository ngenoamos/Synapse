# kotani_pay.py
import requests
import os
from typing import Dict, Any

class KotaniPayBridge:
    """
    Kotani Pay integration for KES onboarding (Phase 1: manual)
    """
    
    def __init__(self):
        self.api_key = os.getenv("KOTANI_API_KEY", "")
        self.base_url = "https://api.kotani-pay.com/v1"
        self.enabled = bool(self.api_key)
    
    def convert_to_kes(self, lusd_amount: float) -> float:
        """
        Convert LUSD to KES (Phase 1: manual rate)
        In Phase 2, use Kotani Pay API
        """
        # 1 LUSD ≈ 150 KES (simplified)
        return lusd_amount * 150
    
    def send_to_mpesa(self, phone_number: str, amount_kes: float) -> Dict[str, Any]:
        """
        Send KES to M-Pesa via Kotani Pay
        Phase 1: Manual processing (you handle it)
        Phase 2: API integration
        """
        if not self.enabled:
            return {
                "status": "manual_required",
                "phone": phone_number,
                "amount_kes": amount_kes,
                "message": "Manual conversion required - Kotani Pay API not configured"
            }
        
        # Phase 2: Actual API call
        response = requests.post(
            f"{self.base_url}/mpesa/send",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"phone": phone_number, "amount": amount_kes}
        )
        return response.json()