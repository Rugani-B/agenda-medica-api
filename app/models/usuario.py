from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, LargeBinary
from sqlalchemy.sql import func
from app.database.base import Base
import enum
import bcrypt


class PerfilUsuario(enum.Enum):
    admin       =   "admin"
    enfermeira  =   "enfermeira"
    secretaria  =   "secretaria"
    operador    =   "operador"


class Usuario(Base):
    __tablename__ = "usuarios"

    id              =   Column(Integer, primary_key=True)
    nome            =   Column(String(100), nullable=False)
    email           =   Column(String(100), unique=True, nullable=False)
    senha_hash      =   Column(LargeBinary, nullable=False)
    perfil          =   Column(Enum(PerfilUsuario), nullable=False)
    ativo           =   Column(Boolean, default=True)
    criado_em       =   Column(DateTime(timezone=True), server_default=func.now())


    def verificar_senha(self, senha: str) -> bool:
        return bcrypt.checkpw(senha.encode("utf-8"), self.senha_hash)
    @staticmethod
    def gerar_hash(senha: str) -> bytes:
        return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt())