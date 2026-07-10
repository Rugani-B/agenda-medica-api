# app/ui/components/dialogs/dialog_consulta.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QComboBox,
    QDateTimeEdit, QTextEdit, QDialogButtonBox,
    QMessageBox, QLabel, QTabWidget, QWidget,
    QTableWidget, QTableWidgetItem, QHBoxLayout,
    QPushButton, QHeaderView
)
from PyQt6.QtCore import QDateTime, Qt
from PyQt6.QtGui import QFont
from app.services.consulta_service import ConsultaService
from app.services.medico_service import MedicoService
from app.services.paciente_service import PacienteService
from app.services.prescricao_service import PrescricaoService
from app.services.exame_service import ExameService
from app.services.pedido_exame_service import PedidoExameService
from app.models.pedido_exame import StatusPedido
from app.models.consulta import StatusConsulta


class DialogConsulta(QDialog):
    def __init__(self, db, consulta=None, reagendar=False):
        super().__init__()
        self.db        = db
        self.consulta  = consulta
        self.reagendar = reagendar
        self.service          = ConsultaService(db)
        self.service_medico   = MedicoService(db)
        self.service_paciente = PacienteService(db)
        self.service_prescricao = PrescricaoService(db)
        self.service_exame      = ExameService(db)
        self.service_pedido     = PedidoExameService(db)

        db.expire_all()

        self._setup_ui()
        if consulta:
            self._preencher_dados()

    def _setup_ui(self):
        if self.reagendar:
            titulo = "🔄 Reagendar Consulta"
        elif self.consulta:
            titulo = "✏️ Editar Consulta"
        else:
            titulo = "➕ Nova Consulta"

        self.setWindowTitle(titulo)
        self.setMinimumSize(700, 550)

        layout = QVBoxLayout(self)

        # Aviso reagendamento
        if self.reagendar:
            aviso = QLabel("⚠️ A data anterior será salva no histórico.")
            aviso.setStyleSheet("color: orange;")
            layout.addWidget(aviso)

        # ── Abas ──────────────────────────────────────
        self.tabs = QTabWidget()
        self.tabs.addTab(self._aba_dados(),       "📋 Dados")
        self.tabs.addTab(self._aba_prescricoes(), "💊 Prescrições")
        self.tabs.addTab(self._aba_pedidos(),     "🧪 Pedidos de Exame")
        layout.addWidget(self.tabs)

        # Faixa de confirmação pelo familiar
        if self.consulta:
            self._faixa_confirmacao = self._criar_faixa_confirmacao()
            if self._faixa_confirmacao:
                layout.addWidget(self._faixa_confirmacao)

        # Botões
        botoes = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        botoes.accepted.connect(self._salvar)
        botoes.rejected.connect(self.reject)
        layout.addWidget(botoes)

    # ── Aba Dados ──────────────────────────────────────
    def _aba_dados(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        form   = QFormLayout()

        self.combo_paciente = QComboBox()
        self.combo_paciente.addItem("— Selecione —", None)
        for p in self.service_paciente.buscar_ativos():
            self.combo_paciente.addItem(p.nome, p.id)

        self.combo_medico = QComboBox()
        self.combo_medico.addItem("— Selecione —", None)
        for m in self.service_medico.buscar_todos():
            self.combo_medico.addItem(m.nome, m.id)

        self.input_data_hora = QDateTimeEdit()
        self.input_data_hora.setCalendarPopup(True)
        self.input_data_hora.setDateTime(QDateTime.currentDateTime())
        self.input_data_hora.setDisplayFormat("dd/MM/yyyy HH:mm")

        self.combo_status = QComboBox()
        for s in StatusConsulta:
            self.combo_status.addItem(s.value.capitalize(), s)

        self.input_obs = QTextEdit()
        self.input_obs.setPlaceholderText("Observações...")
        self.input_obs.setMaximumHeight(80)

        form.addRow("Paciente: *",  self.combo_paciente)
        form.addRow("Médico: *",    self.combo_medico)
        form.addRow("Data/Hora: *", self.input_data_hora)
        form.addRow("Status:",      self.combo_status)
        form.addRow("Observações:", self.input_obs)

        layout.addLayout(form)
        layout.addStretch()
        return widget

    # ── Aba Prescrições ────────────────────────────────
    def _aba_prescricoes(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        aviso = QLabel("ℹ️ Salve a consulta antes de adicionar prescrições.")
        aviso.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(aviso)

        self.tabela_prescricoes = QTableWidget()
        self.tabela_prescricoes.setColumnCount(3)
        self.tabela_prescricoes.setHorizontalHeaderLabels(["ID", "Data", "Observações"])
        h = self.tabela_prescricoes.horizontalHeader()
        h.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.tabela_prescricoes.setColumnWidth(0, 45)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self.tabela_prescricoes.setColumnWidth(1, 130)
        self.tabela_prescricoes.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabela_prescricoes.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabela_prescricoes.setMinimumHeight(160)
        self.tabela_prescricoes.doubleClicked.connect(self._editar_prescricao)
        layout.addWidget(self.tabela_prescricoes)

        btn_layout = QHBoxLayout()
        btn_nova   = QPushButton("➕ Nova Prescrição")
        btn_editar = QPushButton("✏️ Editar")
        btn_del    = QPushButton("🗑️ Remover")
        for btn in [btn_nova, btn_editar, btn_del]:
            btn.setFixedHeight(30)
            btn_layout.addWidget(btn)
        btn_layout.addStretch()
        btn_nova.clicked.connect(self._nova_prescricao)
        btn_editar.clicked.connect(self._editar_prescricao)
        btn_del.clicked.connect(self._remover_prescricao)
        layout.addLayout(btn_layout)

        return widget

    # ── Aba Pedidos de Exame ───────────────────────────
    def _aba_pedidos(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.tabela_pedidos = QTableWidget()
        self.tabela_pedidos.setColumnCount(5)
        self.tabela_pedidos.setHorizontalHeaderLabels(
            ["ID", "Tipo de Exame", "Urgente", "Status", "Exame Agendado"]
        )
        h = self.tabela_pedidos.horizontalHeader()
        h.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.tabela_pedidos.setColumnWidth(0, 45)
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.tabela_pedidos.setColumnWidth(2, 65)
        h.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        self.tabela_pedidos.setColumnWidth(3, 100)
        self.tabela_pedidos.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabela_pedidos.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabela_pedidos.setMinimumHeight(160)
        self.tabela_pedidos.doubleClicked.connect(self._editar_pedido)
        layout.addWidget(self.tabela_pedidos)

        btn_layout = QHBoxLayout()
        btn_novo        = QPushButton("➕ Novo Pedido")
        btn_editar      = QPushButton("✏️ Editar")
        btn_novo_exame  = QPushButton("📅 Agendar (Novo Exame)")
        btn_vincular    = QPushButton("🔗 Vincular Exame Existente")
        btn_desvincular = QPushButton("✂️ Desvincular")
        btn_remover     = QPushButton("🗑️ Remover")

        for btn in [btn_novo, btn_editar, btn_novo_exame,
                    btn_vincular, btn_desvincular, btn_remover]:
            btn.setFixedHeight(30)
            btn_layout.addWidget(btn)
        btn_layout.addStretch()

        btn_novo.clicked.connect(self._novo_pedido)
        btn_editar.clicked.connect(self._editar_pedido)
        btn_novo_exame.clicked.connect(self._agendar_novo_exame)
        btn_vincular.clicked.connect(self._vincular_exame_pedido)
        btn_desvincular.clicked.connect(self._desvincular_exame_pedido)
        btn_remover.clicked.connect(self._remover_pedido)
        layout.addLayout(btn_layout)

        return widget

    # ── Faixa de confirmação pelo familiar ────────────
    def _criar_faixa_confirmacao(self):
        from app.models.confirmacao import Confirmacao, StatusConfirmacao
        try:
            cf = self.db.query(Confirmacao).filter(
                Confirmacao.consulta_id == self.consulta.id,
                Confirmacao.status == StatusConfirmacao.realizada,
            ).first()
        except Exception:
            return None
        if not cf:
            return None

        frame = QWidget()
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(10, 6, 10, 6)
        frame.setStyleSheet(
            "background:#e8f8e8; border-radius:6px; border: 1px solid #a8d8a8;"
        )
        data_str = cf.respondido_em.strftime("%d/%m/%Y às %H:%M") if cf.respondido_em else ""
        nome = cf.respondido or "Familiar"
        lbl = QLabel(f"✅  Confirmada pelo familiar  ·  {nome}  ·  {data_str}")
        lbl.setStyleSheet("color:#1a7a1a; font-size:12px; font-weight:bold;")
        lay.addWidget(lbl)
        return frame

    # ── Preencher dados ────────────────────────────────
    def _preencher_dados(self):
        c = self.consulta

        idx = self.combo_paciente.findData(c.paciente_id)
        if idx >= 0:
            self.combo_paciente.setCurrentIndex(idx)

        idx = self.combo_medico.findData(c.medico_id)
        if idx >= 0:
            self.combo_medico.setCurrentIndex(idx)

        if c.data_hora:
            self.input_data_hora.setDateTime(
                QDateTime(c.data_hora.date(), c.data_hora.time())
            )

        # Compara pelo valor string para evitar divergência entre StatusConsulta e StatusAgendamento
        status_val = c.status.value if c.status else None
        for i in range(self.combo_status.count()):
            if self.combo_status.itemData(i) and self.combo_status.itemData(i).value == status_val:
                self.combo_status.setCurrentIndex(i)
                break

        self.input_obs.setText(c.observacoes or "")
        self._carregar_prescricoes()
        self._carregar_pedidos()

    def _carregar_prescricoes(self):
        self.tabela_prescricoes.setRowCount(0)
        if not self.consulta:
            return
        for p in self.service_prescricao.buscar_por_consulta(self.consulta.id):
            row = self.tabela_prescricoes.rowCount()
            self.tabela_prescricoes.insertRow(row)
            data_str = p.criado_em.strftime("%d/%m/%Y %H:%M") if p.criado_em else ""
            self.tabela_prescricoes.setItem(row, 0, QTableWidgetItem(str(p.id)))
            self.tabela_prescricoes.setItem(row, 1, QTableWidgetItem(data_str))
            self.tabela_prescricoes.setItem(row, 2, QTableWidgetItem(p.observacoes or ""))

    def _carregar_pedidos(self):
        self.tabela_pedidos.setRowCount(0)
        if not self.consulta:
            return
        STATUS_LABELS = {
            "solicitado": "Solicitado", "agendado": "Agendado",
            "realizado": "Realizado",   "cancelado": "Cancelado",
        }
        for p in self.service_pedido.buscar_por_consulta(self.consulta.id):
            row = self.tabela_pedidos.rowCount()
            self.tabela_pedidos.insertRow(row)
            tipo     = p.tipo_exame.nome if p.tipo_exame else "—"
            urgente  = "⚠️ Sim" if p.urgente else "Não"
            status   = STATUS_LABELS.get(p.status.value if p.status else "", "—")
            agendado = ""
            if p.exame:
                data = p.exame.data_hora.strftime("%d/%m/%Y %H:%M") if p.exame.data_hora else ""
                agendado = f"{p.exame.tipo_exame.nome if p.exame.tipo_exame else ''} {data}".strip()
            self.tabela_pedidos.setItem(row, 0, QTableWidgetItem(str(p.id)))
            self.tabela_pedidos.setItem(row, 1, QTableWidgetItem(tipo))
            self.tabela_pedidos.setItem(row, 2, QTableWidgetItem(urgente))
            self.tabela_pedidos.setItem(row, 3, QTableWidgetItem(status))
            self.tabela_pedidos.setItem(row, 4, QTableWidgetItem(agendado))

    # ── Ações Prescrições ──────────────────────────────
    def _nova_prescricao(self):
        if not self.consulta:
            QMessageBox.information(self, "Atenção",
                                    "Salve a consulta antes de adicionar prescrições.")
            return
        from app.ui.components.dialogs.dialog_prescricao import DialogPrescricao
        dlg = DialogPrescricao(self.db, self.consulta, parent=self)
        if dlg.exec():
            self._carregar_prescricoes()

    def _editar_prescricao(self):
        if not self.consulta:
            return
        row = self.tabela_prescricoes.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione uma prescrição.")
            return
        p_id = int(self.tabela_prescricoes.item(row, 0).text())
        prescricao = self.service_prescricao.buscar_por_id(p_id)
        from app.ui.components.dialogs.dialog_prescricao import DialogPrescricao
        dlg = DialogPrescricao(self.db, self.consulta, prescricao=prescricao, parent=self)
        if dlg.exec():
            self._carregar_prescricoes()

    def _remover_prescricao(self):
        row = self.tabela_prescricoes.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione uma prescrição.")
            return
        p_id = int(self.tabela_prescricoes.item(row, 0).text())
        resp = QMessageBox.question(self, "Confirmar",
            "Remover esta prescrição e todos os seus medicamentos?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if resp == QMessageBox.StandardButton.Yes:
            self.service_prescricao.deletar(p_id)
            self._carregar_prescricoes()

    # ── Ações Pedidos ──────────────────────────────────
    def _pedido_selecionado(self):
        row = self.tabela_pedidos.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione um pedido.")
            return None
        p_id = int(self.tabela_pedidos.item(row, 0).text())
        return self.service_pedido.buscar_por_id(p_id)

    def _novo_pedido(self):
        if not self.consulta:
            QMessageBox.information(self, "Atenção", "Salve a consulta antes de adicionar pedidos.")
            return
        from app.ui.components.dialogs.dialog_pedido_exame import DialogPedidoExame
        dlg = DialogPedidoExame(self.db, self.consulta, parent=self)
        if dlg.exec():
            self._carregar_pedidos()

    def _editar_pedido(self):
        pedido = self._pedido_selecionado()
        if not pedido:
            return
        from app.ui.components.dialogs.dialog_pedido_exame import DialogPedidoExame
        dlg = DialogPedidoExame(self.db, self.consulta, pedido=pedido, parent=self)
        if dlg.exec():
            self._carregar_pedidos()

    def _agendar_novo_exame(self):
        """Abre DialogExame pré-preenchido e vincula ao pedido ao salvar."""
        pedido = self._pedido_selecionado()
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
            self.service_pedido.vincular_exame(pedido.id, dlg.exame_criado.id)
            self.db.expire_all()
            self._carregar_pedidos()

    def _vincular_exame_pedido(self):
        """Vincula um exame existente ao pedido selecionado."""
        pedido = self._pedido_selecionado()
        if not pedido:
            return
        from app.ui.components.dialogs.dialog_vincular_exame import DialogVincularExame
        dlg = DialogVincularExame(self.db, self.consulta, parent=self)
        if dlg.exec() and dlg.exame_id_selecionado:
            self.service_pedido.vincular_exame(pedido.id, dlg.exame_id_selecionado)
            self.db.expire_all()
            self._carregar_pedidos()

    def _desvincular_exame_pedido(self):
        pedido = self._pedido_selecionado()
        if not pedido:
            return
        if not pedido.exame_id:
            QMessageBox.information(self, "Atenção", "Este pedido não tem exame vinculado.")
            return
        resp = QMessageBox.question(self, "Confirmar",
            "Desvincular o exame deste pedido? O status voltará para 'Solicitado'.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if resp == QMessageBox.StandardButton.Yes:
            self.service_pedido.desvincular_exame(pedido.id)
            self._carregar_pedidos()

    def _remover_pedido(self):
        pedido = self._pedido_selecionado()
        if not pedido:
            return
        resp = QMessageBox.question(self, "Confirmar",
            "Remover este pedido de exame?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if resp == QMessageBox.StandardButton.Yes:
            self.service_pedido.deletar(pedido.id)
            self._carregar_pedidos()

    # ── Salvar ─────────────────────────────────────────
    def _salvar(self):
        paciente_id = self.combo_paciente.currentData()
        medico_id   = self.combo_medico.currentData()

        if not paciente_id:
            QMessageBox.warning(self, "Atenção", "Selecione um paciente.")
            return
        if not medico_id:
            QMessageBox.warning(self, "Atenção", "Selecione um médico.")
            return

        dados = {
            "paciente_id": paciente_id,
            "medico_id"  : medico_id,
            "data_hora"  : self.input_data_hora.dateTime().toPyDateTime(),
            "status"     : self.combo_status.currentData(),
            "observacoes": self.input_obs.toPlainText().strip() or None,
        }

        try:
            if self.reagendar:
                self.service.reagendar(self.consulta.id,
                                       self.input_data_hora.dateTime().toPyDateTime())
            elif self.consulta:
                self.service.atualizar(self.consulta.id, dados)
            else:
                self.consulta = self.service.cadastrar(dados)
            self.accept()
        except ValueError as e:
            QMessageBox.critical(self, "Erro", str(e))
