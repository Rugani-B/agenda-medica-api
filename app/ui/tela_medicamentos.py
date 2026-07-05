from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QLabel,
    QMessageBox, QHeaderView
)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt
from app.database.connection import SessionLocal
from app.services.medicamento_service import MedicamentoService
from app.ui.components.dialogs.dialog_medicamento import DialogMedicamento


class TelaMedicamentos(QWidget):
    def __init__(self):
        super().__init__()
        self.db      = SessionLocal()
        self.service = MedicamentoService(self.db)
        self._setup_ui()
        self._carregar()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(15, 15, 15, 15)

        titulo = QLabel("💊 Medicamentos")
        titulo.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        titulo.setFixedHeight(30)
        layout.addWidget(titulo)

        # Busca
        busca_layout = QHBoxLayout()
        self.input_busca = QLineEdit()
        self.input_busca.setPlaceholderText("🔍 Buscar por nome ou princípio ativo...")
        self.input_busca.setFixedHeight(32)
        self.input_busca.textChanged.connect(self._buscar)
        busca_layout.addWidget(self.input_busca)
        layout.addLayout(busca_layout)

        # Tabela
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(4)
        self.tabela.setHorizontalHeaderLabels(["ID", "Nome", "Princípio Ativo", "Apresentação"])
        header = self.tabela.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.tabela.setColumnWidth(0, 45)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        self.tabela.setColumnWidth(3, 150)
        self.tabela.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabela.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabela.setAlternatingRowColors(True)
        self.tabela.doubleClicked.connect(self._editar)
        self.tabela.setStyleSheet("""
            QTableWidget {
                background-color: #f9f9f9;
                alternate-background-color: #f0f0f0;
                gridline-color: #d0d0d0;
            }
            QHeaderView::section {
                background-color: #8e44ad;
                color: white;
                font-weight: bold;
                padding: 4px;
                border: none;
            }
        """)
        layout.addWidget(self.tabela)

        # Rodapé
        rodape = QHBoxLayout()
        btn_novo    = QPushButton("➕ Novo")
        btn_editar  = QPushButton("✏️ Editar")
        btn_deletar = QPushButton("🗑️ Deletar")
        btn_atualizar = QPushButton("🔃 Atualizar")

        for btn in [btn_novo, btn_editar, btn_deletar]:
            btn.setFixedHeight(32)
            rodape.addWidget(btn)

        btn_novo.clicked.connect(self._novo)
        btn_editar.clicked.connect(self._editar)
        btn_deletar.clicked.connect(self._deletar)
        btn_atualizar.clicked.connect(self._atualizar)

        rodape.addStretch()
        btn_atualizar.setFixedHeight(32)
        btn_atualizar.setStyleSheet("""
            QPushButton {
                background-color: #8e44ad;
                color: white;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #6c3483; }
        """)
        rodape.addWidget(btn_atualizar)
        layout.addLayout(rodape)

    def _carregar(self, medicamentos=None):
        if medicamentos is None:
            medicamentos = self.service.buscar_todos()
        self.tabela.setRowCount(0)
        for m in medicamentos:
            row = self.tabela.rowCount()
            self.tabela.insertRow(row)
            self.tabela.setItem(row, 0, QTableWidgetItem(str(m.id)))
            self.tabela.setItem(row, 1, QTableWidgetItem(m.nome or ""))
            self.tabela.setItem(row, 2, QTableWidgetItem(m.principio_ativo or ""))
            self.tabela.setItem(row, 3, QTableWidgetItem(m.apresentacao or ""))

    def _buscar(self):
        texto = self.input_busca.text().strip()
        if texto:
            self._carregar(self.service.buscar_por_nome(texto))
        else:
            self._carregar()

    def _selecionado(self):
        row = self.tabela.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione um medicamento.")
            return None
        id_item = self.tabela.item(row, 0)
        return self.service.buscar_por_id(int(id_item.text())) if id_item else None

    def _novo(self):
        dlg = DialogMedicamento(self.db, parent=self)
        if dlg.exec():
            self._carregar()

    def _editar(self):
        med = self._selecionado()
        if not med:
            return
        dlg = DialogMedicamento(self.db, medicamento=med, parent=self)
        if dlg.exec():
            self._carregar()

    def _deletar(self):
        med = self._selecionado()
        if not med:
            return
        resp = QMessageBox.question(self, "Confirmar",
            f"Deletar '{med.nome}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if resp == QMessageBox.StandardButton.Yes:
            try:
                self.service.deletar(med.id)
                self._carregar()
            except Exception as e:
                QMessageBox.critical(self, "Erro", str(e))

    def _atualizar(self):
        self.db.rollback()    # ← encerra transação para ver dados novos (REPEATABLE READ)
        self.db.expire_all()
        self._carregar()
