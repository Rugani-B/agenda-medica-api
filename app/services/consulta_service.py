# app/services/consulta_service.py
from datetime import date
from app.repositorios.consulta_repository import ConsultaRepository
from app.repositorios.reagendamento_repository import ReagendamentoRepository
from app.models.consulta import StatusConsulta


class ConsultaService:
    def __init__(self, db):
        self.repo          = ConsultaRepository(db)
        self.repo_reagend  = ReagendamentoRepository(db)

    def buscar_todos(self):
        return self.repo.buscar_todos()

    def svc_por_paciente(self, paciente_id: int):
        return self.repo.buscar_por_paciente(paciente_id)

    def buscar_por_id(self, id: int):
        return self.repo.buscar_por_id(id)

    def cadastrar(self, dados: dict):
        if not dados.get("paciente_id"):
            raise ValueError("Paciente é obrigatório.")
        if not dados.get("medico_id"):
            raise ValueError("Médico é obrigatório.")
        if not dados.get("data_hora"):
            raise ValueError("Data/hora é obrigatória.")
        return self.repo.criar(dados)

    def atualizar(self, id: int, dados: dict):
        consulta = self.repo.buscar_por_id(id)
        if not consulta:
            raise ValueError("Consulta não encontrada.")
        return self.repo.atualizar(id, dados)

    def atualizar_status(self, id: int, status: StatusConsulta):
        consulta = self.repo.buscar_por_id(id)
        if not consulta:
            raise ValueError("Consulta não encontrada.")
        return self.repo.atualizar(id, {"status": status})

    def reagendar(self, id: int, nova_data):
        consulta = self.repo.buscar_por_id(id)
        if not consulta:
            raise ValueError("Consulta não encontrada.")

        # Salva histórico de reagendamento
        self.repo_reagend.criar({
            "consulta_id"  : id,
            "data_anterior": consulta.data_hora,
            "nova_data"    : nova_data,
            "motivo"       : "Reagendado pelo sistema",
        })

        # Atualiza consulta
        return self.repo.atualizar(id, {
            "data_hora": nova_data,
            "status"   : StatusConsulta.reagendada,
        })

    def filtrar(self, texto=None, status=None,
                medico_id=None, dt_inicio=None, dt_fim=None):
        return self.repo.filtrar(
            texto     = texto,
            status    = status,
            medico_id = medico_id,
            dt_inicio = dt_inicio,
            dt_fim    = dt_fim,
        )

    def deletar(self, id: int):
        return self.repo.deletar(id)
