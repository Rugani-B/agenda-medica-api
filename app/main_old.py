import sys
from PyQt6.QtWidgets import QApplication
from app.ui.tela_pacientes_old import TelaPacientes

a= 1

if a ==1:
    app = QApplication(sys.argv)

    janela = TelaPacientes()

    janela.show()

    sys.exit(app.exec())

# =========================================================
if a == 2:
    from ui.agenda_view import AgendaView

    app = QApplication([])
    window = AgendaView()
    window.show()
    app.exec()