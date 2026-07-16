from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, LargeBinary, ForeignKey
from sqlalchemy.sql import func
from app.database.base import Base
import enum
import bcrypt


class PerfilUsuario(enum.Enum):
    admin       = "admin"
    assistente  = "assistente"   # acesso desktop + web, todos os pacientes vinculados
    familiar    = "familiar"     # acesso web apenas, leitura + adesão + confirmação
    medico      = "medico"       # acesso web, vê seus pacientes, cria prescrições e pedidos
    paciente    = "paciente"     # acesso web apenas, leitura + adesão + confirmação (próprio)
    enfermeira  = "enfermeira"   # legado → tratado como assistente
    secretaria  = "secretaria"   # legado → tratado como assistente
    operador    = "operador"     # legado → tratado como assistente


class Usuario(Base):
    __tablename__ = "usuarios"

    id              =   Column(Integer, primary_key=True)
    nome            =   Column(String(100), nullable=False)
    email           =   Column(String(100), unique=True, nullable=False)
    senha_hash      =   Column(LargeBinary, nullable=False)
    perfil          =   Column(Enum(PerfilUsuario), nullable=False)
    ativo           =   Column(Boolean, default=True)
    medico_id       =   Column(Integer, ForeignKey("medicos.id", ondelete="SET NULL"), nullable=True)
    criado_em       =   Column(DateTime(timezone=True), server_default=func.now())


    def verificar_senha(self, senha: str) -> bool:
        return bcrypt.checkpw(senha.encode("utf-8"), self.senha_hash)
    @staticmethod
    def gerar_hash(senha: str) -> bytes:
        return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt())