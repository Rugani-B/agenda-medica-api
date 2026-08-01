"""
Migração: cria tabela consentimentos e adiciona colunas nivel/protocolo_origem
em usuario_paciente.

Execute uma vez:
  python scripts/migrar_consentimentos.py
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text
from app.database.connection import SessionLocal

SQLS = [
    # Tabela de consentimentos
    text("""
    CREATE TABLE IF NOT EXISTS consentimentos (
      id                  INT AUTO_INCREMENT PRIMARY KEY,
      protocolo           VARCHAR(50) UNIQUE NOT NULL,
      titular_id          INT NULL,
      versao_termo        VARCHAR(20) NOT NULL,
      hash_termo_sha256   VARCHAR(64) NOT NULL,
      consentimentos_json JSON NOT NULL,
      pessoas_autorizadas JSON NOT NULL,
      assinatura_png_b64  LONGTEXT NULL,
      titular_snapshot    JSON NOT NULL,
      representante_legal JSON NULL,
      registrado_em       DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
      ip                  VARCHAR(45) NOT NULL,
      ip_localizacao      JSON NULL,
      user_agent          VARCHAR(500) NULL,
      evidencias_cliente  JSON NULL,
      revogado_em         DATETIME(6) NULL,
      revogacao_detalhe   JSON NULL,
      CONSTRAINT fk_cons_paciente FOREIGN KEY (titular_id)
        REFERENCES pacientes(id) ON DELETE SET NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """),

    # Coluna nivel em usuario_paciente
    text("""
    ALTER TABLE usuario_paciente
      ADD COLUMN IF NOT EXISTS nivel INT NULL,
      ADD COLUMN IF NOT EXISTS protocolo_origem VARCHAR(50) NULL;
    """),
]

# Fallback para MySQL < 8 que não tem ADD COLUMN IF NOT EXISTS
SQLS_FALLBACK = [
    text("""
    ALTER TABLE usuario_paciente ADD COLUMN nivel INT NULL;
    """),
    text("""
    ALTER TABLE usuario_paciente ADD COLUMN protocolo_origem VARCHAR(50) NULL;
    """),
]


def migrar():
    db = SessionLocal()
    try:
        conn = db.connection()

        print("Criando tabela consentimentos...")
        conn.execute(SQLS[0])

        print("Adicionando colunas em usuario_paciente...")
        try:
            conn.execute(SQLS[1])
        except Exception as e:
            if "IF NOT EXISTS" in str(e).upper() or "syntax" in str(e).lower():
                # MySQL < 8 — tenta coluna por coluna, ignorando duplicate
                for sql in SQLS_FALLBACK:
                    try:
                        conn.execute(sql)
                    except Exception as e2:
                        if "Duplicate column" in str(e2):
                            print(f"  → coluna já existe, ignorando.")
                        else:
                            raise
            elif "Duplicate column" in str(e):
                print("  → colunas já existem, ignorando.")
            else:
                raise

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
