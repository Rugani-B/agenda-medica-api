import datetime
import os
import subprocess
import sys
from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QDateEdit, QCheckBox, QGroupBox, QMessageBox, QProgressBar
)
from PyQt6.QtCore import Qt, QDate, QThread, pyqtSignal

from app.services.relatorio_service import gerar_relatorio_paciente


class _WorkerPDF(QThread):
    concluido = pyqtSignal(str)
    erro = pyqtSignal(str)

    def __init__(self, paciente_id, data_inicio, data_fim, secoes, caminho):
        super().__init__()
        self.paciente_id = paciente_id
        self.data_inicio = data_inicio
        self.data_fim = data_fim
        self.secoes = secoes
        self.caminho = caminho

    def run(self):
        try:
            gerar_relatorio_paciente(
                self.paciente_id, self.data_inicio, self.data_fim,
                self.secoes, self.caminho
            )
            self.concluido.emit(self.caminho)
        except Exception as e:
            self.erro.emit(str(e))


class DialogRelatorio(QDialog):
    def __init__(self, paciente_id: int, paciente_nome: str, parent=None):
        super().__init__(parent)
        self.paciente_id = paciente_id
        self.paciente_nome = paciente_nome
        self.setWindowTitle("Relatório PDF")
        self.setMinimumWidth(380)
        self._build_ui()

    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(12)

        lay.addWidget(QLabel(f"<b>{self.paciente_nome}</b>"))

        # Período
        grp_per = QGroupBox("Período")
        per_lay = QHBoxLayout(grp_per)
        hoje = QDate.currentDate()
        inicio_default = hoje.addMonths(-3)

        self.dt_inicio = QDateEdit(calendarPopup=True)
        self.dt_inicio.setDate(inicio_default)
        self.dt_inicio.setDisplayFormat("dd/MM/yyyy")

        self.dt_fim = QDateEdit(calendarPopup=True)
        self.dt_fim.setDate(hoje)
        self.dt_fim.setDisplayFormat("dd/MM/yyyy")

        per_lay.addWidget(QLabel("De:"))
        per_lay.addWidget(self.dt_inicio)
        per_lay.addWidget(QLabel("Até:"))
        per_lay.addWidget(self.dt_fim)
        lay.addWidget(grp_per)

        # Seções
        grp_sec = QGroupBox("Seções")
        sec_lay = QVBoxLayout(grp_sec)
        self.chk_consultas   = QCheckBox("Consultas")
        self.chk_exames      = QCheckBox("Exames")
        self.chk_prescricoes = QCheckBox("Prescrições / Tratamentos")
        self.chk_adesao      = QCheckBox("Adesão ao tratamento")
        for chk in (self.chk_consultas, self.chk_exames, self.chk_prescricoes, self.chk_adesao):
            chk.setChecked(True)
            sec_lay.addWidget(chk)
        lay.addWidget(grp_sec)

        # Barra de progresso (oculta até gerar)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        lay.addWidget(self.progress)

        # Botões
        btn_lay = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setFixedHeight(28)
        btn_cancelar.clicked.connect(self.reject)

        self.btn_gerar = QPushButton("📄 Gerar PDF")
        self.btn_gerar.setFixedHeight(28)
        self.btn_gerar.setMinimumWidth(120)
        self.btn_gerar.setStyleSheet("background:#1a5276; color:white; border-radius:4px; padding: 0 16px;")
        self.btn_gerar.clicked.connect(self._gerar)

        btn_lay.addWidget(btn_cancelar)
        btn_lay.addStretch()
        btn_lay.addWidget(self.btn_gerar)
        lay.addLayout(btn_lay)

    def _gerar(self):
        d_ini = self.dt_inicio.date().toPyDate()
        d_fim = self.dt_fim.date().toPyDate()
        if d_ini > d_fim:
            QMessageBox.warning(self, "Período inválido", "A data de início deve ser anterior à data fim.")
            return

        secoes = {
            "consultas":   self.chk_consultas.isChecked(),
            "exames":      self.chk_exames.isChecked(),
            "prescricoes": self.chk_prescricoes.isChecked(),
            "adesao":      self.chk_adesao.isChecked(),
        }
        if not any(secoes.values()):
            QMessageBox.warning(self, "Sem seções", "Selecione pelo menos uma seção.")
            return

        base = f"relatorio_{self.paciente_nome.replace(' ', '_')}_{d_ini.strftime('%Y%m%d')}"
        downloads = Path.home() / "Downloads"
        downloads.mkdir(exist_ok=True)
        caminho = str(_proximo_caminho(downloads, base))

        self.btn_gerar.setEnabled(False)
        self.progress.setVisible(True)

        self._worker = _WorkerPDF(self.paciente_id, d_ini, d_fim, secoes, caminho)
        self._worker.concluido.connect(self._ao_concluir)
        self._worker.erro.connect(self._ao_erro)
        self._worker.start()

    def _ao_concluir(self, caminho: str):
        self.progress.setVisible(False)
        self.btn_gerar.setEnabled(True)
        _abrir_arquivo(caminho)
        self.accept()

    def _ao_erro(self, msg: str):
        self.progress.setVisible(False)
        self.btn_gerar.setEnabled(True)
        QMessageBox.critical(self, "Erro ao gerar PDF", msg)


def _proximo_caminho(pasta: Path, base: str) -> Path:
    """Retorna pasta/base.pdf; se bloqueado ou em uso, tenta base(1).pdf, base(2).pdf..."""
    candidato = pasta / f"{base}.pdf"
    if not candidato.exists():
        return candidato
    # Arquivo existe — verifica se está bloqueado (aberto por outro processo)
    if _pode_sobrescrever(candidato):
        return candidato
    # Está bloqueado: procura o próximo nome livre ou não bloqueado
    for n in range(1, 100):
        candidato = pasta / f"{base}({n}).pdf"
        if not candidato.exists() or _pode_sobrescrever(candidato):
            return candidato
    return pasta / f"{base}(100).pdf"


def _pode_sobrescrever(caminho: Path) -> bool:
    """Tenta abrir o arquivo para escrita; retorna False se estiver bloqueado."""
    try:
        with open(caminho, "ab"):
            return True
    except OSError:
        return False


def _abrir_arquivo(caminho: str):
    if sys.platform == "win32":
        os.startfile(caminho)
    elif sys.platform == "darwin":
        subprocess.call(["open", caminho])
    else:
        subprocess.call(["xdg-open", caminho])
