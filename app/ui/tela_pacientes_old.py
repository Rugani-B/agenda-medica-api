from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem )
from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import QDateEdit

from app.repositorios.repositorio_pacientes import (PacienteRepository)


class TelaPacientes(QWidget):

    def __init__(self):

        super().__init__()

        self.paciente_em_edicao = None

        self.setWindowTitle(
            "Cadastro de Pacientes"
        )

        self.resize(1000, 650)

        self.setup_ui()

        self.carregar_pacientes()

    def setup_ui(self):

        layout_principal = QVBoxLayout()

        # BUSCA

        busca_layout = QHBoxLayout()

        self.input_busca = QLineEdit()

        self.input_busca.setPlaceholderText(
            "Buscar paciente..."
        )

        self.btn_buscar = QPushButton("Buscar")

        busca_layout.addWidget(self.input_busca)

        busca_layout.addWidget(self.btn_buscar)

        layout_principal.addLayout(busca_layout)

        # FORMULÁRIO

        form_layout = QFormLayout()

        self.input_nome = QLineEdit()

        self.input_data = QDateEdit()

        self.input_data.setCalendarPopup(True)

        self.input_data.setDate(QDate.currentDate())

        self.input_cpf = QLineEdit()

        self.input_cpf.setInputMask(
            "000.000.000-00"
        )

        self.input_telefone = QLineEdit()

        self.input_telefone.setInputMask(
            "(00) 00000-0000"
        )

        self.input_email = QLineEdit()

        self.input_contato = QLineEdit()

        self.input_tel_contato = QLineEdit()

        self.input_tel_contato.setInputMask(
            "(00) 00000-0000"
        )

        form_layout.addRow("Nome:", self.input_nome)

        form_layout.addRow(
            "Nascimento:",
            self.input_data
        )

        form_layout.addRow("CPF:", self.input_cpf)

        form_layout.addRow(
            "Telefone:",
            self.input_telefone
        )

        form_layout.addRow("Email:", self.input_email)

        form_layout.addRow(
            "Contato Emergência:",
            self.input_contato
        )

        form_layout.addRow(
            "Telefone Emergência:",
            self.input_tel_contato
        )

        layout_principal.addLayout(form_layout)

        # BOTÕES

        botoes_layout = QHBoxLayout()

        self.btn_novo = QPushButton("Novo")

        self.btn_salvar = QPushButton("Salvar")

        self.btn_excluir = QPushButton("Excluir")

        botoes_layout.addWidget(self.btn_novo)

        botoes_layout.addWidget(self.btn_salvar)

        botoes_layout.addWidget(self.btn_excluir)

        layout_principal.addLayout(botoes_layout)

        # TABELA

        self.tabela = QTableWidget()

        self.tabela.setColumnCount(4)

        self.tabela.setHorizontalHeaderLabels([
            "ID",
            "Nome",
            "CPF",
            "Telefone"
        ])

        layout_principal.addWidget(self.tabela)

        self.setLayout(layout_principal)

        # EVENTOS

        self.btn_salvar.clicked.connect(
            self.salvar_paciente
        )

        self.btn_excluir.clicked.connect(
            self.excluir_paciente
        )

        self.btn_novo.clicked.connect(
            self.novo_paciente
        )

        self.btn_buscar.clicked.connect(
            self.buscar_pacientes
        )

        self.tabela.cellClicked.connect(
            self.carregar_paciente_selecionado
        )

    def obter_dados_formulario(self):

        return {

            "nome": self.input_nome.text(),

            "data_nascimento":
                self.input_data.date().toPyDate(),

            "cpf": self.input_cpf.text(),

            "telefone":
                self.input_telefone.text(),

            "email":
                self.input_email.text(),

            "contato_emergencia":
                self.input_contato.text(),

            "tel_emergencia":
                self.input_tel_contato.text()
        }

    def salvar_paciente(self):

        try:

            dados = self.obter_dados_formulario()

            if self.paciente_em_edicao:

                PacienteRepository.atualizar(
                    self.paciente_em_edicao,
                    dados
                )

                QMessageBox.information(
                    self,
                    "Sucesso",
                    "Paciente atualizado."
                )

            else:

                PacienteRepository.criar(dados)

                QMessageBox.information(
                    self,
                    "Sucesso",
                    "Paciente criado."
                )

            self.novo_paciente()

            self.carregar_pacientes()

        except Exception as e:

            QMessageBox.critical(
                self,
                "Erro",
                str(e)
            )

    def carregar_pacientes(self):

        pacientes = PacienteRepository.listar()

        self.preencher_tabela(pacientes)

    def preencher_tabela(self, pacientes):

        self.tabela.setRowCount(len(pacientes))

        for linha, paciente in enumerate(pacientes):

            self.tabela.setItem(
                linha,
                0,
                QTableWidgetItem(str(paciente.id))
            )

            self.tabela.setItem(
                linha,
                1,
                QTableWidgetItem(paciente.nome)
            )

            self.tabela.setItem(
                linha,
                2,
                QTableWidgetItem(
                    paciente.cpf or ""
                )
            )

            self.tabela.setItem(
                linha,
                3,
                QTableWidgetItem(
                    paciente.telefone or ""
                )
            )

    def carregar_paciente_selecionado(
        self,
        linha
    ):

        self.paciente_em_edicao = int(
            self.tabela.item(linha, 0).text()
        )

        pacientes = PacienteRepository.listar()

        paciente = next(
            p for p in pacientes
            if p.id == self.paciente_em_edicao
        )

        self.input_nome.setText(
            paciente.nome
        )

        self.input_data.setDate(
            QDate(
                paciente.data_nascimento.year,
                paciente.data_nascimento.month,
                paciente.data_nascimento.day
            )
        )

        self.input_cpf.setText(
            paciente.cpf or ""
        )

        self.input_telefone.setText(
            paciente.telefone or ""
        )

        self.input_email.setText(
            paciente.email or ""
        )

        self.input_contato.setText(
            paciente.contato_emergencia or ""
        )

        self.input_tel_contato.setText(
            paciente.tel_emergencia or ""
        )

    def excluir_paciente(self):

        linha = self.tabela.currentRow()

        if linha < 0:

            QMessageBox.warning(
                self,
                "Aviso",
                "Selecione um paciente."
            )

            return

        paciente_id = int(
            self.tabela.item(linha, 0).text()
        )

        PacienteRepository.excluir(
            paciente_id
        )

        self.carregar_pacientes()

        self.novo_paciente()

    def buscar_pacientes(self):

        texto = self.input_busca.text()

        pacientes = (
            PacienteRepository
            .buscar_por_nome(texto)
        )

        self.preencher_tabela(pacientes)

    def novo_paciente(self):

        self.paciente_em_edicao = None

        self.input_nome.clear()

        self.input_cpf.clear()

        self.input_telefone.clear()

        self.input_email.clear()

        self.input_contato.clear()

        self.input_tel_contato.clear()

        self.input_data.setDate(
            QDate.currentDate()
        )