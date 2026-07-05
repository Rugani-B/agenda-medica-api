from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QComboBox, QLineEdit, QTextEdit, QTableWidget,
    QTableWidgetItem, QDialogButtonBox, QMessageBox,
    QPushButton, QGroupBox, QHeaderView, QLabel
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from app.services.prescricao_service import PrescricaoService
from app.services.medicamento_service import MedicamentoService


class DialogPrescricao(QDialog):
    def __init__(self, db, consulta, prescricao=None, parent=None):
        super().__init__(parent)
        self.db          = db
        self.consulta    = consulta
        self.prescricao  = prescricao
        self.service     = PrescricaoService(db)
        self.svc_med     = MedicamentoService(db)

        self.setWindowTitle("✏️ Editar Prescrição" if prescricao else "➕ Nova Prescrição")
        self.setMinimumSize(700, 550)
        self._setup_ui()
        if prescricao:
            self._carregar_itens()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # ── Observações gerais ────────────────────────
        form = QFormLayout()
        self.input_obs = QTextEdit()
        self.input_obs.setPlaceholderText("Observações gerais da prescrição...")
        self.input_obs.setMaximumHeight(70)
        if self.prescricao:
            self.input_obs.setText(self.prescricao.observacoes or "")
        form.addRow("Observações:", self.input_obs)
        layout.addLayout(form)

        # ── Adicionar medicamento ─────────────────────
        grupo = QGroupBox("💊 Medicamentos")
        grupo.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        glayout = QVBoxLayout(grupo)

        flinha = QHBoxLayout()
        self.combo_med = QComboBox()
        self.combo_med.setMinimumWidth(200)
        self._popular_medicamentos()

        self.input_dose      = QLineEdit(); self.input_dose.setPlaceholderText("Dose (ex: 500mg)")
        self.input_freq      = QLineEdit(); self.input_freq.setPlaceholderText("Frequência (ex: 8/8h)")
        self.input_dur       = QLineEdit(); self.input_dur.setPlaceholderText("Duração (ex: 7 dias)")
        self.input_instrucoes = QLineEdit(); self.input_instrucoes.setPlaceholderText("Instruções")

        btn_add = QPushButton("➕ Adicionar")
        btn_add.setFixedHeight(30)
        btn_add.clicked.connect(self._adicionar_item)

        flinha.addWidget(QLabel("Medicamento:"))
        flinha.addWidget(self.combo_med, 2)
        flinha.addWidget(self.input_dose, 1)
        flinha.addWidget(self.input_freq, 1)
        flinha.addWidget(self.input_dur, 1)
        flinha.addWidget(btn_add)
        glayout.addLayout(flinha)

        flinha2 = QHBoxLayout()
        flinha2.addWidget(QLabel("Instruções:"))
        flinha2.addWidget(self.input_instrucoes)
        glayout.addLayout(flinha2)

        # Tabela de itens
        self.tabela_itens = QTableWidget()
        self.tabela_itens.setColumnCount(6)
        self.tabela_itens.setHorizontalHeaderLabels(
            ["ID", "Medicamento", "Dose", "Frequência", "Duração", "Instruções"]
        )
        self.tabela_itens.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabela_itens.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.tabela_itens.setColumnWidth(0, 40)
        self.tabela_itens.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabela_itens.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabela_itens.setMinimumHeight(180)
        glayout.addWidget(self.tabela_itens)

        btn_remover = QPushButton("🗑️ Remover item selecionado")
        btn_remover.setFixedHeight(28)
        btn_remover.clicked.connect(self._remover_item)
        glayout.addWidget(btn_remover)

        layout.addWidget(grupo)

        botoes = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        botoes.accepted.connect(self._salvar)
        botoes.rejected.connect(self.reject)
        layout.addWidget(botoes)

    def _popular_medicamentos(self):
        self.db.expire_all()
        self.combo_med.clear()
        self.combo_med.addItem("— Selecione —", None)
        for m in self.svc_med.buscar_todos():
            label = m.nome
            if m.apresentacao:
                label += f" ({m.apresentacao})"
            self.combo_med.addItem(label, m.id)

    def _carregar_itens(self):
        self.tabela_itens.setRowCount(0)
        for item in self.prescricao.itens:
            self._inserir_linha_item(item)

    def _inserir_linha_item(self, item):
        row = self.tabela_itens.rowCount()
        self.tabela_itens.insertRow(row)
        nome_med = item.medicamento.nome if item.medicamento else "—"
        self.tabela_itens.setItem(row, 0, QTableWidgetItem(str(item.id)))
        self.tabela_itens.setItem(row, 1, QTableWidgetItem(nome_med))
        self.tabela_itens.setItem(row, 2, QTableWidgetItem(item.dose        or ""))
        self.tabela_itens.setItem(row, 3, QTableWidgetItem(item.frequencia  or ""))
        self.tabela_itens.setItem(row, 4, QTableWidgetItem(item.duracao     or ""))
        self.tabela_itens.setItem(row, 5, QTableWidgetItem(item.instrucoes  or ""))

    def _adicionar_item(self):
        # Auto-cria a prescrição no banco se ainda não existe
        if not self.prescricao:
            obs = self.input_obs.toPlainText().strip() or None
            self.prescricao = self.service.criar(
                consulta_id=self.consulta.id,
                paciente_id=self.consulta.paciente_id,
                medico_id=self.consulta.medico_id,
                observacoes=obs,
            )

        med_id = self.combo_med.currentData()
        if not med_id:
            QMessageBox.warning(self, "Atenção", "Selecione um medicamento.")
            return
        item = self.service.adicionar_item(
            prescricao_id=self.prescricao.id,
            medicamento_id=med_id,
            dose=self.input_dose.text().strip() or None,
            frequencia=self.input_freq.text().strip() or None,
            duracao=self.input_dur.text().strip() or None,
            instrucoes=self.input_instrucoes.text().strip() or None,
        )
        self._inserir_linha_item(item)
        self.input_dose.clear(); self.input_freq.clear()
        self.input_dur.clear();  self.input_instrucoes.clear()
        self.combo_med.setCurrentIndex(0)

    def _remover_item(self):
        row = self.tabela_itens.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione um item.")
            return
        item_id = int(self.tabela_itens.item(row, 0).text())
        resp = QMessageBox.question(self, "Confirmar", "Remover este medicamento da prescrição?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if resp == QMessageBox.StandardButton.Yes:
            self.service.remover_item(item_id)
            self.tabela_itens.removeRow(row)

    def _salvar(self):
        obs = self.input_obs.toPlainText().strip() or None
        try:
            if self.prescricao:
                # Atualiza observações (prescrição pode ter sido auto-criada ao adicionar itens)
                self.service.atualizar(self.prescricao.id, {"observacoes": obs})
            else:
                # Prescrição sem itens — cria agora
                self.prescricao = self.service.criar(
                    consulta_id=self.consulta.id,
                    paciente_id=self.consulta.paciente_id,
                    medico_id=self.consulta.medico_id,
                    observacoes=obs,
                )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))
