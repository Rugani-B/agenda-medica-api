from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
    QFormLayout, QLineEdit, QTextEdit, QMessageBox, QApplication,
    QComboBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

import hashlib
import os
from dotenv import load_dotenv

from app.database.connection import SessionLocal
from app.models.responsavel import Responsavel
from app.models.pacientes import Paciente

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "chave-secreta-padrao")
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def _gerar_token(responsavel_id: int) -> str:
    raw = f"{responsavel_id}:{SECRET_KEY}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def _gerar_link(responsavel_id: int) -> str:
    token = _gerar_token(responsavel_id)
    return f"{BASE_URL}/familia/?token={token}&responsavel_id={responsavel_id}"


def _carregar_pacientes(db):
    return db.query(Paciente).order_by(Paciente.nome).all()


class DialogResponsavel(QDialog):
    def __init__(self, parent=None, responsavel=None):
        super().__init__(parent)
        self.responsavel = responsavel
        self.setWindowTitle("Editar Responsável" if responsavel else "Novo Responsável")
        self.setMinimumWidth(420)
        self._pacientes = []
        self._build()

    def _build(self):
        layout = QFormLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        # Seletor de paciente
        self.combo_paciente = QComboBox()
        db = SessionLocal()
        try:
            self._pacientes = _carregar_pacientes(db)
            for p in self._pacientes:
                self.combo_paciente.addItem(p.nome, p.id)
        finally:
            db.close()

        if self.responsavel:
            idx = next(
                (i for i, p in enumerate(self._pacientes) if p.id == self.responsavel.paciente_id),
                0
            )
            self.combo_paciente.setCurrentIndex(idx)
            self.combo_paciente.setEnabled(False)  # não permite trocar o paciente na edição

        self.nome       = QLineEdit()
        self.parentesco = QLineEdit()
        self.telefone   = QLineEdit()
        self.whatsapp   = QLineEdit()
        self.email      = QLineEdit()
        self.obs        = QTextEdit()
        self.obs.setFixedHeight(60)

        if self.responsavel:
            self.nome.setText(self.responsavel.nome or "")
            self.parentesco.setText(self.responsavel.parentesco or "")
            self.telefone.setText(self.responsavel.telefone or "")
            self.whatsapp.setText(self.responsavel.whatsapp or "")
            self.email.setText(self.responsavel.email or "")
            self.obs.setPlainText(self.responsavel.observacoes or "")

        layout.addRow("Paciente *", self.combo_paciente)
        layout.addRow("Nome *", self.nome)
        layout.addRow("Parentesco", self.parentesco)
        layout.addRow("Telefone", self.telefone)
        layout.addRow("WhatsApp", self.whatsapp)
        layout.addRow("E-mail", self.email)
        layout.addRow("Observações", self.obs)

        btns = QHBoxLayout()
        btn_ok = QPushButton("Salvar")
        btn_ok.setStyleSheet("background:#1abc9c; color:white; padding:6px 18px; border-radius:4px;")
        btn_cancel = QPushButton("Cancelar")
        btn_ok.clicked.connect(self._salvar)
        btn_cancel.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_ok)
        layout.addRow(btns)

    def _salvar(self):
        if not self.nome.text().strip():
            QMessageBox.warning(self, "Atenção", "Nome é obrigatório.")
            return
        if self.combo_paciente.currentIndex() < 0:
            QMessageBox.warning(self, "Atenção", "Selecione um paciente.")
            return
        self.accept()

    def dados(self):
        return {
            "paciente_id": self.combo_paciente.currentData(),
            "nome":        self.nome.text().strip(),
            "parentesco":  self.parentesco.text().strip(),
            "telefone":    self.telefone.text().strip(),
            "whatsapp":    self.whatsapp.text().strip(),
            "email":       self.email.text().strip(),
            "observacoes": self.obs.toPlainText().strip(),
        }


class TelaResponsaveis(QWidget):
    def __init__(self):
        super().__init__()
        self._responsaveis = []
        self._pacientes = {}
        self._build()
        self._carregar()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        topo = QHBoxLayout()
        titulo = QLabel("👥 Responsáveis / Familiares")
        titulo.setFont(QFont("Arial", 15, QFont.Weight.Bold))
        topo.addWidget(titulo)
        topo.addStretch()

        btn_novo = QPushButton("+ Novo responsável")
        btn_novo.setStyleSheet(
            "background:#1abc9c; color:white; padding:6px 16px; border-radius:5px; font-size:13px;"
        )
        btn_novo.clicked.connect(self._novo)
        topo.addWidget(btn_novo)
        layout.addLayout(topo)

        sub = QLabel("Gerencie quem pode acessar a agenda de cada paciente pelo link da família.")
        sub.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(sub)

        self.tabela = QTableWidget()
        self.tabela.setColumnCount(7)
        self.tabela.setHorizontalHeaderLabels(
            ["Paciente", "Nome", "Parentesco", "Telefone", "WhatsApp", "E-mail", "Ações"]
        )
        self.tabela.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tabela.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabela.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.tabela.setColumnWidth(6, 240)
        self.tabela.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabela.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.setAlternatingRowColors(True)
        self.tabela.setStyleSheet("""
            QTableWidget { border: 1px solid #ddd; border-radius: 6px; font-size: 13px; }
            QHeaderView::section { background: #f0f0f0; font-weight: bold; padding: 6px; border: none; border-bottom: 1px solid #ccc; }
            QTableWidget::item { padding: 6px; }
        """)
        layout.addWidget(self.tabela)

        info = QLabel("💡 Clique em 'Copiar link' para obter o link de acesso do familiar.")
        info.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(info)

    def _carregar(self):
        db = SessionLocal()
        try:
            db.rollback()
            db.expire_all()
            responsaveis = db.query(Responsavel).order_by(Responsavel.nome).all()
            paciente_ids = {r.paciente_id for r in responsaveis}
            pacientes = {
                p.id: p for p in db.query(Paciente).filter(Paciente.id.in_(paciente_ids)).all()
            }
            # mantém dados em memória
            dados = []
            for r in responsaveis:
                pac = pacientes.get(r.paciente_id)
                dados.append({
                    "id":          r.id,
                    "paciente_id": r.paciente_id,
                    "paciente":    pac.nome if pac else "",
                    "nome":        r.nome or "",
                    "parentesco":  r.parentesco or "",
                    "telefone":    r.telefone or "",
                    "whatsapp":    r.whatsapp or "",
                    "email":       r.email or "",
                    "observacoes": r.observacoes or "",
                })
            self._dados = dados
        finally:
            db.close()

        self.tabela.setRowCount(len(self._dados))
        for row, d in enumerate(self._dados):
            self.tabela.setItem(row, 0, QTableWidgetItem(d["paciente"]))
            self.tabela.setItem(row, 1, QTableWidgetItem(d["nome"]))
            self.tabela.setItem(row, 2, QTableWidgetItem(d["parentesco"]))
            self.tabela.setItem(row, 3, QTableWidgetItem(d["telefone"]))
            self.tabela.setItem(row, 4, QTableWidgetItem(d["whatsapp"]))
            self.tabela.setItem(row, 5, QTableWidgetItem(d["email"]))

            cell = QWidget()
            h = QHBoxLayout(cell)
            h.setContentsMargins(4, 2, 4, 2)
            h.setSpacing(4)

            btn_link = QPushButton("🔗 Copiar link")
            btn_link.setStyleSheet(
                "background:#2980b9; color:white; padding:3px 8px; border-radius:4px; font-size:11px;"
            )
            btn_link.clicked.connect(lambda _, rid=d["id"]: self._copiar_link(rid))

            btn_edit = QPushButton("✏️")
            btn_edit.setFixedWidth(32)
            btn_edit.setStyleSheet(
                "background:#f0ad4e; color:white; border-radius:4px; font-size:11px;"
            )
            btn_edit.clicked.connect(lambda _, rid=d["id"]: self._editar(rid))

            btn_del = QPushButton("🗑")
            btn_del.setFixedWidth(32)
            btn_del.setStyleSheet(
                "background:#e74c3c; color:white; border-radius:4px; font-size:11px;"
            )
            btn_del.clicked.connect(lambda _, rid=d["id"]: self._excluir(rid))

            h.addWidget(btn_link)
            h.addWidget(btn_edit)
            h.addWidget(btn_del)
            self.tabela.setCellWidget(row, 6, cell)

        self.tabela.resizeRowsToContents()

    def _copiar_link(self, responsavel_id: int):
        link = _gerar_link(responsavel_id)
        QApplication.clipboard().setText(link)
        QMessageBox.information(
            self, "Link copiado",
            f"Link copiado para a área de transferência:\n\n{link}"
        )

    def _novo(self):
        dlg = DialogResponsavel(self)
        if not dlg._pacientes:
            QMessageBox.warning(self, "Atenção", "Nenhum paciente cadastrado.")
            return
        if dlg.exec() == QDialog.DialogCode.Accepted:
            dados = dlg.dados()
            db = SessionLocal()
            try:
                novo = Responsavel(**dados)
                db.add(novo)
                db.commit()
            finally:
                db.close()
            self._carregar()

    def _editar(self, responsavel_id: int):
        d = next((x for x in self._dados if x["id"] == responsavel_id), None)
        if not d:
            return

        # Cria um objeto temporário para passar ao dialog
        class _R:
            pass
        r = _R()
        for k, v in d.items():
            setattr(r, k, v)

        dlg = DialogResponsavel(self, responsavel=r)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            dados = dlg.dados()
            db = SessionLocal()
            try:
                obj = db.query(Responsavel).get(responsavel_id)
                for k, v in dados.items():
                    setattr(obj, k, v)
                db.commit()
            finally:
                db.close()
            self._carregar()

    def _excluir(self, responsavel_id: int):
        d = next((x for x in self._dados if x["id"] == responsavel_id), None)
        nome = d["nome"] if d else "este responsável"
        resp = QMessageBox.question(
            self, "Confirmar exclusão",
            f"Excluir '{nome}'? O link de acesso dele deixará de funcionar.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if resp == QMessageBox.StandardButton.Yes:
            db = SessionLocal()
            try:
                obj = db.query(Responsavel).get(responsavel_id)
                db.delete(obj)
                db.commit()
            finally:
                db.close()
            self._carregar()
