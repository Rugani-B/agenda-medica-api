from sqlalchemy.orm import Session
from app.models.log_auditoria import LogAuditoria


def registrar_log(
    db: Session,
    acao: str,
    recurso: str,
    usuario_id: int | None = None,
    paciente_id: int | None = None,
    recurso_id: int | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
    detalhes: dict | None = None,
) -> None:
    """Grava uma linha de auditoria. Nunca lança exceção — falha silenciosa."""
    try:
        db.add(LogAuditoria(
            usuario_id  = usuario_id,
            paciente_id = paciente_id,
            acao        = acao,
            recurso     = recurso,
            recurso_id  = recurso_id,
            ip          = ip,
            user_agent  = user_agent,
            detalhes    = detalhes,
        ))
        db.flush()
    except Exception:
        pass
