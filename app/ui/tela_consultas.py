# app/ui/tela_consultas.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QLabel,
    QMessageBox, QHeaderView, QComboBox, QDateEdit,
    QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor

from app.database.connection import SessionLocal
from app.services.consulta_service import ConsultaService
from app.services.medico_service import MedicoService
from app.services.paciente_service import PacienteService
from app.ui.components.dialogs.dialog_consulta import DialogConsulta
from app.models.consulta import StatusConsulta


STATUS_CORES = {
    "agendada"  : "#3498db",
    "confirmada": "#2ecc71",
    "reagendada": "#f39c12",
    "cancelada" : "#e74c3c",
    "realizada" : "#95a5a6",
}


class TelaConsultas(QWidget):
    def __init__(self):
        super().__init__()
        self.db              = SessionLocal()
        self.service         = ConsultaService(self.db)
        self.service_medico  = MedicoService(self.db)
        self.service_paciente = PacienteService(self.db)
        self._setup_ui()
        self._carregar_consultas()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(15, 15, 15, 15)

        # Título
        titulo = QLabel("📅 Consultas")
        titulo.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        titulo.setFixedHeight(30)
        layout.addWidget(titulo)

        layout.addLayout(self._criar_filtros())
        layout.addWidget(self._criar_tabela())
        layout.addLayout(self._criar_rodape())

    # ── Filtros ────────────────────────────────────────
    def _criar_filtros(self):
        layout_filtros = QVBoxLayout()

        # Linha 1: busca + status + médico
        linha1 = QHBoxLayout()

        self.input_busca = QLineEdit()
        self.input_busca.setPlaceholderText("🔍 Buscar paciente...")
        self.input_busca.setFixedHeight(32)
        self.input_busca.textChanged.connect(self._aplicar_filtros)

        self.combo_status = QComboBox()
        self.combo_status.setFixedHeight(32)
        self.combo_status.addItem("Todos os status", None)
        for s in StatusConsulta:
            self.combo_status.addItem(s.value.capitalize(), s)
        self.combo_status.currentIndexChanged.connect(self._aplicar_filtros)

        self.combo_medico = QComboBox()
        self.combo_medico.setFixedHeight(32)
        self.combo_medico.addItem("Todos os médicos", None)
        for m in self.service_medico.buscar_todos ():
            self.combo_medico.addItem(m.nome, m.id)
        self.combo_medico.currentIndexChanged.connect(self._aplicar_filtros)

        linha1.addWidget(self.input_busca)
        linha1.addWidget(self.combo_status)
        linha1.addWidget(self.combo_medico)

        # Linha 2: data início + data fim + botão limpar
        linha2 = QHBoxLayout()

        lbl_de = QLabel("De:")
        self.data_inicio = QDateEdit()
        self.data_inicio.setCalendarPopup(True)
        self.data_inicio.setDate(QDate.currentDate().addMonths(-1))
        self.data_inicio.setFixedHeight(32)
        self.data_inicio.dateChanged.connect(self._aplicar_filtros)

        lbl_ate = QLabel("Até:")
        self.data_fim = QDateEdit()
        self.data_fim.setCalendarPopup(True)
        self.data_fim.setDate(QDate.currentDate().addMonths(1))
        self.data_fim.setFixedHeight(32)
        self.data_fim.dateChanged.connect(self._aplicar_filtros)

        btn_limpar = QPushButton("🔄 Limpar Filtros")
        btn_limpar.setFixedHeight(32)
        btn_limpar.clicked.connect(self._limpar_filtros)

        linha2.addWidget(lbl_de)
        linha2.addWidget(self.data_inicio)
        linha2.addWidget(lbl_ate)
        linha2.addWidget(self.data_fim)
        linha2.addStretch()
        linha2.addWidget(btn_limpar)

        layout_filtros.addLayout(linha1)
        layout_filtros.addLayout(linha2)

        return layout_filtros

    # ── Tabela ─────────────────────────────────────────
    def _criar_tabela(self):
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(9)
        self.tabela.setHorizontalHeaderLabels([
            "ID", "Paciente", "Médico", "Especialidade", "Data/Hora", "Status",
            "Prescrições", "Pedidos de Exame", "Observações"
        ])
        header = self.tabela.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.tabela.setColumnWidth(0, 45)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for col in range(2, self.tabela.columnCount()):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)
        self.tabela.setColumnWidth(2, 160)   # Médico
        self.tabela.setColumnWidth(3, 130)   # Especialidade
        self.tabela.setColumnWidth(4, 130)   # Data/Hora
        self.tabela.setColumnWidth(5, 100)   # Status
        self.tabela.setColumnWidth(6, 100)   # Prescrições
        self.tabela.setColumnWidth(7, 130)   # Pedidos de Exame
        self.tabela.setColumnWidth(8, 200)   # Observações
        self.tabela.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabela.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabela.doubleClicked.connect(self._abrir_dialog_editar)

        self.tabela.setStyleSheet("""
            QTableWidget {
                background-color: #eaf4fb;
                alternate-background-color: #d6eaf8;
                gridline-color: #aed6f1;
            }
            QHeaderView::section {
                background-color: #2980b9;
                color: white;
                font-weight: bold;
                padding: 4px;
                border: none;
            }
        """)
        self.tabela.setAlternatingRowColors(True)

        return self.tabela

    # ── Rodapé com ações ───────────────────────────────
    def _criar_rodape(self):
        rodape = QHBoxLayout()

        btn_nova      = QPushButton("➕ Nova Consulta")
        btn_editar    = QPushButton("✏️ Editar")
        btn_confirmar = QPushButton("✅ Confirmar")
        btn_reagendar = QPushButton("🔄 Reagendar")
        btn_cancelar  = QPushButton("❌ Cancelar")
        btn_realizada = QPushButton("🏁 Realizada")
        btn_atualizar = QPushButton("🔃 Atualizar")       # ← novo

        btn_nova.clicked.connect(self._abrir_dialog_novo)
        btn_editar.clicked.connect(self._abrir_dialog_editar)
        btn_confirmar.clicked.connect(lambda: self._mudar_status(StatusConsulta.confirmada))
        btn_reagendar.clicked.connect(self._abrir_dialog_reagendar)
        btn_cancelar.clicked.connect(lambda: self._mudar_status(StatusConsulta.cancelada))
        btn_realizada.clicked.connect(lambda: self._mudar_status(StatusConsulta.realizada))
        btn_atualizar.clicked.connect(self._atualizar)    # ← novo

        for btn in [btn_nova, btn_editar, btn_confirmar,
                    btn_reagendar, btn_cancelar, btn_realizada]:
            btn.setFixedHeight(32)
            rodape.addWidget(btn)

        # ✅ Atualizar separado à direita, com estilo diferente
        rodape.addStretch()
        btn_atualizar.setFixedHeight(32)
        btn_atualizar.setStyleSheet("""
            QPushButton {
                background-color: #2980b9;
                color: white;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #21618c;
            }
        """)
        rodape.addWidget(btn_atualizar)

        return rodape


    def _atualizar(self):
        """Recarrega as consultas direto do banco."""
        self.db.rollback()                # ← encerra a transação atual (REPEATABLE READ do MySQL
                                           #    mantinha o snapshot antigo mesmo com expire_all)
        self.db.expire_all()              # ← limpa cache da sessão SQLAlchemy
        self._limpar_filtros()            # ← reseta filtros (já recarrega a tabela)


    # ── Legenda ────────────────────────────────────────
    def _criar_legenda(self):
        frame = QFrame()
        layout = QVBoxLayout(frame)
        layout.setSpacing(4)

        lbl = QLabel("Legenda:")
        lbl.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        layout.addWidget(lbl)

        for status, cor in STATUS_CORES.items():
            linha = QHBoxLayout()
            quadrado = QLabel("  ")
            quadrado.setStyleSheet(f"background-color: {cor}; border-radius: 3px;")
            quadrado.setFixedSize(16, 16)
            texto = QLabel(status.capitalize())
            linha.addWidget(quadrado)
            linha.addWidget(texto)
            linha.addStretch()
            layout.addLayout(linha)

        return frame

    # ── Carregar / Filtrar ─────────────────────────────
    def _carregar_consultas(self, consultas=None):
        if consultas is None:
            consultas = sorted(self.service.buscar_todos(),
                               key=lambda c: c.data_hora or __import__('datetime').datetime.min)

        self.tabela.setRowCount(0)

        for c in consultas:
            row = self.tabela.rowCount()
            self.tabela.insertRow(row)

            data_str = c.data_hora.strftime("%d/%m/%Y %H:%M") if c.data_hora else ""
            status   = c.status.value if c.status else ""
            cor      = STATUS_CORES.get(status, "#ffffff")

            especialidade = (
                c.medico.especialidade.nome
                if c.medico and c.medico.especialidade else "—"
            )
            tem_prescricao = bool(c.prescricoes)
            tem_pedido     = bool(c.pedidos_exame)

            item_presc = QTableWidgetItem("✅" if tem_prescricao else "✖")
            item_presc.setForeground(QColor("#27ae60" if tem_prescricao else "#95a5a6"))
            item_presc.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            item_pedido = QTableWidgetItem("✅" if tem_pedido else "✖")
            item_pedido.setForeground(QColor("#27ae60" if tem_pedido else "#95a5a6"))
            item_pedido.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self.tabela.setItem(row, 0, QTableWidgetItem(str(c.id)))
            self.tabela.setItem(row, 1, QTableWidgetItem(c.paciente.nome if c.paciente else "—"))
            self.tabela.setItem(row, 2, QTableWidgetItem(c.medico.nome   if c.medico   else "—"))
            self.tabela.setItem(row, 3, QTableWidgetItem(especialidade))
            self.tabela.setItem(row, 4, QTableWidgetItem(data_str))
            self.tabela.setItem(row, 5, QTableWidgetItem(status.capitalize()))
            self.tabela.setItem(row, 6, item_presc)
            self.tabela.setItem(row, 7, item_pedido)
            self.tabela.setItem(row, 8, QTableWidgetItem(c.observacoes or ""))

            for col in range(self.tabela.columnCount()):
                item = self.tabela.item(row, col)
                if item:
                    if col == 5:  # coluna Status
                        item.setBackground(QColor(cor))
                        item.setForeground(QColor("#ffffff"))  # texto branco no status
                    else:
                        # Linhas alternadas em azul claro (preserva a cor da fonte já definida)
                        bg = "#eaf4fb" if row % 2 == 0 else "#d6eaf8"
                        item.setBackground(QColor(bg))

    def _aplicar_filtros(self):
        texto     = self.input_busca.text().strip()
        status    = self.combo_status.currentData()
        medico_id = self.combo_medico.currentData()

        # Suspende filtro de datas quando há busca por nome
        # ou quando o status é "realizada" (podem ser datas antigas)
        ignorar_datas = bool(texto) or (
            status is not None and status.value == "realizada"
        )
        if ignorar_datas:
            dt_ini = None
            dt_fim = None
        else:
            dt_ini = self.data_inicio.date().toPyDate()
            dt_fim = self.data_fim.date().toPyDate()

        try:
            consultas = self.service.filtrar(
                texto     = texto     or None,
                status    = status,
                medico_id = medico_id,
                dt_inicio = dt_ini,
                dt_fim    = dt_fim,
            )
        except Exception:
            self.db.rollback()
            consultas = self.service.filtrar(
                texto     = texto     or None,
                status    = status,
                medico_id = medico_id,
                dt_inicio = dt_ini,
                dt_fim    = dt_fim,
            )
        self._carregar_consultas(consultas)

    def _filtrar_por_periodo(self, dt_inicio, dt_fim):
        from PyQt6.QtCore import QDate
        self.data_inicio.setDate(QDate(dt_inicio.year, dt_inicio.month, dt_inicio.day))
        self.data_fim.setDate(QDate(dt_fim.year, dt_fim.month, dt_fim.day))
        self._aplicar_filtros()

    def _filtrar_por_calendario_data(self, qdate: QDate):
        self.data_inicio.setDate(qdate)
        self.data_fim.setDate(qdate)
        self._aplicar_filtros()

    def _limpar_filtros(self):
        self.input_busca.clear()
        self.combo_status.setCurrentIndex(0)
        self.combo_medico.setCurrentIndex(0)
        self.data_inicio.setDate(QDate.currentDate().addMonths(-1))
        self.data_fim.setDate(QDate.currentDate().addMonths(1))
        self._carregar_consultas()

    # ── Ações ──────────────────────────────────────────
    def _abrir_dialog_novo(self):
        dialog = DialogConsulta(self.db)
        if dialog.exec():
            self._carregar_consultas()

    def _abrir_dialog_editar(self):
        row = self.tabela.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione uma consulta.")
            return
        consulta_id = int(self.tabela.item(row, 0).text())
        consulta    = self.service.buscar_por_id(consulta_id)
        dialog      = DialogConsulta(self.db, consulta)
        if dialog.exec():
            self._carregar_consultas()

    def _mudar_status(self, novo_status: StatusConsulta):
        row = self.tabela.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione uma consulta.")
            return

        consulta_id = int(self.tabela.item(row, 0).text())
        paciente    = self.tabela.item(row, 1).text()

        resposta = QMessageBox.question(
            self, "Confirmar",
            f"Marcar consulta de '{paciente}' como '{novo_status.value}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if resposta == QMessageBox.StandardButton.Yes:
            self.service.atualizar_status(consulta_id, novo_status)
            self._carregar_consultas()

    def _abrir_dialog_reagendar(self):
        row = self.tabela.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione uma consulta.")
            return
        consulta_id = int(self.tabela.item(row, 0).text())
        consulta    = self.service.buscar_por_id(consulta_id)
        dialog      = DialogConsulta(self.db, consulta, reagendar=True)
        if dialog.exec():
            self._carregar_consultas()
