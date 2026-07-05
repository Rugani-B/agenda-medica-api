import os
import subprocess
import sys

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QComboBox,
    QDateTimeEdit, QTextEdit, QDialogButtonBox,
    QMessageBox, QPushButton, QHBoxLayout, QToolBar,
    QGroupBox, QListWidget, QListWidgetItem, QFileDialog,
    QAbstractItemView, QSizePolicy
)
from PyQt6.QtGui import QFont, QAction, QTextListFormat, QIcon
from PyQt6.QtCore import QDateTime, Qt
from app.services.exame_service import ExameService
from app.services.tipo_exame_service import TipoExameService
from app.services.local_exame_service import LocalExameService
from app.services.paciente_service import PacienteService
from app.services.anexo_exame_service import AnexoExameService
from app.models.exame import StatusExame
from app.ui.components.dialogs.dialog_tipo_exame  import DialogTipoExame
from app.ui.components.dialogs.dialog_local_exame import DialogLocalExame
from app.services.medico_service import MedicoService



class DialogExame(QDialog):
    def __init__(self, db, exame=None, dados_iniciais: dict = None):
        super().__init__()
        self.db               = db
        self.exame            = exame
        self.dados_iniciais   = dados_iniciais or {}
        self.exame_criado     = None   # preenchido após salvar novo exame
        self.service          = ExameService(db)
        self.service_tipo     = TipoExameService(db)
        self.service_local    = LocalExameService(db)
        self.service_paciente = PacienteService(db)
        self.service_medico   = MedicoService(db)
        self.service_anexo    = AnexoExameService(db)

        db.expire_all()

        self._setup_ui()
        if exame:
            self._preencher_dados()
        elif self.dados_iniciais:
            self._preencher_iniciais()

    def _setup_ui(self):

        self.setWindowTitle("✏️ Editar Exame" if self.exame else "➕ Novo Exame")
        self.setMinimumSize(700, 600)
        self.resize(900, 700)

        layout = QVBoxLayout(self)
        form   = QFormLayout()

        # ── Paciente ──────────────────────────────────
        self.combo_paciente = QComboBox()
        self.combo_paciente.addItem("— Selecione —", None)
        for p in self.service_paciente.buscar_ativos():
            self.combo_paciente.addItem(p.nome, p.id)

        # ── Médico ────────────────────────────────────
        self.combo_medico = QComboBox()
        self._popular_medicos()   # ← chama o método


        # ── Tipo de Exame + botão novo ─────────────────
        linha_tipo = QHBoxLayout()
        self.combo_tipo = QComboBox()
        self._popular_tipos()
        btn_novo_tipo = QPushButton("➕")
        btn_novo_tipo.setFixedWidth(32)
        btn_novo_tipo.setToolTip("Cadastrar novo tipo de exame")
        btn_novo_tipo.clicked.connect(self._novo_tipo)
        linha_tipo.addWidget(self.combo_tipo)
        linha_tipo.addWidget(btn_novo_tipo)

        # ── Local + botão novo ─────────────────────────
        linha_local = QHBoxLayout()
        self.combo_local = QComboBox()
        self._popular_locais()
        btn_novo_local = QPushButton("➕")
        btn_novo_local.setFixedWidth(32)
        btn_novo_local.setToolTip("Cadastrar novo local")
        btn_novo_local.clicked.connect(self._novo_local)
        linha_local.addWidget(self.combo_local)
        linha_local.addWidget(btn_novo_local)

        # ── Data/Hora ──────────────────────────────────
        self.input_data_hora = QDateTimeEdit()
        self.input_data_hora.setCalendarPopup(True)
        self.input_data_hora.setDateTime(QDateTime.currentDateTime())
        self.input_data_hora.setDisplayFormat("dd/MM/yyyy HH:mm")

        # ── Status ─────────────────────────────────────
        self.combo_status = QComboBox()
        for s in StatusExame:
            self.combo_status.addItem(s.value.capitalize(), s)

        # ── Observações ────────────────────────────────
        self.input_obs = QTextEdit()
        self.input_obs.setPlaceholderText("Observações...")
        self.input_obs.setMaximumHeight(70)

        # ── Adicionar campos ao form ───────────────────
        form.addRow("Paciente:", self.combo_paciente)
        form.addRow("Médico:", self.combo_medico)
        form.addRow("Tipo de Exame:", linha_tipo)
        form.addRow("Local:", linha_local)
        form.addRow("Data/Hora:", self.input_data_hora)
        form.addRow("Status:", self.combo_status)
        form.addRow("Observações:", self.input_obs)

        # ── Resultado ──────────────────────────────────
        resultado_layout = QVBoxLayout()

        toolbar_resultado = QToolBar()
        bold_action = QAction("B", self)
        bold_action.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        bold_action.triggered.connect(lambda: self.input_resultado.setFontWeight(
            QFont.Weight.Normal if self.input_resultado.fontWeight() == QFont.Weight.Bold else QFont.Weight.Bold
        ))
        italic_action = QAction("I", self)
        italic_font = QFont("Arial", 9)
        italic_font.setItalic(True)
        italic_action.setFont(italic_font)
        italic_action.triggered.connect(lambda: self.input_resultado.setFontItalic(
            not self.input_resultado.fontItalic()
        ))
        bullet_action = QAction("• Lista", self)
        bullet_action.triggered.connect(self._toggle_bullet_resultado)
        toolbar_resultado.addAction(bold_action)
        toolbar_resultado.addAction(italic_action)
        toolbar_resultado.addAction(bullet_action)

        self.input_resultado = QTextEdit()
        self.input_resultado.setAcceptRichText(True)
        self.input_resultado.setPlaceholderText("Resultado do exame...")
        self.input_resultado.setMinimumHeight(180)

        resultado_layout.addWidget(toolbar_resultado)
        resultado_layout.addWidget(self.input_resultado)
        form.addRow("Resultado:", resultado_layout)

        botoes = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        botoes.accepted.connect(self._salvar)
        botoes.rejected.connect(self.reject)

        layout.addLayout(form)
        layout.addWidget(self._criar_secao_anexos())
        layout.addWidget(botoes)

    # ── Anexos ────────────────────────────────────────
    def _criar_secao_anexos(self):
        grupo = QGroupBox("📎 Anexos (PDF / Imagem)")
        grupo.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        vlayout = QVBoxLayout(grupo)
        vlayout.setSpacing(6)

        self.lista_anexos = QListWidget()
        self.lista_anexos.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.lista_anexos.setMinimumHeight(100)
        self.lista_anexos.itemDoubleClicked.connect(self._abrir_anexo)
        vlayout.addWidget(self.lista_anexos)

        btn_layout = QHBoxLayout()
        btn_anexar = QPushButton("📎 Anexar arquivo")
        btn_abrir  = QPushButton("📂 Abrir")
        btn_remover = QPushButton("🗑️ Remover")
        btn_anexar.setFixedHeight(30)
        btn_abrir.setFixedHeight(30)
        btn_remover.setFixedHeight(30)
        btn_anexar.clicked.connect(self._anexar_arquivo)
        btn_abrir.clicked.connect(self._abrir_anexo)
        btn_remover.clicked.connect(self._remover_anexo)
        btn_layout.addWidget(btn_anexar)
        btn_layout.addWidget(btn_abrir)
        btn_layout.addWidget(btn_remover)
        btn_layout.addStretch()
        vlayout.addLayout(btn_layout)

        # Carrega anexos existentes se for edição
        if self.exame:
            self._recarregar_anexos()

        return grupo

    def _recarregar_anexos(self):
        self.lista_anexos.clear()
        if not self.exame:
            return
        for anexo in self.service_anexo.buscar_por_exame(self.exame.id):
            icone = "📄" if anexo.tipo == "pdf" else "🖼️"
            item = QListWidgetItem(f"{icone}  {anexo.nome}")
            item.setData(Qt.ItemDataRole.UserRole, anexo)
            self.lista_anexos.addItem(item)

    def _anexar_arquivo(self):
        # Exame precisa estar salvo para ter ID
        if not self.exame:
            QMessageBox.information(
                self, "Atenção",
                "Salve o exame primeiro antes de adicionar anexos."
            )
            return

        paciente_id   = self.combo_paciente.currentData()
        paciente_nome = self.combo_paciente.currentText()

        caminho, _ = QFileDialog.getOpenFileName(
            self, "Selecionar arquivo",
            os.path.expanduser("~"),
            "PDF e Imagens (*.pdf *.jpg *.jpeg *.png *.bmp *.tiff *.tif *.webp)"
        )
        if not caminho:
            return

        try:
            self.service_anexo.anexar(
                exame_id=self.exame.id,
                paciente_id=paciente_id,
                paciente_nome=paciente_nome,
                caminho_origem=caminho,
            )
            self._recarregar_anexos()
        except Exception as e:
            QMessageBox.critical(self, "Erro ao anexar", str(e))

    def _abrir_anexo(self):
        item = self.lista_anexos.currentItem()
        if not item:
            return
        anexo = item.data(Qt.ItemDataRole.UserRole)
        caminho = anexo.caminho
        if not os.path.exists(caminho):
            QMessageBox.warning(self, "Arquivo não encontrado",
                                f"O arquivo não foi encontrado:\n{caminho}")
            return
        if sys.platform == "win32":
            os.startfile(caminho)
        else:
            subprocess.Popen(["xdg-open", caminho])

    def _remover_anexo(self):
        item = self.lista_anexos.currentItem()
        if not item:
            QMessageBox.warning(self, "Atenção", "Selecione um anexo para remover.")
            return
        anexo = item.data(Qt.ItemDataRole.UserRole)
        resp = QMessageBox.question(
            self, "Remover anexo",
            f"Remover '{anexo.nome}'?\n\nDeseja também apagar o arquivo do disco?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No |
            QMessageBox.StandardButton.Cancel
        )
        if resp == QMessageBox.StandardButton.Cancel:
            return
        apagar = resp == QMessageBox.StandardButton.Yes
        try:
            self.service_anexo.remover(anexo.id, apagar_arquivo=apagar)
            self._recarregar_anexos()
        except Exception as e:
            QMessageBox.critical(self, "Erro ao remover", str(e))

    def _toggle_bullet_resultado(self):
        cursor = self.input_resultado.textCursor()
        cursor.createList(QTextListFormat.Style.ListDisc)


    # ── Populadores ───────────────────────────────────
    def _popular_tipos(self):
        self.combo_tipo.clear()
        self.combo_tipo.addItem("— Selecione —", None)
        for t in self.service_tipo.buscar_todos():
            self.combo_tipo.addItem(t.nome, t.id)

    def _popular_locais(self):
        self.combo_local.clear()
        self.combo_local.addItem("— Selecione —", None)
        for l in self.service_local.buscar_todos():
            self.combo_local.addItem(f"{l.nome} ({l.tipo})", l.id)

    def _popular_medicos(self):
        self.combo_medico.clear()
        self.combo_medico.addItem("— Selecione —", None)
        for m in self.service_medico.buscar_todos():
            self.combo_medico.addItem(m.nome, m.id)

    # ── Cadastro rápido ───────────────────────────────
    def _novo_tipo(self):
        dlg = DialogTipoExame(self.db)
        if dlg.exec():
            self._popular_tipos()   # ← atualiza o combo após cadastrar

    def _novo_local(self):
        dlg = DialogLocalExame(self.db)
        if dlg.exec():
            self._popular_locais()  # ← atualiza o combo após cadastrar

    # ── Pré-preencher a partir de pedido ─────────────
    def _preencher_iniciais(self):
        d = self.dados_iniciais
        if d.get("paciente_id"):
            idx = self.combo_paciente.findData(d["paciente_id"])
            if idx >= 0:
                self.combo_paciente.setCurrentIndex(idx)
        if d.get("medico_id"):
            idx = self.combo_medico.findData(d["medico_id"])
            if idx >= 0:
                self.combo_medico.setCurrentIndex(idx)
        if d.get("tipo_exame_id"):
            idx = self.combo_tipo.findData(d["tipo_exame_id"])
            if idx >= 0:
                self.combo_tipo.setCurrentIndex(idx)

    # ── Preencher ao editar ───────────────────────────
    def _preencher_dados(self):
        e = self.exame

        idx = self.combo_paciente.findData(e.paciente_id)
        if idx >= 0:
            self.combo_paciente.setCurrentIndex(idx)

        idx = self.combo_tipo.findData(e.tipo_exame_id)
        if idx >= 0:
            self.combo_tipo.setCurrentIndex(idx)

        idx = self.combo_local.findData(e.local_id)
        if idx >= 0:
            self.combo_local.setCurrentIndex(idx)
        
        idx = self.combo_medico.findData(e.medico_id)
        if idx >= 0:
            self.combo_medico.setCurrentIndex(idx)


        if e.data_hora:
            self.input_data_hora.setDateTime(
                QDateTime(e.data_hora.date(), e.data_hora.time())
            )

        idx = self.combo_status.findData(e.status)
        if idx >= 0:
            self.combo_status.setCurrentIndex(idx)

        self.input_obs.setText(e.observacoes or "")
        self.input_resultado.setHtml(e.resultado or "")

    # ── Salvar ────────────────────────────────────────
    def _salvar(self):
        paciente_id   = self.combo_paciente.currentData()
        tipo_exame_id = self.combo_tipo.currentData()
        local_id      = self.combo_local.currentData()

        if not paciente_id:
            QMessageBox.warning(self, "Atenção", "Selecione um paciente.")
            return
        if not tipo_exame_id:
            QMessageBox.warning(self, "Atenção", "Selecione o tipo de exame.")
            return
        if not local_id:
            QMessageBox.warning(self, "Atenção", "Selecione o local.")
            return

        dados = {
            "paciente_id"  : paciente_id,
            "medico_id"    : self.combo_medico.currentData(),   # ← novo
            "tipo_exame_id": tipo_exame_id,
            "local_id"     : local_id,
            "data_hora"    : self.input_data_hora.dateTime().toPyDateTime(),
            "status"       : self.combo_status.currentData(),
            "observacoes"  : self.input_obs.toPlainText().strip() or None,
            "resultado"    : self.input_resultado.toHtml().strip() if self.input_resultado.toPlainText().strip() else None,
                }

        try:
            if self.exame:
                self.service.atualizar(self.exame.id, dados)
            else:
                self.exame_criado = self.service.cadastrar(dados)
            self.accept()
        except ValueError as e:
            QMessageBox.critical(self, "Erro", str(e))
