from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QDialogButtonBox, QMessageBox, QLabel, QLineEdit,
    QHBoxLayout, QHeaderView
)
from PyQt6.QtCore import Qt
from app.services.exame_service import ExameService


class DialogVincularExame(QDialog):
    def __init__(self, db, consulta, parent=None):
        super().__init__(parent)
        self.db                   = db
        self.consulta             = consulta
        self.service              = ExameService(db)
        self.exame_id_selecionado = None

        self.setWindowTitle("🔗 Vincular Exame à Consulta")
        self.setMinimumSize(650, 420)
        self._setup_ui()
        self._carregar()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        info = QLabel(f"Selecione o(s) exame(s) do paciente "
                      f"<b>{self.consulta.paciente.nome}</b> para vincular a esta consulta.")
        info.setWordWrap(True)
        layout.addWidget(info)

        busca_layout = QHBoxLayout()
        self.input_busca = QLineEdit()
        self.input_busca.setPlaceholderText("🔍 Filtrar por tipo de exame...")
        self.input_busca.setFixedHeight(30)
        self.input_busca.textChanged.connect(self._carregar)
        busca_layout.addWidget(self.input_busca)
        layout.addLayout(busca_layout)

        self.tabela = QTableWidget()
        self.tabela.setColumnCount(4)
        self.tabela.setHorizontalHeaderLabels(["ID", "Tipo de Exame", "Data/Hora", "Status"])
        h = self.tabela.horizontalHeader()
        h.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.tabela.setColumnWidth(0, 45)
        self.tabela.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabela.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabela.setMinimumHeight(220)
        layout.addWidget(self.tabela)

        botoes = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        botoes.accepted.connect(self._vincular)
        botoes.rejected.connect(self.reject)
        layout.addWidget(botoes)

    def _carregar(self):
        # Mostra apenas exames do mesmo paciente sem consulta vinculada
        exames = self.service.filtrar(
            paciente_id=self.consulta.paciente_id
        )
        texto = self.input_busca.text().strip().lower()
        self.tabela.setRowCount(0)
        for e in exames:
            if e.consulta_id is not None:
                continue   # já vinculado
            tipo = e.tipo_exame.nome if e.tipo_exame else ""
            if texto and texto not in tipo.lower():
                continue
            row = self.tabela.rowCount()
            self.tabela.insertRow(row)
            data = e.data_hora.strftime("%d/%m/%Y %H:%M") if e.data_hora else ""
            stat = e.status.value.capitalize() if e.status else ""
            self.tabela.setItem(row, 0, QTableWidgetItem(str(e.id)))
            self.tabela.setItem(row, 1, QTableWidgetItem(tipo))
            self.tabela.setItem(row, 2, QTableWidgetItem(data))
            self.tabela.setItem(row, 3, QTableWidgetItem(stat))

    def _vincular(self):
        row = self.tabela.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione um exame.")
            return
        self.exame_id_selecionado = int(self.tabela.item(row, 0).text())
        self.accept()
