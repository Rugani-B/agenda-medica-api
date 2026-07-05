# app/repositorios/consulta_repository.py
from sqlalchemy.orm import Session
from datetime import datetime, date
from app.models.consulta import Consulta, StatusConsulta
from app.repositorios.base_repository import BaseRepository


class ConsultaRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(Consulta, db)

    def buscar_por_paciente(self, paciente_id: int):
        return (
            self.db.query(Consulta)
            .filter(Consulta.paciente_id == paciente_id)
            .order_by(Consulta.data_hora.desc())
            .all()
        )

    def buscar_por_medico(self, medico_id: int):
        return (
            self.db.query(Consulta)
            .filter(Consulta.medico_id == medico_id)
            .order_by(Consulta.data_hora)
            .all()
        )

    def buscar_por_data(self, data: date):
        inicio = datetime.combine(data, datetime.min.time())
        fim    = datetime.combine(data, datetime.max.time())
        return (
            self.db.query(Consulta)
            .filter(Consulta.data_hora.between(inicio, fim))
            .order_by(Consulta.data_hora)
            .all()
        )

    def buscar_por_status(self, status: StatusConsulta):
        return (
            self.db.query(Consulta)
            .filter(Consulta.status == status)
            .order_by(Consulta.data_hora)
            .all()
        )

    def verificar_conflito(self, medico_id: int, data_hora: datetime):
        """Verifica se o médico já tem consulta no mesmo horário"""
        return (
            self.db.query(Consulta)
            .filter(
                Consulta.medico_id  == medico_id,
                Consulta.data_hora  == data_hora,
                Consulta.status.notin_([
                    StatusConsulta.cancelada,
                    StatusConsulta.realizada
                ])
            )
            .first()
        )

    def atualizar_status(self, id: int, status: StatusConsulta):
        consulta = self.buscar_por_id(id)
        if consulta:
            consulta.status = status
            self.db.commit()
            self.db.refresh(consulta)
        return consulta


    def filtrar(self, texto=None, status=None,
                medico_id=None, dt_inicio=None, dt_fim=None):
        query = self.db.query(Consulta)
        if texto:
            from app.models.pacientes import Paciente
            query = query.join(Consulta.paciente).filter(
                Paciente.nome.ilike(f"%{texto}%")
            )
        if status:
            query = query.filter(Consulta.status == status.value)
        if medico_id:
            query = query.filter(Consulta.medico_id == medico_id)
        if dt_inicio:
            query = query.filter(
                Consulta.data_hora >= datetime.combine(dt_inicio, datetime.min.time())
            )
        if dt_fim:
            query = query.filter(
                Consulta.data_hora <= datetime.combine(dt_fim, datetime.max.time())
            )
        return query.order_by(Consulta.data_hora).all()
