# app/services/notificacao_service.py
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.confirmacao import Confirmacao, StatusConfirmacao
from app.repositorios.consulta_repository import ConsultaRepository


class NotificacaoService:
    def __init__(self, db: Session):
        self.db         = db
        self.repo       = ConsultaRepository(db)

    def registrar_confirmacao(self, consulta_id: int, canal: str) -> Confirmacao:
        """Registra o envio de uma notificação"""
        consulta = self.repo.buscar_por_id(consulta_id)
        if not consulta:
            raise ValueError("Consulta não encontrada.")

        confirmacao = Confirmacao(
            consulta_id = consulta_id,
            enviado_em  = datetime.now(),
            canal       = canal,  # ex: "whatsapp", "email", "sms"
            status      = StatusConfirmacao.agendada
        )
        self.db.add(confirmacao)
        self.db.commit()
        self.db.refresh(confirmacao)
        return confirmacao

    def registrar_resposta(self, confirmacao_id: int, resposta: str) -> Confirmacao:
        """Registra a resposta do paciente"""
        confirmacao = (
            self.db.query(Confirmacao)
            .filter(Confirmacao.id == confirmacao_id)
            .first()
        )
        if not confirmacao:
            raise ValueError("Confirmação não encontrada.")

        confirmacao.respondido      = resposta
        confirmacao.respondido_em   = datetime.now()
        confirmacao.status          = StatusConfirmacao.confirmada

        self.db.commit()
        self.db.refresh(confirmacao)
        return confirmacao
