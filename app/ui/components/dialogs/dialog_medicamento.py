from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QComboBox, QDialogButtonBox, QMessageBox
)

APRESENTACOES = [
    "— Selecione —",
    "Comprimido", "Cápsula", "Solução oral", "Suspensão oral",
    "Injetável", "Pomada", "Creme", "Gel", "Colírio",
    "Spray nasal", "Inalador", "Supositório", "Adesivo", "Outro",
]


class DialogMedicamento(QDialog):
    def __init__(self, db, medicamento=None, parent=None):
        super().__init__(parent)
        self.db          = db
        self.medicamento = medicamento
        from app.services.medicamento_service import MedicamentoService
        self.service = MedicamentoService(db)

        self.setWindowTitle("✏️ Editar Medicamento" if medicamento else "➕ Novo Medicamento")
        self.setMinimumWidth(400)
        self._setup_ui()
        if medicamento:
            self._preencher()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        form   = QFormLayout()

        self.input_nome = QLineEdit()
        self.input_nome.setPlaceholderText("Nome comercial ou genérico")

        self.input_principio = QLineEdit()
        self.input_principio.setPlaceholderText("Ex: Amoxicilina tri-hidratada")

        self.combo_apresentacao = QComboBox()
        self.combo_apresentacao.addItems(APRESENTACOES)

        form.addRow("Nome: *",         self.input_nome)
        form.addRow("Princípio ativo:", self.input_principio)
        form.addRow("Apresentação:",    self.combo_apresentacao)

        botoes = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        botoes.accepted.connect(self._salvar)
        botoes.rejected.connect(self.reject)

        layout.addLayout(form)
        layout.addWidget(botoes)

    def _preencher(self):
        m = self.medicamento
        self.input_nome.setText(m.nome or "")
        self.input_principio.setText(m.principio_ativo or "")
        idx = self.combo_apresentacao.findText(m.apresentacao or "")
        if idx >= 0:
            self.combo_apresentacao.setCurrentIndex(idx)

    def _salvar(self):
        nome = self.input_nome.text().strip()
        if not nome:
            QMessageBox.warning(self, "Atenção", "Nome é obrigatório.")
            return
        apres = self.combo_apresentacao.currentText()
        dados = {
            "nome"           : nome,
            "principio_ativo": self.input_principio.text().strip() or None,
            "apresentacao"   : None if apres == "— Selecione —" else apres,
        }
        try:
            if self.medicamento:
                self.service.atualizar(self.medicamento.id, dados)
            else:
                self.service.cadastrar(dados)
            self.accept()
        except ValueError as e:
            QMessageBox.critical(self, "Erro", str(e))
