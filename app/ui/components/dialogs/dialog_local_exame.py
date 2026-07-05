from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QComboBox, QDialogButtonBox, QMessageBox
)
from app.services.local_exame_service import LocalExameService


class DialogLocalExame(QDialog):
    def __init__(self, db, local=None):
        super().__init__()
        self.db      = db
        self.local   = local
        self.service = LocalExameService(db)
        self._setup_ui()
        if local:
            self._preencher_dados()

    def _setup_ui(self):
        self.setWindowTitle("✏️ Editar Local" if self.local else "➕ Novo Local")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)
        form   = QFormLayout()

        self.input_nome     = QLineEdit()
        self.input_endereco = QLineEdit()
        self.input_telefone = QLineEdit()

        self.combo_tipo = QComboBox()
        for t in ["Hospital", "Clínica", "Laboratório", "Outro"]:
            self.combo_tipo.addItem(t, t.lower())

        form.addRow("Nome: *",    self.input_nome)
        form.addRow("Tipo:",      self.combo_tipo)
        form.addRow("Endereço:",  self.input_endereco)
        form.addRow("Telefone:",  self.input_telefone)

        botoes = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        botoes.accepted.connect(self._salvar)
        botoes.rejected.connect(self.reject)

        layout.addLayout(form)
        layout.addWidget(botoes)

    def _preencher_dados(self):
        self.input_nome.setText(self.local.nome or "")
        self.input_endereco.setText(self.local.endereco or "")
        self.input_telefone.setText(self.local.telefone or "")
        idx = self.combo_tipo.findData(self.local.tipo)
        if idx >= 0:
            self.combo_tipo.setCurrentIndex(idx)

    def _salvar(self):
        nome = self.input_nome.text().strip()
        if not nome:
            QMessageBox.warning(self, "Atenção", "Nome é obrigatório.")
            return

        dados = {
            "nome"    : nome,
            "tipo"    : self.combo_tipo.currentData(),
            "endereco": self.input_endereco.text().strip() or None,
            "telefone": self.input_telefone.text().strip() or None,
        }

        try:
            if self.local:
                self.service.atualizar(self.local.id, dados)
            else:
                self.service.cadastrar(dados)
            self.accept()
        except ValueError as e:
            QMessageBox.critical(self, "Erro", str(e))
