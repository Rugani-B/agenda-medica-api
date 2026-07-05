# app/ui/tela_login.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import os

from app.database.connection import SessionLocal
from app.services.auth_service import AuthService


class TelaLogin(QWidget):
    def __init__(self, ao_logar):
        super().__init__()
        self.ao_logar = ao_logar
        self.db       = SessionLocal()
        self.service  = AuthService(self.db)
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("Gestão de Agenda Médica")
        self.setFixedSize(520, 500)

        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(60, 40, 60, 40)

        # ── Título ─────────────────────────────────────
        titulo = QLabel("🏥 Agenda Médica")
        titulo.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setMinimumHeight(50)          # ← garante altura suficiente
        titulo.setWordWrap(True)             # ← quebra linha se necessário
        titulo.setContentsMargins(0, 0, 0, 20)

        subtitulo = QLabel("Faça login para continuar")
        subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitulo.setStyleSheet("color: gray; font-size: 11px;")
        subtitulo.setContentsMargins(0, 0, 0, 10)

        # ── E-mail ─────────────────────────────────────
        lbl_email = QLabel("E-mail:")
        lbl_email.setFont(QFont("Arial", 10, QFont.Weight.Bold))

        self.input_email = QLineEdit()
        self.input_email.setPlaceholderText("Digite seu e-mail")
        self.input_email.setFixedHeight(40)

        # ── Senha ──────────────────────────────────────
        lbl_senha = QLabel("Senha:")
        lbl_senha.setFont(QFont("Arial", 10, QFont.Weight.Bold))

        self.input_senha = QLineEdit()
        self.input_senha.setPlaceholderText("Digite sua senha")
        self.input_senha.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_senha.setFixedHeight(40)
        self.input_senha.returnPressed.connect(self._fazer_login)

        # ── Botão Entrar ───────────────────────────────
        btn_login = QPushButton("Entrar")
        btn_login.setFixedHeight(42)
        btn_login.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        btn_login.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        btn_login.clicked.connect(self._fazer_login)

        # ── Montagem do layout ─────────────────────────
        layout.addWidget(titulo)
        layout.addWidget(subtitulo)
        layout.addWidget(lbl_email)
        layout.addWidget(self.input_email)
        layout.addSpacing(5)
        layout.addWidget(lbl_senha)
        layout.addWidget(self.input_senha)
        layout.addSpacing(15)
        layout.addWidget(btn_login)

        # ── Botão Dev (só em desenvolvimento) ─────────
        if os.getenv("APP_ENV") != "production":
            layout.addSpacing(20)
            separador = QLabel("─────────── dev ───────────")
            separador.setAlignment(Qt.AlignmentFlag.AlignCenter)
            separador.setStyleSheet("color: #cccccc; font-size: 10px;")

            btn_dev = QPushButton("🔧 Dev Login")
            btn_dev.setFixedHeight(30)
            btn_dev.setStyleSheet("""
                QPushButton {
                    color: gray;
                    font-size: 10px;
                    border: 1px dashed gray;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #f0f0f0;
                }
            """)
            btn_dev.clicked.connect(self._dev_login)

            layout.addWidget(separador)
            layout.addWidget(btn_dev)

        self.setLayout(layout)

    def _fazer_login(self):
        email = self.input_email.text().strip()
        senha = self.input_senha.text().strip()

        if not email or not senha:
            QMessageBox.warning(self, "Atenção", "Preencha e-mail e senha.")
            return

        try:
            usuario = self.service.login(email, senha)
            self.ao_logar(usuario)
            self.close()
        except ValueError as e:
            QMessageBox.critical(self, "Erro", str(e))

    def _dev_login(self):
        """Preenche e loga automaticamente — apenas para desenvolvimento."""
        self.input_email.setText("admin@agenda.com")
        self.input_senha.setText("123456")
        self._fazer_login()
