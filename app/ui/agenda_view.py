from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QCalendarWidget,
    QListWidget, QPushButton, QMessageBox, QLabel
)
from PyQt6.QtCore import QDate


class AgendaView(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Agenda da Clínica")
        self.resize(900, 600)

        # Layout principal
        layout = QHBoxLayout()
        self.setLayout(layout)

        # -------------------------
        # COLUNA ESQUERDA: CALENDÁRIO
        # -------------------------
        self.calendar = QCalendarWidget()
        self.calendar.selectionChanged.connect(self.load_consultas_do_dia)

        layout.addWidget(self.calendar, 40)

        # -------------------------
        # COLUNA DIREITA: LISTA + BOTÕES
        # -------------------------
        right_panel = QVBoxLayout()

        self.label_data = QLabel("Consultas do dia:")
        right_panel.addWidget(self.label_data)

        self.lista_consultas = QListWidget()
        right_panel.addWidget(self.lista_consultas, 80)

        # Botões
        btn_layout = QHBoxLayout()

        self.btn_reagendar = QPushButton("Reagendar")
        self.btn_reagendar.clicked.connect(self.reagendar_consulta)
        btn_layout.addWidget(self.btn_reagendar)

        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.clicked.connect(self.cancelar_consulta)
        btn_layout.addWidget(self.btn_cancelar)

        self.btn_nova = QPushButton("Nova Consulta")
        self.btn_nova.clicked.connect(self.nova_consulta)
        btn_layout.addWidget(self.btn_nova)

        right_panel.addLayout(btn_layout)

        layout.addLayout(right_panel, 60)

        # Carrega consultas do dia atual
        self.load_consultas_do_dia()

    # ---------------------------------------------------------
    # CARREGAR CONSULTAS DO DIA (AQUI VOCÊ VAI INTEGRAR O BANCO)
    # ---------------------------------------------------------
    def load_consultas_do_dia(self):
        data = self.calendar.selectedDate()
        data_str = data.toString("dd/MM/yyyy")

        self.label_data.setText(f"Consultas do dia {data_str}:")
        self.lista_consultas.clear()

        # 🔥 EXEMPLO — depois você troca pelo SELECT no PostgreSQL
        consultas_fake = {
            "20/05/2026": [
                "09:00 - Ana Clara (Retorno)",
                "10:30 - João Pedro (Avaliação)",
                "14:00 - Maria Silva (Consulta)"
            ],
            "21/05/2026": [
                "08:00 - Carlos Souza (Exame)",
                "11:00 - Fernanda Lima (Retorno)"
            ]
        }

        consultas = consultas_fake.get(data_str, [])

        if not consultas:
            self.lista_consultas.addItem("Nenhuma consulta para este dia.")
        else:
            for c in consultas:
                self.lista_consultas.addItem(c)

    # ---------------------------------------------------------
    # AÇÕES DOS BOTÕES
    # ---------------------------------------------------------
    def reagendar_consulta(self):
        item = self.lista_consultas.currentItem()
        if not item:
            QMessageBox.warning(self, "Aviso", "Selecione uma consulta para reagendar.")
            return

        QMessageBox.information(self, "Reagendar", f"Reagendar: {item.text()}")

        # Aqui você abriria uma janela de reagendamento
        # ou chamaria um endpoint FastAPI

    def cancelar_consulta(self):
        item = self.lista_consultas.currentItem()
        if not item:
            QMessageBox.warning(self, "Aviso", "Selecione uma consulta para cancelar.")
            return

        resposta = QMessageBox.question(
            self,
            "Cancelar consulta",
            f"Tem certeza que deseja cancelar:\n\n{item.text()}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if resposta == QMessageBox.StandardButton.Yes:
            QMessageBox.information(self, "Cancelada", "Consulta cancelada com sucesso.")
            # Aqui você chamaria DELETE no backend

    def nova_consulta(self):
        QMessageBox.information(self, "Nova Consulta", "Abrir tela de nova consulta.")
        # Aqui você abriria a tela de criação de consulta
