# api/services/coinbase_service.py
import httpx
import asyncio
from typing import Dict, Optional
import logging
from datetime import datetime
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class CoinbaseService:
    BASE_URL = "https://api.coinbase.com/v2"
    
    def __init__(self):
        self.client = None
        
    async def initialize(self):
        """Inicializa o cliente HTTP assíncrono"""
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def get_exchange_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        """
        Obtém a taxa de câmbio da Coinbase.
        Exemplo: BTC para USD
        """
        if not self.client:
            await self.initialize()
            
        try:
            url = f"{self.BASE_URL}/exchange-rates"
            params = {"currency": from_currency}
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            rates = data.get("data", {}).get("rates", {})
            
            rate = rates.get(to_currency)
            if rate:
                return float(rate)
            
            return None
            
        except httpx.HTTPError as e:
            logger.error(f"Erro HTTP ao buscar taxa de câmbio {from_currency}/{to_currency}: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro inesperado ao buscar taxa de câmbio: {e}")
            return None
    
    async def convert_currency(self, from_currency: str, to_currency: str, amount: float) -> Optional[Dict]:
        """
        Converte um valor de uma moeda para outra usando as taxas da Coinbase.
        """
        try:
            rate = await self.get_exchange_rate(from_currency, to_currency)
            if rate is None:
                return None
            
            converted_amount = amount * rate
            
            return {
                "from_currency": from_currency,
                "to_currency": to_currency,
                "amount": amount,
                "converted_amount": converted_amount,
                "exchange_rate": rate,
                "timestamp": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Erro na conversão: {e}")
            return None
    
    async def close(self):
        """Fecha o cliente HTTP"""
        if self.client:
            await self.client.aclose()


_coinbase_service = None

async def get_coinbase_service() -> CoinbaseService:
    """Obtém uma instância do serviço Coinbase (singleton)"""
    global _coinbase_service
    if _coinbase_service is None:
        _coinbase_service = CoinbaseService()
        await _coinbase_service.initialize()
    return _coinbase_service