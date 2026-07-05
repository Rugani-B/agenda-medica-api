import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QScrollArea, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from app.database.connection import SessionLocal
from app.models.base_enums import StatusAgendamento
from app.models.consulta import Consulta
from app.models.exame import Exame, StatusExame
from app.models.pedido_exame import PedidoExame, StatusPedido
from app.models.prescricao import Prescricao
from app.models.adesao_tratamento import AdesaoTratamento


# ── Paleta por urgência ─────────────────────────────────────────────────────
URGENCIA = {
    "atrasado": {
        "header_bg": "#c0392b", "header_fg": "white",
        "card_bg":   "#fdf0ef", "card_border": "#e74c3c",
        "dot":       "#e74c3c", "label": "🔴  Atrasado / Urgente",
    },
    "semana": {
        "header_bg": "#d68910", "header_fg": "white",
        "card_bg":   "#fef9e7", "card_border": "#f39c12",
        "dot":       "#f39c12", "label": "🟡  Esta semana",
    },
    "futuro": {
        "header_bg": "#1a5276", "header_fg": "white",
        "card_bg":   "#eaf4fb", "card_border": "#2e86c1",
        "dot":       "#2e86c1", "label": "🔵  Próximos 7 dias",
    },
}

ICONES = {
    "consulta": "📅",
    "exame":    "🧪",
    "pedido":   "📋",
    "adesao":   "💊",
    "resultado": "📄",
}


def _segunda_feira(d: datetime.date) -> datetime.date:
    return d - datetime.timedelta(days=d.weekday())


class TelaPendencias(QWidget):
    # Sinais para navegação externa
    abrir_adesao_prescricao = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.db = SessionLocal()
        self._setup_ui()
        self._atualizar()

    # ── UI base ─────────────────────────────────────────────────────────────
    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(8)
        root.setContentsMargins(16, 16, 16, 16)

        # Cabeçalho
        topo = QHBoxLayout()
        titulo = QLabel("✅  Pendências e Ações")
        titulo.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        btn_refresh = QPushButton("🔄  Atualizar")
        btn_refresh.setFixedHeight(32)
        btn_refresh.setStyleSheet("""
            QPushButton {
                background:#2980b9; color:white; border-radius:4px;
                font-weight:bold; padding: 0 14px;
            }
            QPushButton:hover { background:#1a6fa8; }
        """)
        btn_refresh.clicked.connect(self._atualizar)
        topo.addWidget(titulo)
        topo.addStretch()
        topo.addWidget(btn_refresh)
        root.addLayout(topo)

        # Área rolável
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._conteudo = QWidget()
        self._lay_conteudo = QVBoxLayout(self._conteudo)
        self._lay_conteudo.setSpacing(10)
        self._lay_conteudo.setContentsMargins(0, 0, 6, 0)
        scroll.setWidget(self._conteudo)
        root.addWidget(scroll)

    # ── Coleta de pendências ─────────────────────────────────────────────────
    def _coletar(self) -> list[dict]:
        self.db.rollback()
        self.db.expire_all()

        agora     = datetime.datetime.now()
        hoje      = agora.date()
        seg_hoje  = _segunda_feira(hoje)
        amanha    = agora + datetime.timedelta(days=1)
        prox7     = agora + datetime.timedelta(days=7)
        dois_dias = agora - datetime.timedelta(days=2)
        eh_sexta_ou_depois = hoje.weekday() >= 4  # sex=4, sab=5, dom=6

        items: list[dict] = []

        # ── 1. Consultas passadas não atualizadas ──────────────────────────
        pendentes_status = [
            StatusAgendamento.agendada,
            StatusAgendamento.confirmada,
            StatusAgendamento.reagendada,
        ]
        for c in (
            self.db.query(Consulta)
            .filter(Consulta.data_hora < agora)
            .filter(Consulta.status.in_(pendentes_status))
            .order_by(Consulta.data_hora.desc())
            .all()
        ):
            items.append({
                "urgencia":  "atrasado",
                "tipo":      "consulta",
                "descricao": "Consulta não atualizada",
                "detalhe":   (
                    f"{c.paciente.nome}  —  "
                    f"{c.data_hora.strftime('%d/%m/%Y %H:%M')}  "
                    f"({c.status.value})"
                ),
                "acao":  "Editar consulta",
                "obj_id": c.id,
                "obj":   c,
            })

        # ── 2. Consultas realizadas (≤2 dias) — verificar prescrições/pedidos
        for c in (
            self.db.query(Consulta)
            .filter(Consulta.data_hora >= dois_dias)
            .filter(Consulta.data_hora < agora)
            .filter(Consulta.status == StatusAgendamento.realizada)
            .order_by(Consulta.data_hora.desc())
            .all()
        ):
            tem_presc  = bool(c.prescricoes)
            tem_pedido = bool(c.pedidos_exame)
            if not tem_presc and not tem_pedido:
                items.append({
                    "urgencia":  "semana",
                    "tipo":      "consulta",
                    "descricao": "Verificar prescrições / pedidos de exame",
                    "detalhe":   (
                        f"{c.paciente.nome}  —  "
                        f"realizada em {c.data_hora.strftime('%d/%m %H:%M')}"
                    ),
                    "acao":   "Abrir consulta",
                    "obj_id": c.id,
                    "obj":    c,
                })

        # ── 3. Exames agendados com data passada ───────────────────────────
        for e in (
            self.db.query(Exame)
            .filter(Exame.data_hora < agora)
            .filter(Exame.status == StatusExame.agendado)
            .order_by(Exame.data_hora.desc())
            .all()
        ):
            items.append({
                "urgencia":  "atrasado",
                "tipo":      "exame",
                "descricao": "Exame não atualizado (passou a data)",
                "detalhe":   (
                    f"{e.paciente.nome}  —  "
                    f"{e.tipo_exame.nome}  —  "
                    f"{e.data_hora.strftime('%d/%m/%Y %H:%M')}"
                ),
                "acao":   "Editar exame",
                "obj_id": e.id,
                "obj":    e,
            })

        # ── 4. Exames realizados sem resultado e sem anexo ─────────────────
        for e in (
            self.db.query(Exame)
            .filter(Exame.status == StatusExame.realizado)
            .order_by(Exame.data_hora.desc())
            .all()
        ):
            if not (e.resultado and e.resultado.strip()) and not e.anexos:
                items.append({
                    "urgencia":  "atrasado",
                    "tipo":      "resultado",
                    "descricao": "Resultado de exame pendente de upload",
                    "detalhe":   (
                        f"{e.paciente.nome}  —  "
                        f"{e.tipo_exame.nome}  —  "
                        f"{e.data_hora.strftime('%d/%m/%Y')}"
                    ),
                    "acao":   "Editar exame",
                    "obj_id": e.id,
                    "obj":    e,
                })

        # ── 5. Pedidos de exame não agendados ──────────────────────────────
        for p in (
            self.db.query(PedidoExame)
            .filter(PedidoExame.status == StatusPedido.solicitado)
            .order_by(PedidoExame.criado_em)
            .all()
        ):
            items.append({
                "urgencia":  "semana",
                "tipo":      "pedido",
                "descricao": "Pedido de exame não agendado",
                "detalhe":   (
                    f"{p.paciente.nome}  —  "
                    f"{p.tipo_exame.nome}"
                    + ("  🚨 urgente" if p.urgente else "")
                ),
                "acao":   "Ver pedido",
                "obj_id": p.id,
                "obj":    p,
            })

        # ── 6. Adesão semanal a registrar ──────────────────────────────────
        prescricoes_ativas = (
            self.db.query(Prescricao)
            .filter(Prescricao.semana_inicio.isnot(None))
            .filter(Prescricao.semana_fim.isnot(None))
            .filter(Prescricao.semana_inicio <= seg_hoje)
            .filter(Prescricao.semana_fim >= seg_hoje)
            .all()
        )
        for presc in prescricoes_ativas:
            registro = (
                self.db.query(AdesaoTratamento)
                .filter(AdesaoTratamento.prescricao_id == presc.id)
                .filter(AdesaoTratamento.semana == seg_hoje)
                .first()
            )
            if not registro and eh_sexta_ou_depois:
                nomes = ", ".join(
                    i.medicamento.nome for i in presc.itens if i.medicamento
                ) or "Tratamento sem itens"
                items.append({
                    "urgencia":  "semana",
                    "tipo":      "adesao",
                    "descricao": "Registrar adesão semanal",
                    "detalhe":   f"{presc.paciente.nome}  —  {nomes}",
                    "acao":   "Abrir adesão",
                    "obj_id": presc.id,
                    "obj":    presc,
                })

        # ── 7. Semanas passadas com adesão não registrada (últimas 4 sem.) ─
        for semanas_atras in range(1, 5):
            seg_passada = seg_hoje - datetime.timedelta(weeks=semanas_atras)
            prescricoes_passadas = (
                self.db.query(Prescricao)
                .filter(Prescricao.semana_inicio.isnot(None))
                .filter(Prescricao.semana_fim.isnot(None))
                .filter(Prescricao.semana_inicio <= seg_passada)
                .filter(Prescricao.semana_fim >= seg_passada)
                .all()
            )
            for presc in prescricoes_passadas:
                registro = (
                    self.db.query(AdesaoTratamento)
                    .filter(AdesaoTratamento.prescricao_id == presc.id)
                    .filter(AdesaoTratamento.semana == seg_passada)
                    .first()
                )
                if not registro:
                    nomes = ", ".join(
                        i.medicamento.nome for i in presc.itens if i.medicamento
                    ) or "Tratamento"
                    items.append({
                        "urgencia":  "atrasado",
                        "tipo":      "adesao",
                        "descricao": "Adesão não registrada — semana passada",
                        "detalhe":   (
                            f"{presc.paciente.nome}  —  {nomes}  —  "
                            f"sem. {seg_passada.strftime('%d/%m')}"
                        ),
                        "acao":   "Abrir adesão",
                        "obj_id": presc.id,
                        "obj":    presc,
                    })

        # ── 8. Consultas próximos 7 dias ───────────────────────────────────
        for c in (
            self.db.query(Consulta)
            .filter(Consulta.data_hora >= amanha)
            .filter(Consulta.data_hora <= prox7)
            .filter(Consulta.status.in_([
                StatusAgendamento.agendada,
                StatusAgendamento.reagendada,
            ]))
            .order_by(Consulta.data_hora)
            .all()
        ):
            dias = (c.data_hora.date() - hoje).days
            items.append({
                "urgencia":  "futuro",
                "tipo":      "consulta",
                "descricao": f"Consulta em {dias} dia{'s' if dias != 1 else ''} — confirmar com paciente",
                "detalhe":   (
                    f"{c.paciente.nome}  —  "
                    f"{c.data_hora.strftime('%d/%m/%Y %H:%M')}  "
                    f"({c.status.value})"
                ),
                "acao":   "Editar consulta",
                "obj_id": c.id,
                "obj":    c,
            })

        # ── 9. Exames agendados próximos 7 dias ────────────────────────────
        for e in (
            self.db.query(Exame)
            .filter(Exame.data_hora >= amanha)
            .filter(Exame.data_hora <= prox7)
            .filter(Exame.status == StatusExame.agendado)
            .order_by(Exame.data_hora)
            .all()
        ):
            dias = (e.data_hora.date() - hoje).days
            items.append({
                "urgencia":  "futuro",
                "tipo":      "exame",
                "descricao": f"Exame em {dias} dia{'s' if dias != 1 else ''}",
                "detalhe":   (
                    f"{e.paciente.nome}  —  "
                    f"{e.tipo_exame.nome}  —  "
                    f"{e.data_hora.strftime('%d/%m/%Y %H:%M')}"
                ),
                "acao":   "Editar exame",
                "obj_id": e.id,
                "obj":    e,
            })

        return items

    # ── Renderização ─────────────────────────────────────────────────────────
    def _limpar(self):
        while self._lay_conteudo.count():
            child = self._lay_conteudo.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def _atualizar(self):
        self._limpar()
        items = self._coletar()

        for urgencia_key in ("atrasado", "semana", "futuro"):
            grupo = [i for i in items if i["urgencia"] == urgencia_key]
            if not grupo:
                continue
            cfg = URGENCIA[urgencia_key]

            # Cabeçalho da seção
            hdr = QLabel(f"  {cfg['label']}  ({len(grupo)})")
            hdr.setFixedHeight(28)
            hdr.setStyleSheet(
                f"background:{cfg['header_bg']}; color:{cfg['header_fg']};"
                f"font-weight:bold; font-size:12px; border-radius:5px;"
                f"padding-left:8px;"
            )
            self._lay_conteudo.addWidget(hdr)

            for item in grupo:
                self._lay_conteudo.addWidget(self._criar_card(item, cfg))

        if not items:
            vazio = QLabel("✅  Nenhuma pendência encontrada.")
            vazio.setAlignment(Qt.AlignmentFlag.AlignCenter)
            vazio.setStyleSheet("color:#27ae60; font-size:14px; font-weight:bold;")
            vazio.setFixedHeight(60)
            self._lay_conteudo.addWidget(vazio)

        self._lay_conteudo.addStretch()

    def _criar_card(self, item: dict, cfg: dict) -> QFrame:
        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background:{cfg['card_bg']}; border:1px solid {cfg['card_border']};"
            f"border-radius:6px; }}"
        )
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        row = QHBoxLayout(card)
        row.setContentsMargins(10, 8, 10, 8)
        row.setSpacing(10)

        # Ícone do tipo
        icone = QLabel(ICONES.get(item["tipo"], "•"))
        icone.setFixedWidth(22)
        icone.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icone.setStyleSheet("font-size:16px; background:transparent; border:none;")

        # Textos
        txt_lay = QVBoxLayout()
        txt_lay.setSpacing(2)
        lbl_desc = QLabel(item["descricao"])
        lbl_desc.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        lbl_desc.setStyleSheet("background:transparent; border:none;")
        lbl_det = QLabel(item["detalhe"])
        lbl_det.setStyleSheet("color:#555; font-size:10px; background:transparent; border:none;")
        lbl_det.setWordWrap(True)
        txt_lay.addWidget(lbl_desc)
        txt_lay.addWidget(lbl_det)

        # Botão de ação
        btn = QPushButton(item["acao"])
        btn.setFixedHeight(28)
        btn.setFixedWidth(140)
        btn.setStyleSheet(f"""
            QPushButton {{
                background:{cfg['card_border']}; color:white;
                border-radius:4px; font-size:10px; font-weight:bold;
            }}
            QPushButton:hover {{ background:{cfg['header_bg']}; }}
        """)
        btn.clicked.connect(lambda checked=False, i=item: self._executar_acao(i))

        row.addWidget(icone)
        row.addLayout(txt_lay, stretch=1)
        row.addWidget(btn, alignment=Qt.AlignmentFlag.AlignVCenter)

        return card

    # ── Ações ────────────────────────────────────────────────────────────────
    def _executar_acao(self, item: dict):
        tipo = item["tipo"]
        obj  = item["obj"]

        if tipo in ("consulta",):
            from app.ui.components.dialogs.dialog_consulta import DialogConsulta
            dlg = DialogConsulta(self.db, obj)
            if dlg.exec():
                self._atualizar()

        elif tipo in ("exame", "resultado"):
            from app.ui.components.dialogs.dialog_exame import DialogExame
            dlg = DialogExame(self.db, exame=obj)
            if dlg.exec():
                self._atualizar()

        elif tipo == "pedido":
            from app.ui.components.dialogs.dialog_pedido_exame import DialogPedidoExame
            dlg = DialogPedidoExame(self.db, pedido=obj)
            if dlg.exec():
                self._atualizar()

        elif tipo == "adesao":
            self.abrir_adesao_prescricao.emit(item["obj_id"])
