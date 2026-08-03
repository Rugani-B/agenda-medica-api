"""
Migração: adiciona coluna 'status' em usuario_paciente.
Vínculos existentes recebem status='ativo' (foram criados antes do sistema de consentimento).

Execute uma vez:
  python scripts/migrar_status_vinculo.py
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text
from app.database.connection import SessionLocal


def migrar():
    db = SessionLocal()
    try:
        conn = db.connection()

        print("Verificando coluna status...")
        result = conn.execute(text(
            "SELECT COUNT(*) FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'usuario_paciente' "
            "AND COLUMN_NAME = 'status'"
        ))
        if result.fetchone()[0]:
            print("  → coluna já existe, ignorando.")
        else:
            conn.execute(text(
                "ALTER TABLE usuario_paciente "
                "ADD COLUMN status VARCHAR(10) NOT NULL DEFAULT 'ativo'"
            ))
            print("  → coluna status adicionada (existentes marcados como 'ativo').")

        db.commit()
        print("Migração concluída com sucesso.")
    except Exception as e:
        db.rollback()
        print(f"Erro: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    migrar()
