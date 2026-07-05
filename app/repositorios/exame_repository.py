from sqlalchemy.orm import Session
from datetime import datetime, date
from app.models.exame import Exame, StatusExame
from app.repositorios.base_repository import BaseRepository


class ExameRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(Exame, db)

    def buscar_por_paciente(self, paciente_id: int):
        return (
            self.db.query(Exame)
            .filter(Exame.paciente_id == paciente_id)
            .order_by(Exame.data_hora.desc())
            .all()
        )

    def buscar_por_status(self, status: StatusExame):
        return (
            self.db.query(Exame)
            .filter(Exame.status == status)
            .order_by(Exame.data_hora)
            .all()
        )

    def buscar_por_data(self, data: date):
        inicio = datetime.combine(data, datetime.min.time())
        fim    = datetime.combine(data, datetime.max.time())
        return (
            self.db.query(Exame)
            .filter(Exame.data_hora.between(inicio, fim))
            .order_by(Exame.data_hora)
            .all()
        )

    def filtrar(self, texto=None, status=None,
                paciente_id=None, dt_inicio=None, dt_fim=None):
        query = self.db.query(Exame)
        if texto:
            from app.models.pacientes import Paciente
            query = query.join(Exame.paciente).filter(
                Paciente.nome.ilike(f"%{texto}%")
            )
        if status:
            query = query.filter(Exame.status == status)
        if paciente_id:
            query = query.filter(Exame.paciente_id == paciente_id)
        if dt_inicio:
            query = query.filter(
                Exame.data_hora >= datetime.combine(dt_inicio, datetime.min.time())
            )
        if dt_fim:
            query = query.filter(
                Exame.data_hora <= datetime.combine(dt_fim, datetime.max.time())
            )
        return query.order_by(Exame.data_hora).all()

    def atualizar_status(self, id: int, status: StatusExame):
        exame = self.buscar_por_id(id)
        if exame:
            exame.status = status
            self.db.commit()
            self.db.refresh(exame)
        return exame
