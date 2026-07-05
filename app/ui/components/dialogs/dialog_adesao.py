import datetime
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QComboBox,
    QTextEdit, QDialogButtonBox, QMessageBox, QLabel, QDateEdit
)
from PyQt6.QtCore import QDate
from app.services.adesao_service import AdesaoService
from app.models.adesao_tratamento import NivelAdesao, NIVEL_LABELS

NIVEL_ITEMS = [
    (NivelAdesao.nenhuma, "⬛  Nenhuma   (0%)"),
    (NivelAdesao.baixa,   "🔴  Baixa      (até 25%)"),
    (NivelAdesao.parcial, "🟡  Parcial    (até 50%)"),
    (NivelAdesao.boa,     "🔵  Boa        (até 75%)"),
    (NivelAdesao.total,   "🟢  Total      (100%)"),
]


class DialogAdesao(QDialog):
    def __init__(self, db, prescricao, adesao=None, semana=None, parent=None):
        super().__init__(parent)
        self.db         = db
        self.prescricao = prescricao
        self.adesao     = adesao
        self._semana_inicial = semana
        self.service    = AdesaoService(db)

        self.setWindowTitle("✏️ Editar Adesão" if adesao else "📋 Registrar Adesão Semanal")
        self.setMinimumWidth(420)
        self._setup_ui()
        if adesao:
            self._preencher()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Cabeçalho informativo
        pac  = self.prescricao.paciente.nome if self.prescricao.paciente else "—"
        info = QLabel(f"Prescrição #{self.prescricao.id}  —  {pac}")
        info.setStyleSheet("font-weight: bold; font-size: 13px; margin-bottom: 4px;")
        layout.addWidget(info)

        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        # Semana (segunda-feira)
        self.input_semana = QDateEdit()
        self.input_semana.setCalendarPopup(True)
        self.input_semana.setDisplayFormat("dd/MM/yyyy")
        data_inicial = self._semana_inicial or AdesaoService.semana_atual()
        self.input_semana.setDate(QDate(data_inicial.year, data_inicial.month, data_inicial.day))
        self.input_semana.dateChanged.connect(self._corrigir_para_segunda)

        # Nível
        self.combo_nivel = QComboBox()
        self.combo_nivel.setFixedHeight(34)
        for nivel, label in NIVEL_ITEMS:
            self.combo_nivel.addItem(label, nivel)
        self.combo_nivel.currentIndexChanged.connect(self._atualizar_cor_combo)
        self._atualizar_cor_combo()

        # Observações
        self.input_obs = QTextEdit()
        self.input_obs.setPlaceholderText("Comentários sobre a adesão desta semana...")
        self.input_obs.setMaximumHeight(80)

        form.addRow("Semana (início):", self.input_semana)
        form.addRow("Nível de adesão:", self.combo_nivel)
        form.addRow("Observações:",     self.input_obs)
        layout.addLayout(form)

        botoes = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        botoes.accepted.connect(self._salvar)
        botoes.rejected.connect(self.reject)
        layout.addWidget(botoes)

    def _corrigir_para_segunda(self, qdate):
        """Garante que a data sempre seja uma segunda-feira."""
        d = qdate.toPyDate()
        segunda = d - datetime.timedelta(days=d.weekday())
        if segunda != d:
            self.input_semana.blockSignals(True)
            self.input_semana.setDate(QDate(segunda.year, segunda.month, segunda.day))
            self.input_semana.blockSignals(False)

    def _atualizar_cor_combo(self):
        nivel = self.combo_nivel.currentData()
        cores = {
            NivelAdesao.nenhuma: "#888780",
            NivelAdesao.baixa  : "#c0392b",
            NivelAdesao.parcial: "#d68910",
            NivelAdesao.boa    : "#1a6fb5",
            NivelAdesao.total  : "#3b6d11",
        }
        cor = cores.get(nivel, "#333")
        self.combo_nivel.setStyleSheet(
            f"QComboBox {{ color: {cor}; font-weight: bold; }}"
        )

    def _preencher(self):
        a = self.adesao
        d = a.semana
        self.input_semana.setDate(QDate(d.year, d.month, d.day))
        for i in range(self.combo_nivel.count()):
            if self.combo_nivel.itemData(i) == a.nivel:
                self.combo_nivel.setCurrentIndex(i)
                break
        self.input_obs.setText(a.observacoes or "")

    def _salvar(self):
        semana = self.input_semana.date().toPyDate()
        nivel  = self.combo_nivel.currentData()
        obs    = self.input_obs.toPlainText().strip() or None
        try:
            self.service.registrar(self.prescricao.id, semana, nivel, obs)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))
