# api/routers/carteira_router.py
from fastapi import APIRouter, HTTPException, Depends
from typing import List

from api.services.carteira_service import CarteiraService
from api.persistence.repositories.carteira_repository import CarteiraRepository
from api.models.carteira_models import (
    Carteira, CarteiraCriada, DepositoRequest, SaldoCarteira, 
    SaqueRequest, TransacaoResponse, ConversaoRequest, 
    ConversaoResponse, CotacaoResponse
)


router = APIRouter(prefix="/carteiras", tags=["carteiras"])


def get_carteira_service() -> CarteiraService:
    repo = CarteiraRepository()
    return CarteiraService(repo)


@router.on_event("shutdown")
async def shutdown_event():
    """Fecha o serviço da Coinbase ao desligar o app"""
    service = get_carteira_service()
    await service.close()


@router.post("", response_model=CarteiraCriada, status_code=201)
def criar_carteira(
    service: CarteiraService = Depends(get_carteira_service),
)->CarteiraCriada:
    """
    Cria uma nova carteira. O body é opcional.
    Retorna endereço e chave privada (apenas nesta resposta).
    """
    try:
        return service.criar_carteira()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[Carteira])
def listar_carteiras(service: CarteiraService = Depends(get_carteira_service)):
    return service.listar()


@router.get("/{endereco_carteira}", response_model=Carteira)
def buscar_carteira(
    endereco_carteira: str,
    service: CarteiraService = Depends(get_carteira_service),
):
    try:
        return service.buscar_por_endereco(endereco_carteira)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{endereco_carteira}", response_model=Carteira)
def bloquear_carteira(
    endereco_carteira: str,
    service: CarteiraService = Depends(get_carteira_service),
):
    try:
        return service.bloquear(endereco_carteira)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{endereco_carteira}/depositos", response_model=TransacaoResponse, status_code=201)
def realizar_deposito(
    endereco_carteira: str,
    deposito: DepositoRequest,
    service: CarteiraService = Depends(get_carteira_service),
):
    try:
        return service.realizar_deposito(endereco_carteira, deposito)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{endereco_carteira}/saques", response_model=TransacaoResponse, status_code=201)
def realizar_saque(
    endereco_carteira: str,
    saque: SaqueRequest,
    service: CarteiraService = Depends(get_carteira_service),
):
    try:
        return service.realizar_saque(endereco_carteira, saque)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{endereco_carteira}/saldos", response_model=List[SaldoCarteira])
def obter_saldos(
    endereco_carteira: str,
    service: CarteiraService = Depends(get_carteira_service),
):
    try:
        saldos = service.obter_saldos(endereco_carteira)
        if not saldos:
            raise ValueError("Nenhum saldo encontrado")
        return saldos
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
@router.get("/{endereco_carteira}/saldos/{id_moeda}", response_model=SaldoCarteira)
def obter_saldo(
    endereco_carteira: str,
    id_moeda: int,
    service: CarteiraService = Depends(get_carteira_service),
):
    try:
        saldo = service.obter_saldo(endereco_carteira, id_moeda)
        if not saldo:
            raise ValueError("Saldo não encontrado")
        return saldo
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{endereco_carteira}/conversoes", response_model=ConversaoResponse, status_code=201)
async def realizar_conversao(
    endereco_carteira: str,
    conversao: ConversaoRequest,
    service: CarteiraService = Depends(get_carteira_service),
):
    """
    Realiza conversão de moedas dentro da mesma carteira.
    
    - **id_moeda_origem**: ID da moeda a ser convertida
    - **id_moeda_destino**: ID da moeda de destino
    - **valor_origem**: Valor a ser convertido (deve ser positivo)
    - **hash_chave**: Hash da chave privada para autenticação
    
    Usa a API da Coinbase para obter cotações em tempo real.
    Aplica uma taxa de 0.5% para a conversão.
    """
    try:
        return await service.realizar_conversao(endereco_carteira, conversao)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cotacoes/{moeda_base}/{moeda_alvo}", response_model=CotacaoResponse)
async def obter_cotacao(
    moeda_base: str,
    moeda_alvo: str,
    service: CarteiraService = Depends(get_carteira_service),
):
    """
    Obtém cotação entre duas moedas usando a API da Coinbase.
    
    Exemplos:
    - /cotacoes/BTC/USD (Bitcoin para Dólar)
    - /cotacoes/ETH/BTC (Ethereum para Bitcoin)
    - /cotacoes/USD/BRL (Dólar para Real)
    """
    try:
        return await service.obter_cotacao(moeda_base.upper(), moeda_alvo.upper())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hello-world", response_model=str)
def hello_world():
    return "hello world"