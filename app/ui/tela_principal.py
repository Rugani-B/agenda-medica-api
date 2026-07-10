# app/ui/tela_principal.py
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QLabel,
    QStackedWidget, QFrame, QCalendarWidget,
    QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import subprocess
import os
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
from app.ui.tela_pacientes    import TelaPacientes
from app.ui.tela_consultas    import TelaConsultas
from app.ui.tela_medicos      import TelaMedicos
from app.ui.tela_exames       import TelaExames
from app.ui.tela_medicamentos   import TelaMedicamentos
from app.ui.tela_pedidos_exame  import TelaPedidosExame
from app.ui.tela_adesao         import TelAdesao
from app.ui.tela_pendencias     import TelaPendencias
from app.ui.tela_responsaveis   import TelaResponsaveis


class TelaPrincipal(QMainWindow):
    def __init__(self, usuario):
        super().__init__()
        self.usuario = usuario
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("Gestão de Agenda Médica")
        self.setMinimumSize(1100, 700)
        self.showMaximized()                         # ← abre maximizado

        # Widget central
        central = QWidget()
        self.setCentralWidget(central)

        layout_principal = QHBoxLayout(central)
        layout_principal.setSpacing(0)
        layout_principal.setContentsMargins(0, 0, 0, 0)

        # Menu lateral
        menu = self._criar_menu()
        layout_principal.addWidget(menu)

        # Área de conteúdo
        self.stack = QStackedWidget()
        tela_pac = TelaPacientes()
        tela_pac.abrir_consultas_semana.connect(self._filtrar_consultas_semana)
        tela_pac.abrir_exames_semana.connect(self._filtrar_exames_semana)
        tela_pac.abrir_adesao_prescricao.connect(self._abrir_adesao_prescricao)
        self.stack.addWidget(tela_pac)               # índice 0
        self.stack.addWidget(TelaConsultas())        # índice 1
        self.stack.addWidget(TelaMedicos())          # índice 2
        self.stack.addWidget(TelaExames())           # índice 3
        self.stack.addWidget(TelaMedicamentos())     # índice 4
        self.stack.addWidget(TelaPedidosExame())     # índice 5
        self.stack.addWidget(TelAdesao())            # índice 6
        tela_pend = TelaPendencias()
        tela_pend.abrir_adesao_prescricao.connect(self._abrir_adesao_prescricao)
        self.stack.addWidget(tela_pend)              # índice 7
        self.stack.addWidget(TelaResponsaveis())     # índice 8

        layout_principal.addWidget(self.stack)

    def _criar_menu(self):
        menu = QFrame()
        menu.setFixedWidth(230)
        menu.setStyleSheet("background-color: #2c3e50;")

        layout = QVBoxLayout(menu)
        layout.setSpacing(5)
        layout.setContentsMargins(10, 20, 10, 20)

        # Título do menu
        titulo = QLabel("🏥 Agenda\nMédica")
        titulo.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        titulo.setStyleSheet("color: white;")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Usuário logado
        usuario_label = QLabel(f"👤 {self.usuario.nome}")
        usuario_label.setStyleSheet("color: #bdc3c7; font-size: 11px;")
        usuario_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        usuario_label.setWordWrap(True)

        # Botões do menu — seção principal
        btn_pacientes    = self._criar_btn_menu("👴 Pacientes",        0)
        btn_consultas    = self._criar_btn_menu("📅 Consultas",        1)
        btn_exames       = self._criar_btn_menu("🧪 Exames",           3)
        btn_pedidos      = self._criar_btn_menu("📋 Pedidos de Exame", 5)
        btn_adesao       = self._criar_btn_menu("📈 Adesão",           6)
        btn_pendencias   = self._criar_btn_menu("✅ Pendências",        7)

        # Botões do menu — seção cadastros
        btn_medicos        = self._criar_btn_menu("👨‍⚕️ Médicos",          2)
        btn_medicamentos   = self._criar_btn_menu("💊 Medicamentos",      4)
        btn_responsaveis   = self._criar_btn_menu("👥 Responsáveis",      8)

        # Separador visual
        separador = QFrame()
        separador.setFrameShape(QFrame.Shape.HLine)
        separador.setStyleSheet("color: #4a6278; margin: 4px 0px;")

        lbl_cadastros = QLabel("CADASTROS")
        lbl_cadastros.setStyleSheet(
            "color: #7f8c8d; font-size: 10px; font-weight: bold; padding-left: 10px;"
        )
        lbl_cadastros.setFixedHeight(20)

        layout.addWidget(titulo)
        layout.addWidget(usuario_label)
        layout.addSpacing(20)
        layout.addWidget(btn_pacientes)
        layout.addWidget(btn_consultas)
        layout.addWidget(btn_exames)
        layout.addWidget(btn_pedidos)
        layout.addWidget(btn_adesao)
        layout.addWidget(btn_pendencias)
        layout.addSpacing(8)
        layout.addWidget(separador)
        layout.addWidget(lbl_cadastros)
        layout.addWidget(btn_medicos)
        layout.addWidget(btn_medicamentos)
        layout.addWidget(btn_responsaveis)
        layout.addStretch()

        # ── Botão de backup ───────────────────────────
        btn_backup = QPushButton("💾 Backup")
        btn_backup.setFixedHeight(28)
        btn_backup.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                padding: 0 10px;
            }
            QPushButton:hover { background-color: #2ecc71; }
            QPushButton:pressed { background-color: #1e8449; }
        """)
        btn_backup.clicked.connect(self._fazer_backup)
        layout.addWidget(btn_backup)


        return menu

    def _filtrar_consultas_semana(self, seg, dom):
        self.stack.setCurrentIndex(1)
        tela_consultas = self.stack.widget(1)
        if hasattr(tela_consultas, '_filtrar_por_periodo'):
            tela_consultas._filtrar_por_periodo(seg, dom)

    def _filtrar_exames_semana(self, seg, dom):
        self.stack.setCurrentIndex(3)
        tela_exames = self.stack.widget(3)
        if hasattr(tela_exames, '_filtrar_por_periodo'):
            tela_exames._filtrar_por_periodo(seg, dom)

    def _abrir_adesao_prescricao(self, prescricao_id: int):
        self.stack.setCurrentIndex(6)
        tela_adesao = self.stack.widget(6)
        if hasattr(tela_adesao, 'selecionar_prescricao'):
            tela_adesao.selecionar_prescricao(prescricao_id)

    def _fazer_backup(self):
        # Extrai credenciais do DATABASE_URL
        db_url = os.getenv("DATABASE_URL", "")
        try:
            # mysql+pymysql://user:pass@host:port/dbname
            sem_prefixo = db_url.split("://", 1)[1]
            user_pass, resto = sem_prefixo.split("@", 1)
            usuario, senha = user_pass.split(":", 1)
            host_port, dbname = resto.split("/", 1)
            dbname = dbname.split("?")[0]
            if ":" in host_port:
                host, port = host_port.split(":", 1)
            else:
                host, port = host_port, "3306"
        except Exception:
            QMessageBox.critical(self, "Erro", "Não foi possível ler DATABASE_URL do .env")
            return

        # Sugere nome de arquivo com data/hora
        nome_sugerido = f"backup_agenda_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        caminho, _ = QFileDialog.getSaveFileName(
            self, "Salvar backup", nome_sugerido, "SQL Files (*.sql);;All Files (*)"
        )
        if not caminho:
            return

        # Procura mysqldump no PATH e em locais comuns
        mysqldump = "mysqldump"
        locais_comuns = [
            r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe",
            r"C:\Program Files\MySQL\MySQL Server 9.4\bin\mysqldump.exe",
            r"C:\xampp\mysql\bin\mysqldump.exe",
        ]
        for loc in locais_comuns:
            if os.path.exists(loc):
                mysqldump = loc
                break

        env = os.environ.copy()
        env["MYSQL_PWD"] = senha

        cmd = [mysqldump, f"-u{usuario}", f"-h{host}", f"-P{port}", dbname]
        try:
            with open(caminho, "w", encoding="utf-8") as f:
                result = subprocess.run(
                    cmd, stdout=f, stderr=subprocess.PIPE,
                    env=env, timeout=120
                )
            if result.returncode != 0:
                erro = result.stderr.decode("utf-8", errors="replace")
                QMessageBox.critical(self, "Erro no backup", f"mysqldump falhou:\n{erro}")
                return
            tamanho = os.path.getsize(caminho) // 1024
            QMessageBox.information(
                self, "Backup concluído",
                f"Backup salvo com sucesso!\n\n{caminho}\n\nTamanho: {tamanho} KB"
            )
        except FileNotFoundError:
            QMessageBox.critical(
                self, "mysqldump não encontrado",
                "O programa mysqldump não foi encontrado.\n\n"
                "Instale o MySQL Client ou o MySQL Workbench para habilitar o backup."
            )
        except subprocess.TimeoutExpired:
            QMessageBox.critical(self, "Timeout", "O backup demorou demais. Verifique a conexão.")

    def _criar_btn_menu(self, texto: str, indice: int):
        btn = QPushButton(texto)
        btn.setFixedHeight(45)
        btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                border-radius: 5px;
                text-align: left;
                padding-left: 10px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
            QPushButton:pressed {
                background-color: #1abc9c;
            }
        """)
        btn.clicked.connect(lambda: self.stack.setCurrentIndex(indice))
        return btn
