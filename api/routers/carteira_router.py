from fastapi import APIRouter, HTTPException, Depends
from typing import List

from api.services.carteira_service import CarteiraService
from api.persistence.repositories.carteira_repository import CarteiraRepository
from api.models.carteira_models import Carteira, CarteiraCriada, DepositoRequest, SaldoCarteira, SaqueRequest, TransacaoResponse


router = APIRouter(prefix="/carteiras", tags=["carteiras"])


def get_carteira_service() -> CarteiraService:
    repo = CarteiraRepository()
    return CarteiraService(repo)


@router.post("", response_model=CarteiraCriada, status_code=201)
def criar_carteira(
    service: CarteiraService = Depends(get_carteira_service),
)->CarteiraCriada:
    """
    Cria uma nova carteira. O body é opcional .
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

@router.get("/hello-world", response_model=str)
def hello_world():
    return "hello world"