# app/main.py
import sys
from PyQt6.QtWidgets import QApplication, QLabel
from app.database.init_db import init_db
from app.ui.tela_login import TelaLogin
from app.ui.tela_principal import TelaPrincipal


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Inicializa o banco
    init_db()

    # Função chamada após login bem-sucedido
    def ao_logar(usuario):
        global janela_principal
        janela_principal = TelaPrincipal(usuario)
        janela_principal.show()

    # Abre a tela de login
    login = TelaLogin(ao_logar)
    login.show()

    sys.exit(app.exec())


if __name__ == "__main__":
     main()
