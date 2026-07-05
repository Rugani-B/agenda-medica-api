# app/ui/tela_medicos.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QTableWidget,
    QTableWidgetItem, QLabel, QMessageBox,
    QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from app.database.connection import SessionLocal
from app.services.medico_service import MedicoService
from app.ui.components.dialogs.dialog_medico import DialogMedico


class TelaMedicos(QWidget):
    def __init__(self):
        super().__init__()
        self.db      = SessionLocal()
        self.service = MedicoService(self.db)
        self._setup_ui()
        self._carregar_medicos()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        # Título
        titulo = QLabel("👨‍⚕️ Médicos")
        titulo.setFont(QFont("Arial", 16, QFont.Weight.Bold))

        # Barra de busca e botões
        barra = QHBoxLayout()

        self.input_busca = QLineEdit()
        self.input_busca.setPlaceholderText("🔍 Buscar por nome...")
        self.input_busca.setFixedHeight(35)
        self.input_busca.textChanged.connect(self._buscar)

        btn_novo = QPushButton("+ Novo Médico")
        btn_novo.setFixedHeight(35)
        btn_novo.clicked.connect(self._abrir_dialog_novo)

        barra.addWidget(self.input_busca)
        barra.addWidget(btn_novo)

        # Tabela
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(5)
        self.tabela.setHorizontalHeaderLabels([
            "ID", "Nome", "CRM", "Especialidade", "Telefone"
        ])
        self.tabela.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.tabela.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.tabela.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.tabela.doubleClicked.connect(self._abrir_dialog_editar)

        # Rodapé
        rodape = QHBoxLayout()

        btn_editar  = QPushButton("✏️ Editar")
        btn_deletar = QPushButton("🗑️ Deletar")

        btn_editar.clicked.connect(self._abrir_dialog_editar)
        btn_deletar.clicked.connect(self._deletar_medico)

        rodape.addStretch()
        rodape.addWidget(btn_editar)
        rodape.addWidget(btn_deletar)

        layout.addWidget(titulo)
        layout.addLayout(barra)
        layout.addWidget(self.tabela)
        layout.addLayout(rodape)

    def _carregar_medicos(self, medicos=None):
        if medicos is None:
            medicos = self.service.buscar_todos()

        self.tabela.setRowCount(0)

        for medico in medicos:
            row = self.tabela.rowCount()
            self.tabela.insertRow(row)
            self.tabela.setItem(row, 0, QTableWidgetItem(str(medico.id)))
            self.tabela.setItem(row, 1, QTableWidgetItem(medico.nome))
            self.tabela.setItem(row, 2, QTableWidgetItem(medico.crm or ""))
            self.tabela.setItem(row, 3, QTableWidgetItem(
                medico.especialidade.nome if medico.especialidade else "—"
            ))
            self.tabela.setItem(row, 4, QTableWidgetItem(medico.telefone or ""))

    def _buscar(self, texto: str):
        if texto.strip():
            medicos = self.service.buscar_por_nome(texto)
        else:
            medicos = self.service.buscar_todos()
        self._carregar_medicos(medicos)

    def _abrir_dialog_novo(self):
        dialog = DialogMedico(self.db)
        if dialog.exec():
            self._carregar_medicos()

    def _abrir_dialog_editar(self):
        row = self.tabela.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione um médico.")
            return

        medico_id = int(self.tabela.item(row, 0).text())
        medico    = self.service.buscar_por_id(medico_id)

        dialog = DialogMedico(self.db, medico)
        if dialog.exec():
            self._carregar_medicos()

    def _deletar_medico(self):
        row = self.tabela.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione um médico.")
            return

        nome      = self.tabela.item(row, 1).text()
        medico_id = int(self.tabela.item(row, 0).text())

        resposta = QMessageBox.question(
            self, "Confirmar",
            f"Deletar o médico '{nome}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if resposta == QMessageBox.StandardButton.Yes:
            self.service.deletar(medico_id)
            self._carregar_medicos()
