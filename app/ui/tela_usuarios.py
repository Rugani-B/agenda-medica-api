# app/ui/tela_usuarios.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QDialog, QFormLayout, QLineEdit, QComboBox, QCheckBox,
    QListWidget, QListWidgetItem, QAbstractItemView, QSplitter,
    QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from app.database.connection import SessionLocal
from app.models.usuario import Usuario, PerfilUsuario
from app.models.pacientes import Paciente
from app.models.usuario_paciente import UsuarioPaciente


_PERFIS = [
    (PerfilUsuario.assistente, "Assistente"),
    (PerfilUsuario.familiar,   "Familiar (web)"),
    (PerfilUsuario.admin,      "Administrador"),
]

_ESTILO_TABELA = """
    QTableWidget {
        border: 1px solid #ddd;
        border-radius: 6px;
        font-size: 13px;
    }
    QHeaderView::section {
        background: #f0f0f0;
        font-weight: bold;
        padding: 6px;
        border: none;
        border-bottom: 1px solid #ccc;
    }
    QTableWidget::item { padding: 6px; }
"""


class DialogUsuario(QDialog):
    """Cria ou edita um usuário e define quais pacientes ele acessa."""

    def __init__(self, parent=None, usuario=None, pacientes=None):
        super().__init__(parent)
        self._usuario  = usuario
        self._pacientes = pacientes or []
        self.setWindowTitle("Editar usuário" if usuario else "Novo usuário")
        self.setMinimumWidth(480)
        self._build()
        if usuario:
            self._preencher()

    def _build(self):
        layout = QFormLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        self.nome  = QLineEdit()
        self.email = QLineEdit()
        self.senha = QLineEdit()
        self.senha.setEchoMode(QLineEdit.EchoMode.Password)
        self.senha.setPlaceholderText("Deixe em branco para manter a atual" if self._usuario else "")

        self.combo_perfil = QComboBox()
        for enum_val, label in _PERFIS:
            self.combo_perfil.addItem(label, enum_val)

        self.check_ativo = QCheckBox("Ativo")
        self.check_ativo.setChecked(True)

        # Lista de pacientes vinculáveis
        lbl_pac = QLabel("Pacientes com acesso:")
        lbl_pac.setStyleSheet("font-weight: bold; margin-top: 6px;")

        self.lista_pacientes = QListWidget()
        self.lista_pacientes.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.lista_pacientes.setFixedHeight(160)
        for p in self._pacientes:
            item = QListWidgetItem(p.nome)
            item.setData(Qt.ItemDataRole.UserRole, p.id)
            self.lista_pacientes.addItem(item)

        layout.addRow("Nome *", self.nome)
        layout.addRow("E-mail *", self.email)
        layout.addRow("Senha" + (" *" if not self._usuario else ""), self.senha)
        layout.addRow("Perfil", self.combo_perfil)
        layout.addRow("", self.check_ativo)
        layout.addRow(lbl_pac, QLabel(""))
        layout.addRow(self.lista_pacientes)

        dica = QLabel("Segure Ctrl para selecionar mais de um paciente.")
        dica.setStyleSheet("color: #888; font-size: 11px;")
        layout.addRow(dica)

        btns = QHBoxLayout()
        btn_ok     = QPushButton("Salvar")
        btn_cancel = QPushButton("Cancelar")
        btn_ok.setStyleSheet(
            "background:#1abc9c; color:white; padding:6px 18px; border-radius:4px;"
        )
        btn_ok.clicked.connect(self._salvar)
        btn_cancel.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_ok)
        layout.addRow(btns)

    def _preencher(self):
        u = self._usuario
        self.nome.setText(u.nome or "")
        self.email.setText(u.email or "")
        self.check_ativo.setChecked(bool(u.ativo))
        idx = next((i for i, (e, _) in enumerate(_PERFIS) if e == u.perfil), 0)
        self.combo_perfil.setCurrentIndex(idx)

    def selecionar_pacientes(self, ids: set):
        for i in range(self.lista_pacientes.count()):
            item = self.lista_pacientes.item(i)
            if item.data(Qt.ItemDataRole.UserRole) in ids:
                item.setSelected(True)

    def _salvar(self):
        if not self.nome.text().strip():
            QMessageBox.warning(self, "Atenção", "Nome é obrigatório.")
            return
        if not self.email.text().strip():
            QMessageBox.warning(self, "Atenção", "E-mail é obrigatório.")
            return
        if not self._usuario and not self.senha.text():
            QMessageBox.warning(self, "Atenção", "Senha é obrigatória para novo usuário.")
            return
        self.accept()

    def dados(self) -> dict:
        ids_sel = {
            self.lista_pacientes.item(i).data(Qt.ItemDataRole.UserRole)
            for i in range(self.lista_pacientes.count())
            if self.lista_pacientes.item(i).isSelected()
        }
        return {
            "nome":        self.nome.text().strip(),
            "email":       self.email.text().strip(),
            "senha":       self.senha.text(),
            "perfil":      self.combo_perfil.currentData(),
            "ativo":       self.check_ativo.isChecked(),
            "paciente_ids": ids_sel,
        }


class TelaUsuarios(QWidget):
    def __init__(self, usuario=None):
        super().__init__()
        self.usuario = usuario
        self._build()
        self._carregar()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        # Cabeçalho
        topo = QHBoxLayout()
        titulo = QLabel("👤 Usuários do Sistema")
        titulo.setFont(QFont("Arial", 15, QFont.Weight.Bold))
        topo.addWidget(titulo)
        topo.addStretch()

        btn_novo = QPushButton("+ Novo usuário")
        btn_novo.setStyleSheet(
            "background:#1abc9c; color:white; padding:6px 16px;"
            "border-radius:5px; font-size:13px;"
        )
        btn_novo.clicked.connect(self._novo)
        topo.addWidget(btn_novo)
        layout.addLayout(topo)

        sub = QLabel("Gerencie administradores e assistentes. Defina quais pacientes cada um pode acessar.")
        sub.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(sub)

        # Tabela
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(5)
        self.tabela.setHorizontalHeaderLabels(
            ["Nome", "E-mail", "Perfil", "Status", "Ações"]
        )
        hh = self.tabela.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.tabela.setColumnWidth(4, 140)
        self.tabela.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabela.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.setAlternatingRowColors(True)
        self.tabela.setStyleSheet(_ESTILO_TABELA)
        layout.addWidget(self.tabela)

    def _carregar(self):
        db = SessionLocal()
        try:
            db.rollback()
            usuarios = db.query(Usuario).order_by(Usuario.nome).all()
            pacientes = db.query(Paciente).filter_by(ativo=True).order_by(Paciente.nome).all()

            # vínculos: usuario_id → set(paciente_id)
            vinculos = {}
            for v in db.query(UsuarioPaciente).all():
                vinculos.setdefault(v.usuario_id, set()).add(v.paciente_id)

            self._usuarios  = [(u, vinculos.get(u.id, set())) for u in usuarios]
            self._pacientes = pacientes
        finally:
            db.close()

        self.tabela.setRowCount(len(self._usuarios))
        _PERFIL_LABEL = {
            PerfilUsuario.admin:      "Administrador",
            PerfilUsuario.assistente: "Assistente",
            PerfilUsuario.familiar:   "Familiar",
            PerfilUsuario.enfermeira: "Enfermeira (legado)",
            PerfilUsuario.secretaria: "Secretaria (legado)",
            PerfilUsuario.operador:   "Operador (legado)",
        }

        for row, (u, pac_ids) in enumerate(self._usuarios):
            self.tabela.setItem(row, 0, QTableWidgetItem(u.nome))
            self.tabela.setItem(row, 1, QTableWidgetItem(u.email))
            self.tabela.setItem(row, 2, QTableWidgetItem(_PERFIL_LABEL.get(u.perfil, str(u.perfil))))

            status_item = QTableWidgetItem("Ativo" if u.ativo else "Inativo")
            status_item.setForeground(
                __import__("PyQt6.QtGui", fromlist=["QColor"]).QColor(
                    "#27ae60" if u.ativo else "#e74c3c"
                )
            )
            self.tabela.setItem(row, 3, status_item)

            cell = QWidget()
            h = QHBoxLayout(cell)
            h.setContentsMargins(4, 2, 4, 2)
            h.setSpacing(4)

            btn_edit = QPushButton("✏️ Editar")
            btn_edit.setStyleSheet(
                "background:#2980b9; color:white; padding:3px 8px; border-radius:4px; font-size:11px;"
            )
            btn_edit.clicked.connect(lambda _, uid=u.id: self._editar(uid))

            btn_tog = QPushButton("🚫 Desativar" if u.ativo else "✅ Ativar")
            btn_tog.setStyleSheet(
                "background:#e67e22; color:white; padding:3px 8px; border-radius:4px; font-size:11px;"
                if u.ativo else
                "background:#27ae60; color:white; padding:3px 8px; border-radius:4px; font-size:11px;"
            )
            btn_tog.clicked.connect(lambda _, uid=u.id, at=u.ativo: self._toggle_ativo(uid, at))

            h.addWidget(btn_edit)
            h.addWidget(btn_tog)
            self.tabela.setCellWidget(row, 4, cell)
            self.tabela.setRowHeight(row, 38)

    def _novo(self):
        dlg = DialogUsuario(self, pacientes=self._pacientes)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        d = dlg.dados()
        db = SessionLocal()
        try:
            if db.query(Usuario).filter_by(email=d["email"]).first():
                QMessageBox.warning(self, "E-mail duplicado", "Já existe um usuário com este e-mail.")
                return
            u = Usuario(
                nome       = d["nome"],
                email      = d["email"],
                senha_hash = Usuario.gerar_hash(d["senha"]),
                perfil     = d["perfil"],
                ativo      = d["ativo"],
            )
            db.add(u)
            db.flush()
            for pid in d["paciente_ids"]:
                db.add(UsuarioPaciente(usuario_id=u.id, paciente_id=pid))
            db.commit()
        finally:
            db.close()
        self._carregar()

    def _editar(self, usuario_id: int):
        usuario, pac_ids_atuais = next(
            ((u, ids) for u, ids in self._usuarios if u.id == usuario_id), (None, set())
        )
        if not usuario:
            return
        dlg = DialogUsuario(self, usuario=usuario, pacientes=self._pacientes)
        dlg.selecionar_pacientes(pac_ids_atuais)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        d = dlg.dados()
        db = SessionLocal()
        try:
            u = db.query(Usuario).get(usuario_id)
            u.nome   = d["nome"]
            u.email  = d["email"]
            u.perfil = d["perfil"]
            u.ativo  = d["ativo"]
            if d["senha"]:
                u.senha_hash = Usuario.gerar_hash(d["senha"])
            # Atualiza vínculos
            db.query(UsuarioPaciente).filter_by(usuario_id=usuario_id).delete()
            for pid in d["paciente_ids"]:
                db.add(UsuarioPaciente(usuario_id=usuario_id, paciente_id=pid))
            db.commit()
        finally:
            db.close()
        self._carregar()

    def _toggle_ativo(self, usuario_id: int, ativo_atual: bool):
        acao = "desativar" if ativo_atual else "ativar"
        resp = QMessageBox.question(
            self, "Confirmar",
            f"Deseja {acao} este usuário?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if resp != QMessageBox.StandardButton.Yes:
            return
        db = SessionLocal()
        try:
            u = db.query(Usuario).get(usuario_id)
            u.ativo = not ativo_atual
            db.commit()
        finally:
            db.close()
        self._carregar()
