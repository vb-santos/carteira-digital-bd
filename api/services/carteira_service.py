# api/services/carteira_service.py
import hashlib
from typing import Any, Dict, List, Optional
from decimal import Decimal

from api.services.cotacao_service import CoinbaseService, get_coinbase_service
from api.persistence.repositories.carteira_repository import CarteiraRepository
from api.models.carteira_models import (
    Carteira, CarteiraCriada, DepositoRequest, SaldoCarteira, 
    SaqueRequest, TransacaoResponse, ConversaoRequest, 
    ConversaoResponse, CotacaoResponse, TransferenciaRequest, TransferenciaResponse
)


class CarteiraService:
    def __init__(self, carteira_repo: CarteiraRepository):
        self.carteira_repo = carteira_repo
        self.coinbase_service = None
        
    async def _get_coinbase_service(self):
        """Inicializa o serviço da Coinbase se necessário"""
        if self.coinbase_service is None:
            self.coinbase_service = await get_coinbase_service()
        return self.coinbase_service

    def criar_carteira(self) -> CarteiraCriada:
        row = self.carteira_repo.criar()
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
    
    async def obter_cotacao(self, moeda_base: str, moeda_alvo: str) -> CotacaoResponse:
        """
        Obtém cotação entre duas moedas usando a API da Coinbase.
        """
        coinbase = await self._get_coinbase_service()
        cotacao = await coinbase.get_exchange_rate(moeda_base, moeda_alvo)
        
        if cotacao is None:
            raise ValueError(f"Não foi possível obter cotação para {moeda_base}/{moeda_alvo}")
        
        from datetime import datetime
        return CotacaoResponse(
            moeda_base=moeda_base,
            moeda_alvo=moeda_alvo,
            cotacao=cotacao,
            timestamp=datetime.utcnow()
        )
    
    async def realizar_conversao(self, endereco_carteira: str, conversao: ConversaoRequest) -> ConversaoResponse:
        """
        Realiza conversão entre moedas usando a API da Coinbase.
        """
        carteira = self.carteira_repo.buscar_por_endereco(endereco_carteira)
        if not carteira or carteira["status"] != "ATIVA":
            raise ValueError("Carteira não encontrada ou bloqueada")
        
        if not self.carteira_repo.validar_chave_privada(endereco_carteira, conversao.hash_chave):
            raise ValueError("Chave privada inválida")
        
        if conversao.id_moeda_origem == conversao.id_moeda_destino:
            raise ValueError("Moeda de origem e destino não podem ser iguais")
        
        if conversao.valor_origem <= 0:
            raise ValueError("Valor de origem deve ser positivo")
        
        codigo_origem = self.carteira_repo.obter_codigo_moeda(conversao.id_moeda_origem)
        codigo_destino = self.carteira_repo.obter_codigo_moeda(conversao.id_moeda_destino)
        
        if not codigo_origem or not codigo_destino:
            raise ValueError("Moeda(s) não encontrada(s)")
        
        coinbase = await self._get_coinbase_service()
        cotacao = await coinbase.get_exchange_rate(codigo_origem, codigo_destino)
        
        if cotacao is None:
            cotacao_inversa = await coinbase.get_exchange_rate(codigo_destino, codigo_origem)
            if cotacao_inversa:
                cotacao = 1 / cotacao_inversa
            else:
                raise ValueError(f"Não foi possível obter cotação para {codigo_origem}/{codigo_destino}")
        
        taxa_percentual = 0.5
        valor_com_taxa = conversao.valor_origem * (1 - taxa_percentual / 100)
        valor_destino = valor_com_taxa * cotacao
        
        resultado = self.carteira_repo.registrar_conversao(
            endereco_carteira=endereco_carteira,
            id_moeda_origem=conversao.id_moeda_origem,
            id_moeda_destino=conversao.id_moeda_destino,
            valor_origem=conversao.valor_origem,
            valor_destino=valor_destino,
            taxa_percentual=taxa_percentual,
            cotacao_utilizada=cotacao
        )
        
        return ConversaoResponse(
            id_conversao=resultado["id_conversao"],
            endereco_carteira=endereco_carteira,
            id_moeda_origem=conversao.id_moeda_origem,
            id_moeda_destino=conversao.id_moeda_destino,
            valor_origem=conversao.valor_origem,
            valor_destino=valor_destino,
            taxa_percentual=taxa_percentual,
            cotacao_utilizada=cotacao,
            data_hora=resultado["data_hora"],
            saldo_origem_final=resultado["saldo_origem_final"],
            saldo_destino_final=resultado["saldo_destino_final"]
        )
    
    def realizar_transferencia(self, endereco_origem: str, transferencia: TransferenciaRequest) -> TransferenciaResponse:
        """
        Realiza transferência entre carteiras.
        """
        # 1. Validações iniciais
        carteira_origem = self.carteira_repo.buscar_por_endereco(endereco_origem)
        if not carteira_origem or carteira_origem["status"] != "ATIVA":
            raise ValueError("Carteira origem não encontrada ou bloqueada")
        
        carteira_destino = self.carteira_repo.buscar_por_endereco(transferencia.endereco_destino)
        if not carteira_destino or carteira_destino["status"] != "ATIVA":
            raise ValueError("Carteira destino não encontrada ou bloqueada")
        
        if transferencia.valor <= 0:
            raise ValueError("Valor da transferência deve ser positivo")
        
        if not self.carteira_repo.validar_chave_privada(endereco_origem, transferencia.hash_chave):
            raise ValueError("Chave privada inválida")
        
        if endereco_origem == transferencia.endereco_destino:
            raise ValueError("Não é possível transferir para a mesma carteira")
        
        # 2. Calcula taxa (exemplo: 1% para transferências, mínimo 0.01)
        taxa_percentual = 1.0  # 1% de taxa
        taxa_valor = max(transferencia.valor * taxa_percentual / 100, 0.01)  # Mínimo 0.01
        
        # 3. Realiza transferência no repository
        try:
            resultado = self.carteira_repo.registrar_transferencia(
                endereco_origem=endereco_origem,
                endereco_destino=transferencia.endereco_destino,
                id_moeda=transferencia.id_moeda,
                valor=transferencia.valor,
                taxa_valor=taxa_valor
            )
            
            return TransferenciaResponse(
                id_transferencia=resultado["id_transferencia"],
                endereco_origem=endereco_origem,
                endereco_destino=transferencia.endereco_destino,
                id_moeda=transferencia.id_moeda,
                valor=transferencia.valor,
                taxa_valor=taxa_valor,
                data_hora=resultado["data_hora"],
                saldo_origem_final=resultado["saldo_origem_final"],
                saldo_destino_final=resultado["saldo_destino_final"]
            )
            
        except ValueError as e:
            raise ValueError(str(e))
        except Exception as e:
            raise Exception(f"Erro na transferência: {str(e)}")
    
    def obter_transferencias(self, endereco_carteira: str) -> List[Dict[str, Any]]:
        """
        Obtém todas as transferências de uma carteira.
        """
        carteira = self.carteira_repo.buscar_por_endereco(endereco_carteira)
        if not carteira:
            raise ValueError("Carteira não encontrada")
        
        return self.carteira_repo.obter_transferencias_por_carteira(endereco_carteira)
    
    def obter_transferencia(self, id_transferencia: int) -> Optional[Dict[str, Any]]:
        """
        Obtém uma transferência específica pelo ID.
        """
        return self.carteira_repo.obter_transferencia_por_id(id_transferencia)
    
    async def close(self):
        """Fecha o serviço da Coinbase"""
        if self.coinbase_service:
            await self.coinbase_service.close()