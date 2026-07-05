import os
import shutil
from datetime import datetime
from app.repositorios.pedido_exame_repository import PedidoExameRepository
from app.models.pedido_exame import StatusPedido
from app.services.anexo_exame_service import DOCS_ROOT, _pasta_paciente


class PedidoExameService:
    def __init__(self, db):
        self.repo = PedidoExameRepository(db)

    @staticmethod
    def _registrar_documento(paciente_id: int, paciente_nome: str, caminho_origem: str) -> str:
        """
        Copia o arquivo (PDF/JPG) do pedido de exame para a pasta do paciente
        em DOCS_ROOT (se ainda não estiver lá) e retorna o caminho final.
        """
        caminho_origem = os.path.normpath(caminho_origem)
        docs_root_norm = os.path.normpath(DOCS_ROOT)

        if caminho_origem.startswith(docs_root_norm):
            return caminho_origem

        pasta = _pasta_paciente(paciente_id, paciente_nome)
        nome_arquivo = os.path.basename(caminho_origem)
        destino = os.path.join(pasta, nome_arquivo)
        if os.path.exists(destino):
            base, ext = os.path.splitext(nome_arquivo)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_arquivo = f"{base}_{ts}{ext}"
            destino = os.path.join(pasta, nome_arquivo)
        shutil.copy2(caminho_origem, destino)
        return destino

    def buscar_por_consulta(self, consulta_id: int):
        return self.repo.buscar_por_consulta(consulta_id)

    def buscar_por_id(self, id: int):
        return self.repo.buscar_por_id(id)

    def filtrar(self, status=None, paciente_id=None, medico_id=None):
        return self.repo.filtrar(status=status, paciente_id=paciente_id, medico_id=medico_id)

    def criar(self, paciente_id: int, tipo_exame_id: int,
              consulta_id: int = None, medico_id: int = None,
              urgente: bool = False, observacoes: str = None,
              status: StatusPedido = None,
              paciente_nome: str = None, documento_origem: str = None):
        if not tipo_exame_id:
            raise ValueError("Tipo de exame é obrigatório.")
        if not paciente_id:
            raise ValueError("Paciente é obrigatório.")

        documento_path = None
        if documento_origem:
            documento_path = self._registrar_documento(
                paciente_id, paciente_nome or "", documento_origem
            )

        return self.repo.criar({
            "consulta_id"   : consulta_id,
            "paciente_id"   : paciente_id,
            "medico_id"     : medico_id,
            "tipo_exame_id" : tipo_exame_id,
            "urgente"       : urgente,
            "observacoes"   : observacoes,
            "status"        : status or StatusPedido.solicitado,
            "criado_em"     : datetime.utcnow(),
            "documento_path": documento_path,
        })

    def atualizar(self, id: int, dados: dict):
        return self.repo.atualizar(id, dados)

    def deletar(self, id: int):
        return self.repo.deletar(id)

    def vincular_exame(self, pedido_id: int, exame_id: int):
        """Vincula um exame existente ao pedido e marca como agendado."""
        return self.repo.atualizar(pedido_id, {
            "exame_id": exame_id,
            "status"  : StatusPedido.agendado,
        })

    def desvincular_exame(self, pedido_id: int):
        return self.repo.atualizar(pedido_id, {
            "exame_id": None,
            "status"  : StatusPedido.solicitado,
        })

    def marcar_realizado(self, pedido_id: int):
        return self.repo.atualizar(pedido_id, {"status": StatusPedido.realizado})

    def cancelar(self, pedido_id: int):
        return self.repo.atualizar(pedido_id, {"status": StatusPedido.cancelado})
