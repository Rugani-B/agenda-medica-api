"""
Migração: cria tabela logs_auditoria.

Execute uma vez:
  python scripts/migrar_logs_auditoria.py
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text
from app.database.connection import SessionLocal

SQL = text("""
CREATE TABLE IF NOT EXISTS logs_auditoria (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  usuario_id  INT NULL,
  paciente_id INT NULL,
  acao        VARCHAR(20)  NOT NULL,
  recurso     VARCHAR(50)  NOT NULL,
  recurso_id  INT NULL,
  ip          VARCHAR(45)  NULL,
  user_agent  VARCHAR(500) NULL,
  criado_em   DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  detalhes    JSON NULL,
  CONSTRAINT fk_log_usuario  FOREIGN KEY (usuario_id)  REFERENCES usuarios(id)  ON DELETE SET NULL,
  CONSTRAINT fk_log_paciente FOREIGN KEY (paciente_id) REFERENCES pacientes(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
""")

def migrar():
    db = SessionLocal()
    try:
        conn = db.connection()
        print("Criando tabela logs_auditoria...")
        conn.execute(SQL)
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
