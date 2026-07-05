from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QTextEdit, QDialogButtonBox, QMessageBox
)
from app.services.tipo_exame_service import TipoExameService


class DialogTipoExame(QDialog):
    def __init__(self, db, tipo_exame=None):
        super().__init__()
        self.db          = db
        self.tipo_exame  = tipo_exame
        self.service     = TipoExameService(db)
        self._setup_ui()
        if tipo_exame:
            self._preencher_dados()

    def _setup_ui(self):
        self.setWindowTitle("✏️ Editar Tipo de Exame" if self.tipo_exame else "➕ Novo Tipo de Exame")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)
        form   = QFormLayout()

        self.input_nome      = QLineEdit()
        self.input_descricao = QTextEdit()
        self.input_descricao.setMaximumHeight(80)
        self.input_descricao.setPlaceholderText("Descrição opcional...")

        form.addRow("Nome: *",    self.input_nome)
        form.addRow("Descrição:", self.input_descricao)

        botoes = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        botoes.accepted.connect(self._salvar)
        botoes.rejected.connect(self.reject)

        layout.addLayout(form)
        layout.addWidget(botoes)

    def _preencher_dados(self):
        self.input_nome.setText(self.tipo_exame.nome or "")
        self.input_descricao.setText(self.tipo_exame.descricao or "")

    def _salvar(self):
        nome = self.input_nome.text().strip()
        if not nome:
            QMessageBox.warning(self, "Atenção", "Nome é obrigatório.")
            return

        dados = {
            "nome"     : nome,
            "descricao": self.input_descricao.toPlainText().strip() or None,
        }

        try:
            if self.tipo_exame:
                self.service.atualizar(self.tipo_exame.id, dados)
            else:
                self.service.cadastrar(dados)
            self.accept()
        except ValueError as e:
            QMessageBox.critical(self, "Erro", str(e))
