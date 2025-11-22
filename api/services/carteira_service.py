import hashlib
from typing import List

from api.persistence.repositories.carteira_repository import CarteiraRepository
from api.models.carteira_models import Carteira, CarteiraCriada, DepositoRequest, SaldoCarteira, SaqueRequest, TransacaoResponse


class CarteiraService:
    def __init__(self, carteira_repo: CarteiraRepository):
        self.carteira_repo = carteira_repo

    def criar_carteira(self) -> CarteiraCriada:
        row = self.carteira_repo.criar()
        # row tem: endereco_carteira, data_criacao, status, hash_chave_privada, chave_privada
        # não expomos o hash
        return CarteiraCriada(
            endereco_carteira=row["endereco_carteira"],
            data_criacao=row["data_criacao"],
            status=row["status"],
            chave_privada=row["chave_privada"],
        )

    def buscar_por_endereco(self, endereco_carteira: str) -> Carteira:
        row = self.carteira_repo.buscar_por_endereco(endereco_carteira)
        if not row:
            raise ValueError("Carteira não encontrada")

        return Carteira(
            endereco_carteira=row["endereco_carteira"],
            data_criacao=row["data_criacao"],
            status=row["status"],
        )

    def listar(self) -> List[Carteira]:
        rows = self.carteira_repo.listar()
        return [
            Carteira(
                endereco_carteira=r["endereco_carteira"],
                data_criacao=r["data_criacao"],
                status=r["status"],
            )
            for r in rows
        ]

    def bloquear(self, endereco_carteira: str) -> Carteira:
        row = self.carteira_repo.atualizar_status(endereco_carteira, "BLOQUEADA")
        if not row:
            raise ValueError("Carteira não encontrada")

        return Carteira(
            endereco_carteira=row["endereco_carteira"],
            data_criacao=row["data_criacao"],
            status=row["status"],
        )
        
    def realizar_deposito(self, endereco_carteira: str, deposito: DepositoRequest) -> TransacaoResponse:
        carteira = self.carteira_repo.buscar_por_endereco(endereco_carteira)
        if not carteira or carteira["status"] != "ATIVA":
            raise ValueError("Carteira não encontrada ou bloqueada")
        if deposito.valor <= 0:
            raise ValueError("Valor do depósito deve ser positivo")
        result = self.carteira_repo.registrar_deposito(endereco_carteira, deposito.id_moeda, deposito.valor)
        return TransacaoResponse(
            id_transacao=result["id_transacao"],
            tipo="DEPOSITO",
            id_moeda=deposito.id_moeda,
            valor=deposito.valor,
            taxa_aplicada=0.0,
            taxa_valor=deposito.valor,
            data_operacao=result["data_hora"],  
            saldo_final=result["saldo_final"]
        )

    def realizar_saque(self, endereco_carteira: str, saque: SaqueRequest) -> TransacaoResponse:
        carteira = self.carteira_repo.buscar_por_endereco(endereco_carteira)
        if not carteira or carteira["status"] != "ATIVA":
            raise ValueError("Carteira não encontrada ou bloqueada")
        if saque.valor <= 0:
            raise ValueError("Valor do saque deve ser positivo")
        if not self.carteira_repo.validar_chave_privada(endereco_carteira, saque.hash_chave):
            raise ValueError("Chave privada inválida")
        result = self.carteira_repo.registrar_saque(endereco_carteira, saque.id_moeda, saque.valor)
        return TransacaoResponse(
            id_transacao=result["id_transacao"],
            tipo="SAQUE",
            id_moeda=saque.id_moeda,
            valor=saque.valor,
            taxa_aplicada=result["taxa_aplicada"],
            taxa_valor=saque.valor * result["taxa_aplicada"] + saque.valor,
            data_operacao=result["data_hora"], 
            saldo_final=result["saldo_final"]
        )

    def obter_saldos(self, endereco_carteira: str) -> List[SaldoCarteira]:
        carteira = self.carteira_repo.buscar_por_endereco(endereco_carteira)
        if not carteira:
            raise ValueError("Carteira não encontrada")
        return self.carteira_repo.obter_saldos(endereco_carteira)
    
    def obter_saldo(self, endereco_carteira: str, id_moeda: int) -> List[SaldoCarteira]:
        carteira = self.carteira_repo.buscar_por_endereco(endereco_carteira)
        if not carteira:
            raise ValueError("Carteira não encontrada")
        return self.carteira_repo.obter_saldo(endereco_carteira, id_moeda)