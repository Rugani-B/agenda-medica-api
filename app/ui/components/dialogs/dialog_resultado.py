from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTextEdit, QDialogButtonBox, QMessageBox
)
from PyQt6.QtGui import QFont, QTextListFormat
from PyQt6.QtCore import Qt

class DialogResultado(QDialog):
    def __init__(self, resultado: str = "", editavel: bool = False, parent=None):
        super().__init__(parent)
        self.editavel = editavel
        self.setWindowTitle("📄 Resultado do Exame")
        self.setMinimumSize(1000, 750)
        self.resize(1000, 800)
        self._setup_ui(resultado)

    def _setup_ui(self, resultado: str):
        layout = QVBoxLayout(self)
        
        # ── Área de Texto (usando HTML) ───────────────
        self.texto = QTextEdit()
        self.texto.setAcceptRichText(True)
        self.texto.setHtml(resultado) 
        self.texto.setReadOnly(not self.editavel)
        layout.addWidget(self.texto)

        # ── Botões ─────────────────────────────────────
        botoes = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save if self.editavel else QDialogButtonBox.StandardButton.Close
        )
        botoes.accepted.connect(self.accept)
        botoes.rejected.connect(self.reject)
        layout.addWidget(botoes)

    def get_resultado(self) -> str:
        # Retorna o texto formatado como HTML para salvar no banco
        return self.texto.toHtml()
