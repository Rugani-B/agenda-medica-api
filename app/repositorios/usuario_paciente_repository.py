from sqlalchemy.orm import Session
from app.models.usuario_paciente import UsuarioPaciente
from app.models.pacientes import Paciente


class UsuarioPacienteRepository:
    def __init__(self, db: Session):
        self.db = db

    def pacientes_do_usuario(self, usuario_id: int) -> list[Paciente]:
        return (
            self.db.query(Paciente)
            .join(UsuarioPaciente, UsuarioPaciente.paciente_id == Paciente.id)
            .filter(UsuarioPaciente.usuario_id == usuario_id)
            .filter(Paciente.ativo == True)
            .order_by(Paciente.nome)
            .all()
        )

    def ids_do_usuario(self, usuario_id: int) -> set[int]:
        rows = (
            self.db.query(UsuarioPaciente.paciente_id)
            .filter(UsuarioPaciente.usuario_id == usuario_id)
            .all()
        )
        return {r[0] for r in rows}

    def vincular(self, usuario_id: int, paciente_id: int) -> UsuarioPaciente:
        existente = (
            self.db.query(UsuarioPaciente)
            .filter_by(usuario_id=usuario_id, paciente_id=paciente_id)
            .first()
        )
        if existente:
            return existente
        vinculo = UsuarioPaciente(usuario_id=usuario_id, paciente_id=paciente_id)
        self.db.add(vinculo)
        self.db.commit()
        self.db.refresh(vinculo)
        return vinculo

    def desvincular(self, usuario_id: int, paciente_id: int) -> None:
        self.db.query(UsuarioPaciente).filter_by(
            usuario_id=usuario_id, paciente_id=paciente_id
        ).delete()
        self.db.commit()

    def vinculos_do_usuario(self, usuario_id: int) -> list[UsuarioPaciente]:
        return (
            self.db.query(UsuarioPaciente)
            .filter_by(usuario_id=usuario_id)
            .all()
        )
