from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QLabel,
    QMessageBox, QHeaderView, QComboBox, QDateEdit, QSizePolicy
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor
from app.database.connection import SessionLocal
from app.services.exame_service import ExameService
from app.services.paciente_service import PacienteService
from app.models.exame import StatusExame
from app.ui.components.dialogs.dialog_exame import DialogExame
from app.ui.components.dialogs.dialog_resultado import DialogResultado



STATUS_CORES = {
    "a_marcar" : "#f39c12",
    "agendado" : "#3498db",
    "realizado": "#2ecc71",
    "cancelado": "#e74c3c",
}

STATUS_LABELS = {
    "a_marcar" : "A Marcar",
    "agendado" : "Agendado",
    "realizado": "Realizado",
    "cancelado": "Cancelado",
}


class TelaExames(QWidget):
    def __init__(self):
        super().__init__()
        self.db               = SessionLocal()
        self.service          = ExameService(self.db)
        self.service_paciente = PacienteService(self.db)
        self._setup_ui()
        self._carregar_exames()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(15, 15, 15, 15)

        titulo = QLabel("🧪 Exames")
        titulo.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        titulo.setFixedHeight(30)
        layout.addWidget(titulo)

        layout.addLayout(self._criar_filtros())
        layout.addWidget(self._criar_tabela())
        layout.addLayout(self._criar_rodape())

    def _criar_filtros(self):
        layout_filtros = QVBoxLayout()

        linha1 = QHBoxLayout()

        self.input_busca = QLineEdit()
        self.input_busca.setPlaceholderText("🔍 Buscar paciente...")
        self.input_busca.setFixedHeight(32)
        self.input_busca.textChanged.connect(self._aplicar_filtros)

        self.combo_status = QComboBox()
        self.combo_status.setFixedHeight(32)
        self.combo_status.addItem("Todos os status", None)
        for s in StatusExame:
            self.combo_status.addItem(STATUS_LABELS.get(s.value, s.value.capitalize()), s)
        self.combo_status.currentIndexChanged.connect(self._aplicar_filtros)

        linha1.addWidget(self.input_busca)
        linha1.addWidget(self.combo_status)

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

    def _criar_tabela(self):
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(8)
        self.tabela.setHorizontalHeaderLabels([
            "ID", "Paciente", "Médico", "Tipo de Exame", "Local", "Data/Hora", "Status", "Resultado"
        ])
        header = self.tabela.horizontalHeader()
        # Col 0 – ID: fixa e estreita
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.tabela.setColumnWidth(0, 45)
        # Col 1 – Paciente: estica e absorve o espaço extra
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        # Demais colunas: tamanho interativo
        for col in range(2, 8):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)
        self.tabela.setColumnWidth(2, 200)   # Médico
        self.tabela.setColumnWidth(3, 200)   # Tipo de Exame
        self.tabela.setColumnWidth(4, 150)   # Local
        self.tabela.setColumnWidth(5, 130)   # Data/Hora
        self.tabela.setColumnWidth(6, 90)    # Status
        self.tabela.setColumnWidth(7, 220)   # Resultado
        self.tabela.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabela.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabela.setAlternatingRowColors(True)
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
        return self.tabela

    def _criar_rodape(self):
        rodape = QHBoxLayout()

        btn_novo    = QPushButton("➕ Novo Exame")
        btn_editar  = QPushButton("✏️ Editar")
        btn_deletar = QPushButton("🗑️ Deletar")
        btn_atualizar = QPushButton("🔃 Atualizar")

        btn_novo.clicked.connect(self._abrir_dialog_novo)
        btn_editar.clicked.connect(self._abrir_dialog_editar)
        btn_deletar.clicked.connect(self._deletar)
        btn_atualizar.clicked.connect(self._atualizar)

        btn_resultado = QPushButton("📄 Ver Resultado")
        btn_resultado.setFixedHeight(32)
        btn_resultado.clicked.connect(self._ver_resultado)
        rodape.addWidget(btn_resultado)

        for btn in [btn_novo, btn_editar, btn_deletar]:
            btn.setFixedHeight(32)
            rodape.addWidget(btn)

        rodape.addStretch()
        btn_atualizar.setFixedHeight(32)
        btn_atualizar.setStyleSheet("""
            QPushButton {
                background-color: #2980b9;
                color: white;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #21618c; }
        """)
        rodape.addWidget(btn_atualizar)
        return rodape

    def _ver_resultado(self):
        exame = self._exame_selecionado()
        if not exame:
            return
        dlg = DialogResultado(
            resultado=exame.resultado or "",
            editavel=False,   # ← só leitura na tela de exames
            parent=self
        )
        dlg.exec()



    def _criar_legenda(self):
        from PyQt6.QtWidgets import QFrame, QGridLayout
        legenda = QFrame()
        grid    = QGridLayout(legenda)
        grid.setSpacing(4)

        for i, (status, cor) in enumerate(STATUS_CORES.items()):
            caixa = QLabel()
            caixa.setFixedSize(14, 14)
            caixa.setStyleSheet(f"background-color: {cor}; border-radius: 3px;")
            lbl = QLabel(STATUS_LABELS.get(status, status.capitalize()))
            lbl.setStyleSheet("font-size: 11px;")
            grid.addWidget(caixa, i, 0)
            grid.addWidget(lbl,   i, 1)

        return legenda

    # ── Carregar / Filtrar ─────────────────────────────
    def _carregar_exames(self, exames=None):
        if exames is None:
            exames = self.service.buscar_todos()

        self.tabela.setRowCount(0)

        for e in exames:
            row = self.tabela.rowCount()
            self.tabela.insertRow(row)

            data_str  = e.data_hora.strftime("%d/%m/%Y %H:%M") if e.data_hora else ""
            status    = e.status.value if e.status else ""
            cor       = STATUS_CORES.get(status, "#ffffff")
            tipo_nome = e.tipo_exame.nome if e.tipo_exame else "—"
            local_nom = e.local.nome      if e.local      else "—"
            tem_resultado = bool(e.resultado and e.resultado.strip())
            tem_anexo     = bool(e.anexos)
            if tem_resultado and tem_anexo:
                resultado = "📝 Resultado  📎 Anexo"
            elif tem_resultado:
                resultado = "📝 Resultado"
            elif tem_anexo:
                resultado = "📎 Anexo"
            else:
                resultado = "Vazio"
            medico_nom = e.medico.nome if e.medico else "—"       # ← novo

            self.tabela.setItem(row, 0, QTableWidgetItem(str(e.id)))
            self.tabela.setItem(row, 1, QTableWidgetItem(e.paciente.nome if e.paciente else "—"))
            self.tabela.setItem(row, 2, QTableWidgetItem(medico_nom))      # ← novo
            self.tabela.setItem(row, 3, QTableWidgetItem(tipo_nome))
            self.tabela.setItem(row, 4, QTableWidgetItem(local_nom))
            self.tabela.setItem(row, 5, QTableWidgetItem(data_str))
            self.tabela.setItem(row, 6, QTableWidgetItem(STATUS_LABELS.get(status, status.capitalize())))
            self.tabela.setItem(row, 7, QTableWidgetItem(resultado))

            for col in range(self.tabela.columnCount()):
                item = self.tabela.item(row, col)
                if item:
                    if col == 6:  # coluna Status
                        item.setBackground(QColor(cor))
                        item.setForeground(QColor("#ffffff"))
                    elif col == 7:  # coluna Resultado
                        if tem_resultado or tem_anexo:
                            item.setBackground(QColor("#d5f5e3"))   # verde claro
                            item.setForeground(QColor("#1a7a3c"))
                        else:
                            item.setBackground(QColor("#f2f3f4"))   # cinza claro
                            item.setForeground(QColor("#999999"))
                    else:
                        bg = "#eaf4fb" if row % 2 == 0 else "#d6eaf8"
                        item.setBackground(QColor(bg))

    def _aplicar_filtros(self):
        texto     = self.input_busca.text().strip() or None
        status    = self.combo_status.currentData()
        dt_inicio = self.data_inicio.date().toPyDate()
        dt_fim    = self.data_fim.date().toPyDate()
        exames    = self.service.filtrar(
            texto=texto, status=status,
            dt_inicio=dt_inicio, dt_fim=dt_fim
        )
        self._carregar_exames(exames)

    def _filtrar_por_periodo(self, dt_inicio, dt_fim):
        self.data_inicio.setDate(QDate(dt_inicio.year, dt_inicio.month, dt_inicio.day))
        self.data_fim.setDate(QDate(dt_fim.year, dt_fim.month, dt_fim.day))
        self._aplicar_filtros()

    def _filtrar_por_calendario_data(self, qdate: QDate):
        data = qdate.toPyDate()
        self.data_inicio.setDate(qdate)
        self.data_fim.setDate(qdate)
        exames = self.service.filtrar(dt_inicio=data, dt_fim=data)
        self._carregar_exames(exames)

    def _limpar_filtros(self):
        self.input_busca.clear()
        self.combo_status.setCurrentIndex(0)
        self.data_inicio.setDate(QDate.currentDate().addMonths(-1))
        self.data_fim.setDate(QDate.currentDate().addMonths(1))
        self._carregar_exames()

    def _atualizar(self):
        self.db.rollback()    # ← encerra transação para ver dados novos (REPEATABLE READ)
        self.db.expire_all()
        self._limpar_filtros()

    # ── Dialogs ───────────────────────────────────────
    def _abrir_dialog_novo(self):
        dlg = DialogExame(self.db)
        if dlg.exec():
            self._carregar_exames()

    def _abrir_dialog_editar(self):
        exame = self._exame_selecionado()
        if not exame:
            return
        dlg = DialogExame(self.db, exame=exame)
        if dlg.exec():
            self._carregar_exames()

    def _deletar(self):
        exame = self._exame_selecionado()
        if not exame:
            return
        resp = QMessageBox.question(
            self, "Confirmar",
            f"Deletar exame de {exame.paciente.nome}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if resp == QMessageBox.StandardButton.Yes:
            self.service.deletar(exame.id)
            self._carregar_exames()

    def _exame_selecionado(self):
        row = self.tabela.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione um exame.")
            return None
        id_item = self.tabela.item(row, 0)
        if not id_item:
            return None
        return self.service.buscar_por_id(int(id_item.text()))
