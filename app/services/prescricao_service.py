from datetime import datetime
from app.repositorios.prescricao_repository import PrescricaoRepository


class PrescricaoService:
    def __init__(self, db):
        self.repo = PrescricaoRepository(db)

    def buscar_por_consulta(self, consulta_id: int):
        return self.repo.buscar_por_consulta(consulta_id)

    def buscar_por_id(self, id: int):
        return self.repo.buscar_por_id(id)

    def buscar_todas(self):
        return self.repo.buscar_todas()

    def buscar_por_paciente(self, paciente_id: int):
        return self.repo.buscar_por_paciente(paciente_id)

    def criar(self, consulta_id: int, paciente_id: int,
              medico_id: int = None, observacoes: str = None):
        dados = {
            "consulta_id": consulta_id,
            "paciente_id": paciente_id,
            "medico_id"  : medico_id,
            "observacoes": observacoes,
            "criado_em"  : datetime.utcnow(),
        }
        return self.repo.criar(dados)

    def atualizar(self, id: int, dados: dict):
        return self.repo.atualizar(id, dados)

    def deletar(self, id: int):
        return self.repo.deletar(id)

    def adicionar_item(self, prescricao_id: int, medicamento_id: int,
                       dose: str = None, frequencia: str = None,
                       duracao: str = None, instrucoes: str = None):
        dados = {
            "prescricao_id" : prescricao_id,
            "medicamento_id": medicamento_id,
            "dose"          : dose,
            "frequencia"    : frequencia,
            "duracao"       : duracao,
            "instrucoes"    : instrucoes,
        }
        return self.repo.adicionar_item(dados)

    def remover_item(self, item_id: int):
        self.repo.remover_item(item_id)
