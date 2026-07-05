import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.exc import OperationalError

# URL de conexão (padrão placeholder). Preferível definir POSTGRES_URL como variável de ambiente.
# Ex: export POSTGRES_URL="postgresql+psycopg://user:pass@host:5432/dbname"
DATABASE_URL = os.getenv("POSTGRES_URL", "postgresql+psycopg://user:pass@localhost:5432/mydb")

# Engine e Session
engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

# Base declarativa para modelos definidos manualmente
Base = declarative_base()

# Função utilitária para obter sessão (usar com context manager)
def get_session():
    return SessionLocal()

# Testar conexão (raise se falhar)
def test_connection():
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return True
    except OperationalError as e:
        raise RuntimeError(f"DB connection failed: {e}") from e

# Opcional: função para refletir (automap) tabelas existentes no banco
def automap_models():
    """
    Retorna uma automap Base com as classes mapeadas com os nomes das tabelas.
    Uso:
        AutomapBase = automap_models()
        Patient = AutomapBase.classes.pacientes
    """
    md = MetaData()
    md.reflect(bind=engine)
    AutomapBase = automap_base(metadata=md)
    AutomapBase.prepare()
    return AutomapBase

if __name__ == "__main__":
    # Teste rápido
    ok = test_connection()
    print("DB connection OK" if ok else "DB connection FAILED")
