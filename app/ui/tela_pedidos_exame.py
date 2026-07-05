from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QLabel,
    QMessageBox, QHeaderView, QComboBox
)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt
from app.database.connection import SessionLocal
from app.services.pedido_exame_service import PedidoExameService
from app.models.pedido_exame import StatusPedido

STATUS_CORES = {
    "solicitado": "#f39c12",
    "agendado"  : "#3498db",
    "realizado" : "#2ecc71",
    "cancelado" : "#e74c3c",
}
STATUS_LABELS = {
    "solicitado": "Solicitado",
    "agendado"  : "Agendado",
    "realizado" : "Realizado",
    "cancelado" : "Cancelado",
}


class TelaPedidosExame(QWidget):
    def __init__(self):
        super().__init__()
        self.db      = SessionLocal()
        self.service = PedidoExameService(self.db)
        self._setup_ui()
        self._carregar()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(15, 15, 15, 15)

        titulo = QLabel("📋 Pedidos de Exame")
        titulo.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        titulo.setFixedHeight(30)
        layout.addWidget(titulo)

        # Filtros
        filtros = QHBoxLayout()
        self.combo_status = QComboBox()
        self.combo_status.setFixedHeight(32)
        self.combo_status.addItem("Todos os status", None)
        for s in StatusPedido:
            self.combo_status.addItem(STATUS_LABELS[s.value], s)
        self.combo_status.currentIndexChanged.connect(self._carregar)
        filtros.addWidget(QLabel("Status:"))
        filtros.addWidget(self.combo_status)
        filtros.addStretch()
        layout.addLayout(filtros)

        # Tabela
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(10)
        self.tabela.setHorizontalHeaderLabels([
            "ID", "Paciente", "Médico", "Tipo de Exame",
            "Urgente", "Status", "Exame Agendado", "Documento", "Observações", "Criado Em"
        ])
        header = self.tabela.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.tabela.setColumnWidth(0, 45)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.tabela.setColumnWidth(4, 65)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)
        self.tabela.setColumnWidth(5, 100)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Interactive)
        self.tabela.setColumnWidth(6, 130)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        self.tabela.setColumnWidth(7, 80)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Interactive)
        self.tabela.setColumnWidth(8, 180)
        header.setSectionResizeMode(9, QHeaderView.ResizeMode.Interactive)
        self.tabela.setColumnWidth(9, 120)
        self.tabela.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabela.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabela.setAlternatingRowColors(True)
        self.tabela.setStyleSheet("""
            QTableWidget {
                background-color: #eaf4fb;
                alternate-background-color: #d6eaf8;
                gridline-color: #aed6f1;
            }
            QHeaderView::section {
                background-color: #16a085;
                color: white;
                font-weight: bold;
                padding: 4px;
                border: none;
            }
        """)
        layout.addWidget(self.tabela)

        # Rodapé
        rodape = QHBoxLayout()
        btn_novo          = QPushButton("➕ Novo Pedido")
        btn_editar        = QPushButton("✏️ Editar")
        btn_agendar_novo  = QPushButton("📅 Agendar Exame")
        btn_vincular      = QPushButton("🔗 Vincular Exame Existente")
        btn_desvincular   = QPushButton("✂️ Desvincular")
        btn_cancelar      = QPushButton("❌ Cancelar Pedido")
        btn_atualizar     = QPushButton("🔃 Atualizar")

        for btn in [btn_novo, btn_editar, btn_agendar_novo, btn_vincular, btn_desvincular, btn_cancelar]:
            btn.setFixedHeight(32)
            rodape.addWidget(btn)

        btn_novo.clicked.connect(self._novo_pedido)
        btn_editar.clicked.connect(self._editar_pedido)
        btn_agendar_novo.clicked.connect(self._agendar_novo_exame)
        btn_vincular.clicked.connect(self._vincular_exame)
        btn_desvincular.clicked.connect(self._desvincular_exame)
        btn_cancelar.clicked.connect(self._cancelar_pedido)
        btn_atualizar.clicked.connect(self._atualizar)

        rodape.addStretch()
        btn_atualizar.setFixedHeight(32)
        btn_atualizar.setStyleSheet("""
            QPushButton { background-color:#16a085; color:white;
                          border-radius:4px; font-weight:bold; }
            QPushButton:hover { background-color:#1abc9c; }
        """)
        rodape.addWidget(btn_atualizar)
        layout.addLayout(rodape)

    def _carregar(self):
        status = self.combo_status.currentData()
        pedidos = self.service.filtrar(status=status)
        self.tabela.setRowCount(0)
        for p in pedidos:
            row = self.tabela.rowCount()
            self.tabela.insertRow(row)
            tipo     = p.tipo_exame.nome if p.tipo_exame else "—"
            urgente  = "⚠️ Sim" if p.urgente else "Não"
            status_v = p.status.value if p.status else ""
            cor      = STATUS_CORES.get(status_v, "#ffffff")
            agendado = ""
            if p.exame and p.exame.data_hora:
                agendado = p.exame.data_hora.strftime("%d/%m/%Y %H:%M")

            criado_em = p.criado_em.strftime("%d/%m/%Y %H:%M") if p.criado_em else ""

            tem_doc = bool(p.documento_path)
            item_doc = QTableWidgetItem("✅" if tem_doc else "✖")
            item_doc.setForeground(QColor("#27ae60" if tem_doc else "#95a5a6"))
            item_doc.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if tem_doc:
                item_doc.setToolTip(p.documento_path)

            self.tabela.setItem(row, 0, QTableWidgetItem(str(p.id)))
            self.tabela.setItem(row, 1, QTableWidgetItem(p.paciente.nome if p.paciente else "—"))
            self.tabela.setItem(row, 2, QTableWidgetItem(p.medico.nome   if p.medico   else "—"))
            self.tabela.setItem(row, 3, QTableWidgetItem(tipo))
            self.tabela.setItem(row, 4, QTableWidgetItem(urgente))
            self.tabela.setItem(row, 5, QTableWidgetItem(STATUS_LABELS.get(status_v, status_v)))
            self.tabela.setItem(row, 6, QTableWidgetItem(agendado))
            self.tabela.setItem(row, 7, item_doc)
            self.tabela.setItem(row, 8, QTableWidgetItem(p.observacoes or ""))
            self.tabela.setItem(row, 9, QTableWidgetItem(criado_em))

            for col in range(self.tabela.columnCount()):
                item = self.tabela.item(row, col)
                if item:
                    if col == 5:
                        item.setBackground(QColor(cor))
                        item.setForeground(QColor("#ffffff"))
                    else:
                        item.setBackground(QColor("#eaf4fb" if row % 2 == 0 else "#d6eaf8"))

    def _selecionado(self):
        row = self.tabela.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione um pedido.")
            return None
        p_id = int(self.tabela.item(row, 0).text())
        return self.service.buscar_por_id(p_id)

    def _novo_pedido(self):
        from app.ui.components.dialogs.dialog_pedido_exame import DialogPedidoExame
        dlg = DialogPedidoExame(self.db, consulta=None, pedido=None, parent=self)
        if dlg.exec():
            self.db.expire_all()
            self._carregar()

    def _editar_pedido(self):
        pedido = self._selecionado()
        if not pedido:
            return
        from app.ui.components.dialogs.dialog_pedido_exame import DialogPedidoExame
        # Passa a consulta do pedido para o dialog
        consulta = pedido.consulta
        dlg = DialogPedidoExame(self.db, consulta, pedido=pedido, parent=self)
        if dlg.exec():
            self.db.expire_all()
            self._carregar()

    def _agendar_novo_exame(self):
        pedido = self._selecionado()
        if not pedido:
            return
        from app.ui.components.dialogs.dialog_exame import DialogExame
        dados_iniciais = {
            "paciente_id"  : pedido.paciente_id,
            "medico_id"    : pedido.medico_id,
            "tipo_exame_id": pedido.tipo_exame_id,
            "consulta_id"  : pedido.consulta_id,
        }
        dlg = DialogExame(self.db, dados_iniciais=dados_iniciais)
        if dlg.exec() and dlg.exame_criado:
            self.service.vincular_exame(pedido.id, dlg.exame_criado.id)
            self._carregar()

    def _vincular_exame(self):
        pedido = self._selecionado()
        if not pedido:
            return
        from app.ui.components.dialogs.dialog_vincular_exame import DialogVincularExame
        # Cria consulta fake apenas para passar o paciente_id ao dialog
        class _FakeConsulta:
            def __init__(self, p):
                self.paciente_id = p.paciente_id
                self.paciente    = p.paciente
        dlg = DialogVincularExame(self.db, _FakeConsulta(pedido), parent=self)
        if dlg.exec() and dlg.exame_id_selecionado:
            self.service.vincular_exame(pedido.id, dlg.exame_id_selecionado)
            self._carregar()

    def _desvincular_exame(self):
        pedido = self._selecionado()
        if not pedido or not pedido.exame_id:
            QMessageBox.information(self, "Atenção", "Este pedido não tem exame vinculado.")
            return
        resp = QMessageBox.question(self, "Confirmar",
            "Desvincular o exame deste pedido?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if resp == QMessageBox.StandardButton.Yes:
            self.service.desvincular_exame(pedido.id)
            self._carregar()

    def _cancelar_pedido(self):
        pedido = self._selecionado()
        if not pedido:
            return
        resp = QMessageBox.question(self, "Confirmar",
            "Cancelar este pedido de exame?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if resp == QMessageBox.StandardButton.Yes:
            self.service.cancelar(pedido.id)
            self._carregar()

    def _atualizar(self):
        self.db.rollback()    # ← encerra transação para ver dados novos (REPEATABLE READ)
        self.db.expire_all()
        self._carregar()
