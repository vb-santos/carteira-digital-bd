import os
import secrets
import hashlib
from typing import Dict, Any, Optional, List

from sqlalchemy import text

from api.models.carteira_models import SaldoCarteira
from api.persistence.db import get_connection


class CarteiraRepository:
    """
    Acesso a dados da carteira usando SQLAlchemy Core + SQL puro.
    """

    def criar(self) -> Dict[str, Any]:
        """
        Gera chave pública, chave privada, salva no banco (apenas hash da privada)
        e retorna os dados da carteira + chave privada em claro.
        """
        # 1) Geração das chaves
        private_key_size:int = int(os.getenv("PRIVATE_KEY_SIZE"))
        public_key_size:int = int(os.getenv("PUBLIC_KEY_SIZE"))
        chave_privada = secrets.token_hex(private_key_size)      # 32 bytes -> 64 hex chars (configurável depois)
        endereco = secrets.token_hex(public_key_size)           # "chave pública" simplificada
        hash_privada = hashlib.sha256(chave_privada.encode()).hexdigest()

        with get_connection() as conn:
            # 2) INSERT
            conn.execute(
                text("""
                    INSERT INTO carteira (endereco_carteira, hash_chave_privada)
                    VALUES (:endereco, :hash_privada)
                """),
                {"endereco": endereco, "hash_privada": hash_privada},
            )

            # 3) SELECT para retornar a carteira criada
            row = conn.execute(
                text("""
                    SELECT endereco_carteira,
                           data_criacao,
                           status,
                           hash_chave_privada
                      FROM carteira
                     WHERE endereco_carteira = :endereco
                """),
                {"endereco": endereco},
            ).mappings().first()

        carteira = dict(row)
        carteira["chave_privada"] = chave_privada
        return carteira

    def buscar_por_endereco(self, endereco_carteira: str) -> Optional[Dict[str, Any]]:
        with get_connection() as conn:
            row = conn.execute(
                text("""
                    SELECT endereco_carteira,
                           data_criacao,
                           status,
                           hash_chave_privada
                      FROM carteira
                     WHERE endereco_carteira = :endereco
                """),
                {"endereco": endereco_carteira},
            ).mappings().first()

        return dict(row) if row else None

    def listar(self) -> List[Dict[str, Any]]:
        with get_connection() as conn:
            rows = conn.execute(
                text("""
                    SELECT endereco_carteira,
                           data_criacao,
                           status,
                           hash_chave_privada
                      FROM carteira
                """)
            ).mappings().all()

        return [dict(r) for r in rows]

    def atualizar_status(self, endereco_carteira: str, status: str) -> Optional[Dict[str, Any]]:
        with get_connection() as conn:
            conn.execute(
                text("""
                    UPDATE carteira
                       SET status = :status
                     WHERE endereco_carteira = :endereco
                """),
                {"status": status, "endereco": endereco_carteira},
            )

            row = conn.execute(
                text("""
                    SELECT endereco_carteira,
                           data_criacao,
                           status,
                           hash_chave_privada
                      FROM carteira
                     WHERE endereco_carteira = :endereco
                """),
                {"endereco": endereco_carteira},
            ).mappings().first()

        return dict(row) if row else None
    
    def validar_chave_privada(self, endereco: str, hash_chave_privada: str) -> bool:
        carteira = self.buscar_por_endereco(endereco)
        if not carteira:
            return False
        
        return hash_chave_privada == carteira['hash_chave_privada']

    def obter_saldo(self, endereco: str, id_moeda: int) -> Optional[SaldoCarteira]:
        #retorna o saldo da carteira para uma moeda específica
        with get_connection() as conn:
            row = conn.execute(
                text("""
                    SELECT endereco_carteira, id_moeda, saldo, data_atualizacao
                    FROM saldo_carteira
                    WHERE endereco_carteira = :endereco_carteira AND id_moeda = :id_moeda
                """),
                {"endereco_carteira": endereco, "id_moeda": id_moeda}
            ).mappings().first()
            
            if row:
                return SaldoCarteira(**dict(row))
            return None
    
    def obter_saldos(self, endereco: str) -> List[SaldoCarteira]:
        #retorna o saldo da carteira para todas as moedas
        with get_connection() as conn:
            rows = conn.execute(
                text("""
                    SELECT endereco_carteira, id_moeda, saldo, data_atualizacao
                    FROM saldo_carteira
                    WHERE endereco_carteira = :endereco_carteira
                """),
                {"endereco_carteira": endereco}
            ).mappings().all()
            
            return [SaldoCarteira(**dict(row)) for row in rows]
    
    def registrar_deposito(self, endereco: str, id_moeda: int, valor: float) -> Dict:
        with get_connection() as conn:
            try:
                result = conn.execute(
                    text("""
                        INSERT INTO deposito_saque 
                        (endereco_carteira, id_moeda, tipo, valor, taxa_valor, data_hora)
                        VALUES (:endereco_carteira, :id_moeda, 'DEPOSITO', :valor, :valor_liquido, CURRENT_TIMESTAMP)
                    """),
                    {
                        "endereco_carteira": endereco,
                        "id_moeda": id_moeda,
                        "valor": valor,
                        "valor_liquido": valor
                    }
                )
                
                id_transacao = result.lastrowid
                
                row = conn.execute(
                    text("""
                        SELECT data_hora 
                        FROM deposito_saque 
                        WHERE id_movimento = :id
                    """),
                    {"id": id_transacao}
                ).mappings().first()

                data_transacao = row["data_hora"]

                conn.execute(
                    text("""
                        INSERT INTO saldo_carteira 
                        (endereco_carteira, id_moeda, saldo, data_atualizacao)
                        VALUES (:endereco_carteira, :id_moeda, :valor, CURRENT_TIMESTAMP)
                        ON DUPLICATE KEY UPDATE 
                            saldo = saldo + :valor,
                            data_atualizacao = CURRENT_TIMESTAMP
                    """),
                    {"endereco_carteira": endereco, "id_moeda": id_moeda, "valor": valor}
                )
                
                row = conn.execute(
                    text("""
                        SELECT saldo FROM saldo_carteira 
                        WHERE endereco_carteira = :endereco_carteira AND id_moeda = :id_moeda
                    """),
                    {"endereco_carteira": endereco, "id_moeda": id_moeda}
                ).mappings().first()
                
                saldo_final = float(row['saldo'])
                        
                return {
                    'id_transacao': id_transacao,
                    'data_hora': data_transacao,
                    'saldo_final': saldo_final
                }
                
            except Exception as e:
                conn.rollback()
                raise e
            
    def registrar_saque(self, endereco: str, id_moeda: int, valor: float) -> Dict:
        taxa_percentual = float(os.getenv("TAXA_SAQUE_PERCENTUAL"))
        taxa_valor = valor * taxa_percentual
        valor_liquido = valor + taxa_valor
        
        with get_connection() as conn:
            try:
                row = conn.execute(
                    text("""
                        SELECT saldo FROM saldo_carteira 
                        WHERE endereco_carteira = :endereco_carteira AND id_moeda = :id_moeda
                    """),
                    {"endereco_carteira": endereco, "id_moeda": id_moeda}
                ).mappings().first()
                
                if not row or float(row['saldo']) < valor_liquido:
                    raise ValueError("Saldo insuficiente para realizar o saque (valor + taxa)")
                
                result = conn.execute(
                    text("""
                        INSERT INTO deposito_saque 
                        (endereco_carteira, id_moeda, tipo, valor, taxa_valor, data_hora)
                        VALUES (:endereco_carteira, :id_moeda, 'SAQUE', :valor, :taxa_valor, CURRENT_TIMESTAMP)
                    """),
                    {
                        "endereco_carteira": endereco,
                        "id_moeda": id_moeda,
                        "valor": valor,
                        "taxa_valor": valor_liquido,
                    }
                )

                id_transacao = result.lastrowid

                row = conn.execute(
                    text("""
                        SELECT data_hora 
                        FROM deposito_saque 
                        WHERE id_movimento = :id
                    """),
                    {"id": id_transacao}
                ).mappings().first()

                data_transacao = row["data_hora"]
                
                conn.execute(
                    text("""
                        UPDATE saldo_carteira 
                        SET saldo = saldo - :taxa_valor,
                            data_atualizacao = CURRENT_TIMESTAMP
                        WHERE endereco_carteira = :endereco_carteira AND id_moeda = :id_moeda
                    """),
                    {"taxa_valor": valor_liquido, "endereco_carteira": endereco, "id_moeda": id_moeda}
                )
                
                row = conn.execute(
                    text("""
                        SELECT saldo FROM saldo_carteira 
                        WHERE endereco_carteira = :endereco_carteira AND id_moeda = :id_moeda
                    """),
                    {"endereco_carteira": endereco, "id_moeda": id_moeda}
                ).mappings().first()
                
                saldo_final = float(row['saldo'])
                                
                return {
                    'id_transacao': id_transacao,
                    'data_hora': data_transacao,
                    'taxa_aplicada': taxa_valor,
                    'saldo_final': saldo_final
                }
                
            except Exception as e:
                conn.rollback()
                raise e