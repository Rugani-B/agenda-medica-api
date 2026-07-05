# app/ui/components/dialogs/dialog_paciente.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout,
    QLineEdit, QDateEdit, QPushButton,
    QHBoxLayout, QMessageBox, QDialogButtonBox
)
from PyQt6.QtCore import QDate
from app.services.paciente_service import PacienteService


class DialogPaciente(QDialog):
    def __init__(self, db, paciente=None):
        super().__init__()
        self.db       = db
        self.paciente = paciente  # None = novo, objeto = editar
        self.service  = PacienteService(db)
        self._setup_ui()

        if paciente:
            self._preencher_dados()

    def _setup_ui(self):
        titulo = "Editar Paciente" if self.paciente else "Novo Paciente"
        self.setWindowTitle(titulo)
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        # Formulário
        form = QFormLayout()

        self.input_nome         = QLineEdit()
        self.input_cpf          = QLineEdit()
        self.input_cpf.setInputMask("000.000.000-00")
        self.input_telefone     = QLineEdit()
        self.input_email        = QLineEdit()
        self.input_nascimento   = QDateEdit()
        self.input_nascimento.setCalendarPopup(True)
        self.input_nascimento.setDate(QDate.currentDate())
        self.input_emergencia   = QLineEdit()
        self.input_tel_emergencia = QLineEdit()

        form.addRow("Nome: *",              self.input_nome)
        form.addRow("CPF:",                 self.input_cpf)
        form.addRow("Data Nascimento: *",   self.input_nascimento)
        form.addRow("Telefone:",            self.input_telefone)
        form.addRow("E-mail:",              self.input_email)
        form.addRow("Contato Emergência:",  self.input_emergencia)
        form.addRow("Tel. Emergência:",     self.input_tel_emergencia)

        # Botões
        botoes = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        botoes.accepted.connect(self._salvar)
        botoes.rejected.connect(self.reject)

        layout.addLayout(form)
        layout.addWidget(botoes)

    def _preencher_dados(self):
        p = self.paciente
        self.input_nome.setText(p.nome)
        self.input_cpf.setText(p.cpf or "")
        self.input_telefone.setText(p.telefone or "")
        self.input_email.setText(p.email or "")
        self.input_emergencia.setText(p.contato_emergencia or "")
        self.input_tel_emergencia.setText(p.tel_emergencia or "")

        if p.data_nascimento:
            self.input_nascimento.setDate(QDate(
                p.data_nascimento.year,
                p.data_nascimento.month,
                p.data_nascimento.day
            ))

    def _salvar(self):
        nome = self.input_nome.text().strip()
        if not nome:
            QMessageBox.warning(self, "Atenção", "Nome é obrigatório.")
            return

        dados = {
            "nome"              : nome,
            "cpf"               : self.input_cpf.text().strip() or None,
            "data_nascimento"   : self.input_nascimento.date().toPyDate(),
            "telefone"          : self.input_telefone.text().strip() or None,
            "email"             : self.input_email.text().strip() or None,
            "contato_emergencia": self.input_emergencia.text().strip() or None,
            "tel_emergencia"    : self.input_tel_emergencia.text().strip() or None,
        }

        try:
            if self.paciente:
                self.service.atualizar(self.paciente.id, dados)
            else:
                self.service.cadastrar(dados)
            self.accept()
        except ValueError as e:
            QMessageBox.critical(self, "Erro", str(e))
