import os
from sqlalchemy import text
from api.persistence.db import get_connection

def inicializar_banco():
    with get_connection() as conn:
        # Verifica se já existem moedas cadastradas
        result = conn.execute(text("SELECT COUNT(*) as total FROM moeda")).mappings().first()
        if result and result["total"] == 0:
            data_sql_path = os.path.join(os.path.dirname(__file__), "../../data.sql")
            with open(data_sql_path, "r") as f:
                sql_script = f.read()
            for statement in sql_script.split(";"):
                stmt = statement.strip()
                if stmt:
                    conn.execute(text(stmt))