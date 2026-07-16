"""
Migração: adicionar perfis 'medico' e 'paciente' ao enum usuarios.perfil
         e coluna medico_id em usuarios.

Execute uma vez:
  python scripts/migrar_perfis_medico_paciente.py
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text
from app.database.connection import SessionLocal

SQL_ENUM = text("""
ALTER TABLE usuarios
  MODIFY COLUMN perfil ENUM(
    'admin','assistente','familiar','medico','paciente',
    'enfermeira','secretaria','operador'
  ) NOT NULL
""")

SQL_CHECK_COL = text(
    "SELECT COUNT(*) FROM information_schema.COLUMNS "
    "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'usuarios' AND COLUMN_NAME = 'medico_id'"
)

SQL_ADD_COL = text("ALTER TABLE usuarios ADD COLUMN medico_id INT NULL")

SQL_ADD_FK = text(
    "ALTER TABLE usuarios ADD CONSTRAINT fk_usuarios_medico "
    "FOREIGN KEY (medico_id) REFERENCES medicos(id) ON DELETE SET NULL"
)


def migrar():
    db = SessionLocal()
    try:
        conn = db.connection()

        print("Alterando ENUM de perfil...")
        conn.execute(SQL_ENUM)

        print("Verificando coluna medico_id...")
        result = conn.execute(SQL_CHECK_COL)
        existe = result.fetchone()[0]
        if not existe:
            conn.execute(SQL_ADD_COL)
            try:
                conn.execute(SQL_ADD_FK)
            except Exception:
                pass  # FK pode já existir ou não ser suportada
            print("  → coluna medico_id adicionada.")
        else:
            print("  → coluna medico_id já existe, ignorando.")

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
