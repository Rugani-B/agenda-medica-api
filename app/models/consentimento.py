from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from app.database.base import Base


class Consentimento(Base):
    __tablename__ = "consentimentos"

    id                    = Column(Integer, primary_key=True, autoincrement=True)
    protocolo             = Column(String(50), unique=True, nullable=False)

    # vínculo com paciente cadastrado (preenchido se CPF bater com algum paciente)
    titular_id            = Column(Integer, ForeignKey("pacientes.id", ondelete="SET NULL"), nullable=True)

    # hash SHA-256 do CPF titular (dígitos apenas) — para lookup sem expor o CPF
    titular_cpf_hash      = Column(String(64), nullable=True, index=True)

    # o que foi aceito
    versao_termo          = Column(String(20), nullable=False)
    hash_termo_sha256     = Column(String(64), nullable=False)
    consentimentos_json   = Column(JSON, nullable=False)          # {dados_comuns, dados_sensiveis, ...}
    pessoas_autorizadas   = Column(JSON, nullable=False)          # [{nome, cpf, vinculo, nivel}, ...]

    # campos sensíveis — armazenados criptografados (Fernet; prefixo "enc1:")
    assinatura_png_b64    = Column(Text, nullable=True)           # data:image/png;base64,...
    titular_snapshot      = Column(Text, nullable=False)          # JSON criptografado
    representante_legal   = Column(Text, nullable=True)           # JSON criptografado (opcional)

    # evidências do servidor
    registrado_em         = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ip                    = Column(String(45), nullable=False)
    ip_localizacao        = Column(JSON, nullable=True)           # {cidade, regiao, pais} — futuro
    user_agent            = Column(String(500), nullable=True)

    # evidências enviadas pelo cliente
    evidencias_cliente    = Column(JSON, nullable=True)

    # ciclo de vida — revogação NÃO apaga o registro
    revogado_em           = Column(DateTime(timezone=True), nullable=True)
    revogacao_detalhe     = Column(JSON, nullable=True)           # {motivo, canal, por_quem}
