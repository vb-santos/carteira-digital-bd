from typing import Literal
from datetime import  datetime
from pydantic import BaseModel


class Carteira(BaseModel):
    endereco_carteira: str
    data_criacao: datetime
    status: Literal["ATIVA","BLOQUEADA"]

class CarteiraCriada(Carteira):
    chave_privada: str

class DepositoRequest(BaseModel):
    id_moeda: int
    valor: float

class SaqueRequest(BaseModel):
    id_moeda: int
    valor: float
    hash_chave: str

class SaldoCarteira(BaseModel):
    endereco_carteira: str
    id_moeda: int
    saldo: float
    data_atualizacao: datetime

class TransacaoResponse(BaseModel):
    id_transacao: int
    tipo: Literal["DEPOSITO", "SAQUE"]
    id_moeda: int
    valor: float
    taxa_aplicada: float
    taxa_valor: float
    data_operacao: datetime
    saldo_final: float