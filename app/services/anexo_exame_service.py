import os
import shutil
from datetime import datetime
from app.repositorios.anexo_exame_repository import AnexoExameRepository

DOCS_ROOT = r"C:\Users\User\OneDrive\1_Geral 2026\Gestao_Agenda_Docs"

EXTENSOES_IMAGEM = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}
EXTENSOES_PDF    = {".pdf"}


def _detectar_tipo(caminho: str) -> str:
    ext = os.path.splitext(caminho)[1].lower()
    if ext in EXTENSOES_PDF:
        return "pdf"
    if ext in EXTENSOES_IMAGEM:
        return "imagem"
    return "outro"


def _pasta_paciente(paciente_id: int, paciente_nome: str) -> str:
    """
    Localiza ou cria a pasta do paciente em DOCS_ROOT.
    Padrão esperado: '{id}. {nome}'  ex: '1. Paulo Roberto Rugani Barcellos'
    """
    os.makedirs(DOCS_ROOT, exist_ok=True)

    # Procura pasta existente que comece com '{id}.'
    prefixo = f"{paciente_id}."
    for entry in os.scandir(DOCS_ROOT):
        if entry.is_dir() and entry.name.startswith(prefixo):
            return entry.path

    # Não encontrou → cria
    nome_pasta = f"{paciente_id}. {paciente_nome}"
    caminho = os.path.join(DOCS_ROOT, nome_pasta)
    os.makedirs(caminho, exist_ok=True)
    return caminho


class AnexoExameService:
    def __init__(self, db):
        self.repo = AnexoExameRepository(db)

    def buscar_por_exame(self, exame_id: int):
        return self.repo.buscar_por_exame(exame_id)

    def anexar(self, exame_id: int, paciente_id: int, paciente_nome: str,
               caminho_origem: str) -> object:
        """
        - Se o arquivo já está dentro de DOCS_ROOT → apenas registra.
        - Caso contrário → copia para a pasta do paciente e registra.
        Retorna o objeto AnexoExame criado.
        """
        caminho_origem = os.path.normpath(caminho_origem)
        docs_root_norm = os.path.normpath(DOCS_ROOT)

        # Verifica se já está no destino correto
        if caminho_origem.startswith(docs_root_norm):
            caminho_final = caminho_origem
        else:
            pasta = _pasta_paciente(paciente_id, paciente_nome)
            nome_arquivo = os.path.basename(caminho_origem)
            # Evita sobrescrever: adiciona timestamp se já existir
            destino = os.path.join(pasta, nome_arquivo)
            if os.path.exists(destino):
                base, ext = os.path.splitext(nome_arquivo)
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                nome_arquivo = f"{base}_{ts}{ext}"
                destino = os.path.join(pasta, nome_arquivo)
            shutil.copy2(caminho_origem, destino)
            caminho_final = destino

        dados = {
            "exame_id" : exame_id,
            "nome"     : os.path.basename(caminho_final),
            "caminho"  : caminho_final,
            "tipo"     : _detectar_tipo(caminho_final),
            "criado_em": datetime.utcnow(),
        }
        return self.repo.criar(dados)

    def remover(self, anexo_id: int, apagar_arquivo: bool = False):
        anexo = self.repo.buscar_por_id(anexo_id)
        if not anexo:
            return
        if apagar_arquivo and os.path.exists(anexo.caminho):
            os.remove(anexo.caminho)
        self.repo.deletar(anexo_id)
