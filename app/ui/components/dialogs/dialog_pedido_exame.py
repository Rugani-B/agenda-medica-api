import os
import subprocess
import sys

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QComboBox,
    QTextEdit, QCheckBox, QDialogButtonBox, QMessageBox,
    QLineEdit, QPushButton, QHBoxLayout, QFileDialog
)
from app.services.pedido_exame_service import PedidoExameService
from app.services.tipo_exame_service import TipoExameService
from app.services.paciente_service import PacienteService
from app.services.medico_service import MedicoService
from app.services.consulta_service import ConsultaService
from app.models.pedido_exame import StatusPedido

STATUS_LABELS = {
    "solicitado": "Solicitado",
    "agendado"  : "Agendado",
    "realizado" : "Realizado",
    "cancelado" : "Cancelado",
}


class DialogPedidoExame(QDialog):
    """Cria ou edita um pedido de exame.

    Quando chamado a partir de uma consulta, recebe `consulta` e os combos
    de paciente/médico/consulta são pré-preenchidos e bloqueados.
    Quando chamado da tela standalone, `consulta=None` e todos os combos
    ficam livres para seleção.
    """

    def __init__(self, db, consulta=None, pedido=None, parent=None):
        super().__init__(parent)
        self.db       = db
        self.consulta = consulta
        self.pedido   = pedido
        self.service      = PedidoExameService(db)
        self.svc_tipo     = TipoExameService(db)
        self.svc_paciente = PacienteService(db)
        self.svc_medico   = MedicoService(db)
        self.svc_consulta = ConsultaService(db)

        self.setWindowTitle("✏️ Editar Pedido de Exame" if pedido else "➕ Novo Pedido de Exame")
        self.setMinimumWidth(560)
        self._setup_ui()
        if pedido:
            self._preencher()
        elif consulta:
            self._preencher_de_consulta()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        form   = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        # Paciente
        self.combo_paciente = QComboBox()
        self.combo_paciente.addItem("— Selecione —", None)
        for p in self.svc_paciente.buscar_ativos():
            self.combo_paciente.addItem(p.nome, p.id)
        self.combo_paciente.currentIndexChanged.connect(self._ao_mudar_paciente)

        # Médico
        self.combo_medico = QComboBox()
        self.combo_medico.addItem("— Nenhum —", None)
        for m in self.svc_medico.buscar_todos():
            self.combo_medico.addItem(m.nome, m.id)

        # Consulta (opcional, filtrada pelo paciente)
        self.combo_consulta = QComboBox()
        self._popular_consultas(paciente_id=None)

        # Tipo de Exame
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItem("— Selecione —", None)
        for t in self.svc_tipo.buscar_todos():
            self.combo_tipo.addItem(t.nome, t.id)

        # Status
        self.combo_status = QComboBox()
        for s in StatusPedido:
            self.combo_status.addItem(STATUS_LABELS[s.value], s)

        # Urgente
        self.check_urgente = QCheckBox("Urgente")

        # Observações
        self.input_obs = QTextEdit()
        self.input_obs.setPlaceholderText("Observações / justificativa clínica...")
        self.input_obs.setMaximumHeight(80)

        # Documento (PDF / JPG)
        linha_doc = QHBoxLayout()
        self.input_doc = QLineEdit()
        self.input_doc.setPlaceholderText("Caminho do arquivo (PDF ou imagem)...")
        self.input_doc.setReadOnly(True)
        btn_selecionar = QPushButton("📂 Selecionar")
        btn_selecionar.setFixedWidth(110)
        btn_selecionar.clicked.connect(self._selecionar_documento)
        btn_abrir = QPushButton("🔍 Abrir")
        btn_abrir.setFixedWidth(70)
        btn_abrir.clicked.connect(self._abrir_documento)
        linha_doc.addWidget(self.input_doc)
        linha_doc.addWidget(btn_selecionar)
        linha_doc.addWidget(btn_abrir)

        form.addRow("Paciente: *",      self.combo_paciente)
        form.addRow("Médico:",          self.combo_medico)
        form.addRow("Consulta:",        self.combo_consulta)
        form.addRow("Tipo de Exame: *", self.combo_tipo)
        form.addRow("Status:",          self.combo_status)
        form.addRow("",                 self.check_urgente)
        form.addRow("Observações:",     self.input_obs)
        form.addRow("Documento:",       linha_doc)

        botoes = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        botoes.accepted.connect(self._salvar)
        botoes.rejected.connect(self.reject)

        layout.addLayout(form)
        layout.addWidget(botoes)

    # ── Populadores ───────────────────────────────────

    def _popular_consultas(self, paciente_id=None):
        self.combo_consulta.clear()
        self.combo_consulta.addItem("— Nenhuma —", None)
        for c in self.svc_consulta.buscar_todos():
            if paciente_id and c.paciente_id != paciente_id:
                continue
            pac  = c.paciente.nome if c.paciente else "?"
            data = c.data_hora.strftime("%d/%m/%Y") if c.data_hora else "s/d"
            self.combo_consulta.addItem(f"#{c.id} – {pac} ({data})", c.id)

    def _ao_mudar_paciente(self):
        pac_id = self.combo_paciente.currentData()
        self._popular_consultas(paciente_id=pac_id)

    # ── Documento ─────────────────────────────────────

    def _selecionar_documento(self):
        caminho, _ = QFileDialog.getOpenFileName(
            self, "Selecionar documento do pedido",
            os.path.expanduser("~"),
            "PDF e Imagens (*.pdf *.jpg *.jpeg *.png *.bmp *.tiff *.tif *.webp)"
        )
        if caminho:
            self.input_doc.setText(caminho)

    def _abrir_documento(self):
        caminho = self.input_doc.text().strip()
        if not caminho:
            return
        if not os.path.exists(caminho):
            QMessageBox.warning(self, "Arquivo não encontrado",
                                f"O arquivo não foi encontrado:\n{caminho}")
            return
        if sys.platform == "win32":
            os.startfile(caminho)
        else:
            subprocess.Popen(["xdg-open", caminho])

    # ── Pré-preenchimento ─────────────────────────────

    def _preencher_de_consulta(self):
        """Pré-preenche quando aberto a partir de uma consulta (campos bloqueados)."""
        c = self.consulta
        idx = self.combo_paciente.findData(c.paciente_id)
        if idx >= 0:
            self.combo_paciente.setCurrentIndex(idx)
        self.combo_paciente.setEnabled(False)

        if c.medico_id:
            idx = self.combo_medico.findData(c.medico_id)
            if idx >= 0:
                self.combo_medico.setCurrentIndex(idx)
        self.combo_medico.setEnabled(False)

        self._popular_consultas(paciente_id=c.paciente_id)
        idx = self.combo_consulta.findData(c.id)
        if idx >= 0:
            self.combo_consulta.setCurrentIndex(idx)
        self.combo_consulta.setEnabled(False)

    def _preencher(self):
        """Pré-preenche ao editar pedido existente."""
        p = self.pedido

        idx = self.combo_paciente.findData(p.paciente_id)
        if idx >= 0:
            self.combo_paciente.setCurrentIndex(idx)

        if p.medico_id:
            idx = self.combo_medico.findData(p.medico_id)
            if idx >= 0:
                self.combo_medico.setCurrentIndex(idx)

        if p.consulta_id:
            self._popular_consultas(paciente_id=p.paciente_id)
            idx = self.combo_consulta.findData(p.consulta_id)
            if idx >= 0:
                self.combo_consulta.setCurrentIndex(idx)

        idx = self.combo_tipo.findData(p.tipo_exame_id)
        if idx >= 0:
            self.combo_tipo.setCurrentIndex(idx)

        for i in range(self.combo_status.count()):
            if self.combo_status.itemData(i) == p.status:
                self.combo_status.setCurrentIndex(i)
                break

        self.check_urgente.setChecked(bool(p.urgente))
        self.input_obs.setText(p.observacoes or "")

        if p.documento_path:
            self.input_doc.setText(p.documento_path)

    # ── Salvar ────────────────────────────────────────

    def _salvar(self):
        paciente_id   = self.combo_paciente.currentData()
        tipo_id       = self.combo_tipo.currentData()
        medico_id     = self.combo_medico.currentData()
        consulta_id   = self.combo_consulta.currentData()
        status        = self.combo_status.currentData()
        urgente       = self.check_urgente.isChecked()
        observacoes   = self.input_obs.toPlainText().strip() or None
        doc_origem    = self.input_doc.text().strip() or None

        if not paciente_id:
            QMessageBox.warning(self, "Atenção", "Selecione o paciente.")
            return
        if not tipo_id:
            QMessageBox.warning(self, "Atenção", "Selecione o tipo de exame.")
            return

        # Resolve nome do paciente para cópia de arquivo
        paciente_nome = self.combo_paciente.currentText()

        try:
            if self.pedido:
                # Processa documento se foi alterado
                doc_path = self.pedido.documento_path
                if doc_origem and doc_origem != doc_path:
                    doc_path = self.service._registrar_documento(
                        paciente_id, paciente_nome, doc_origem
                    )
                elif not doc_origem:
                    doc_path = None

                self.service.atualizar(self.pedido.id, {
                    "paciente_id"   : paciente_id,
                    "medico_id"     : medico_id,
                    "consulta_id"   : consulta_id,
                    "tipo_exame_id" : tipo_id,
                    "status"        : status,
                    "urgente"       : urgente,
                    "observacoes"   : observacoes,
                    "documento_path": doc_path,
                })
            else:
                self.service.criar(
                    paciente_id     = paciente_id,
                    tipo_exame_id   = tipo_id,
                    consulta_id     = consulta_id,
                    medico_id       = medico_id,
                    urgente         = urgente,
                    observacoes     = observacoes,
                    status          = status,
                    paciente_nome   = paciente_nome,
                    documento_origem= doc_origem,
                )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))
