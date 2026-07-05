import datetime
from app.repositorios.adesao_repository import AdesaoRepository
from app.models.adesao_tratamento import NivelAdesao, NIVEL_PCT


class AdesaoService:
    def __init__(self, db):
        self.repo = AdesaoRepository(db)

    def buscar_por_prescricao(self, prescricao_id: int):
        return self.repo.buscar_por_prescricao(prescricao_id)

    def registrar(self, prescricao_id: int, semana: datetime.date,
                  nivel: NivelAdesao, observacoes: str = None):
        """Cria ou atualiza o registro da semana (upsert)."""
        existente = self.repo.buscar_por_semana(prescricao_id, semana)
        dados = {
            "prescricao_id": prescricao_id,
            "semana"       : semana,
            "nivel"        : nivel,
            "observacoes"  : observacoes,
            "registrado_em": datetime.datetime.utcnow(),
        }
        if existente:
            return self.repo.atualizar(existente.id, dados)
        return self.repo.criar(dados)

    def deletar(self, adesao_id: int):
        return self.repo.deletar(adesao_id)

    @staticmethod
    def semana_atual() -> datetime.date:
        """Retorna a segunda-feira da semana corrente."""
        hoje = datetime.date.today()
        return hoje - datetime.timedelta(days=hoje.weekday())

    @staticmethod
    def media_percentual(adesoes: list) -> float:
        """Média simples em % dos registros existentes."""
        if not adesoes:
            return 0.0
        total = sum(NIVEL_PCT.get(a.nivel.value if hasattr(a.nivel, 'value') else a.nivel, 0)
                    for a in adesoes)
        return total / len(adesoes)
