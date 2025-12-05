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
    chave_privada: str

class SaldoCarteira(BaseModel):
    endereco_carteira: str
    id_moeda: int
    saldo: float
    data_atualizacao: datetime

class ConversaoRequest(BaseModel):
    id_moeda_origem: int
    id_moeda_destino: int
    valor_origem: float
    chave_privada: str
    
class TransferenciaRequest(BaseModel):
    endereco_destino: str
    id_moeda: int
    valor: float
    chave_privada: str

class ConversaoResponse(BaseModel):
    id_conversao: int
    endereco_carteira: str
    id_moeda_origem: int
    id_moeda_destino: int
    valor_origem: float
    valor_destino: float
    taxa_percentual: float
    cotacao_utilizada: float
    data_hora: datetime
    saldo_origem_final: float
    saldo_destino_final: float

class TransacaoResponse(BaseModel):
    id_transacao: int
    tipo: Literal["DEPOSITO", "SAQUE"]
    id_moeda: int
    valor: float
    taxa_aplicada: float
    taxa_valor: float
    data_operacao: datetime
    saldo_final: float

class TransferenciaResponse(BaseModel):
    id_transferencia: int
    endereco_origem: str
    endereco_destino: str
    id_moeda: int
    valor: float
    taxa_valor: float
    data_hora: datetime
    saldo_origem_final: float
    saldo_destino_final: float
    
class CotacaoResponse(BaseModel):
    moeda_base: str
    moeda_alvo: str
    cotacao: float
    timestamp: datetime