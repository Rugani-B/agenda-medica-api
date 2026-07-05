# app/ui/components/dialogs/dialog_medico.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout,
    QLineEdit, QComboBox, QPushButton,
    QMessageBox, QDialogButtonBox
)
from app.services.medico_service import MedicoService
from app.repositorios.especialidade_repository import EspecialidadeRepository


class DialogMedico(QDialog):
    def __init__(self, db, medico=None):
        super().__init__()
        self.db      = db
        self.medico  = medico
        self.service = MedicoService(db)
        self.repo_especialidade = EspecialidadeRepository(db)
        self._setup_ui()

        if medico:
            self._preencher_dados()

    def _setup_ui(self):
        titulo = "Editar Médico" if self.medico else "Novo Médico"
        self.setWindowTitle(titulo)
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)
        form   = QFormLayout()

        self.input_nome      = QLineEdit()
        self.input_crm       = QLineEdit()
        self.input_telefone  = QLineEdit()
        self.input_clinica   = QLineEdit()

        # ComboBox de especialidades
        self.combo_especialidade = QComboBox()
        self._carregar_especialidades()

        form.addRow("Nome: *",        self.input_nome)
        form.addRow("CRM:",           self.input_crm)
        form.addRow("Especialidade:", self.combo_especialidade)
        form.addRow("Clínica:",       self.input_clinica)
        form.addRow("Telefone:",      self.input_telefone)

        # Botões
        botoes = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        botoes.accepted.connect(self._salvar)
        botoes.rejected.connect(self.reject)

        layout.addLayout(form)
        layout.addWidget(botoes)

    def _carregar_especialidades(self):
        self.combo_especialidade.clear()
        self.combo_especialidade.addItem("— Selecione —", None)

        especialidades = self.repo_especialidade.buscar_todos()
        for esp in especialidades:
            self.combo_especialidade.addItem(esp.nome, esp.id)

    def _preencher_dados(self):
        m = self.medico
        self.input_nome.setText(m.nome)
        self.input_crm.setText(m.crm or "")
        self.input_telefone.setText(m.telefone or "")
        self.input_clinica.setText(m.clinica or "")

        # Seleciona a especialidade correta no combo
        if m.especialidade_id:
            index = self.combo_especialidade.findData(m.especialidade_id)
            if index >= 0:
                self.combo_especialidade.setCurrentIndex(index)

    def _salvar(self):
        nome = self.input_nome.text().strip()
        if not nome:
            QMessageBox.warning(self, "Atenção", "Nome é obrigatório.")
            return

        dados = {
            "nome"            : nome,
            "crm"             : self.input_crm.text().strip() or None,
            "telefone"        : self.input_telefone.text().strip() or None,
            "clinica"         : self.input_clinica.text().strip() or None,
            "especialidade_id": self.combo_especialidade.currentData(),
        }

        try:
            if self.medico:
                self.service.atualizar(self.medico.id, dados)
            else:
                self.service.cadastrar(dados)
            self.accept()
        except ValueError as e:
            QMessageBox.critical(self, "Erro", str(e))
