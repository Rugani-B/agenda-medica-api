import datetime
from collections import defaultdict

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QLabel, QMessageBox, QSplitter,
    QFrame, QScrollArea, QGridLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor

from app.database.connection import SessionLocal
from app.services.paciente_service import PacienteService
from app.services.consulta_service import ConsultaService
from app.repositorios.exame_repository import ExameRepository
from app.repositorios.prescricao_repository import PrescricaoRepository
from app.services.adesao_service import AdesaoService
from app.models.adesao_tratamento import NIVEL_PCT
from app.ui.components.dialogs.dialog_paciente import DialogPaciente
from app.ui.components.dialogs.dialog_relatorio import DialogRelatorio

# Cores de adesão (mesmas de tela_adesao.py)
_COR_ADESAO = {
    0:   "#888780",
    25:  "#E24B4A",
    50:  "#EF9F27",
    75:  "#378ADD",
    100: "#639922",
}

def _cor_adesao(media: float) -> str:
    if media == 0:   return _COR_ADESAO[0]
    if media <= 25:  return _COR_ADESAO[25]
    if media <= 50:  return _COR_ADESAO[50]
    if media <= 75:  return _COR_ADESAO[75]
    return _COR_ADESAO[100]

def _cor_clara(hex_cor: str, fator: float = 0.45) -> str:
    """Clareia uma cor hex misturando com branco."""
    h = hex_cor.lstrip("#")
    r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    r = int(r + (255 - r) * fator)
    g = int(g + (255 - g) * fator)
    b = int(b + (255 - b) * fator)
    return f"#{r:02x}{g:02x}{b:02x}"

MESES_PT = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
            "Jul", "Ago", "Set", "Out", "Nov", "Dez"]

CW = 90   # largura da célula
CH    = 62   # altura da célula — consultas
CH_EX = 72   # altura da célula — exames


def _segunda_feira(d: datetime.date) -> datetime.date:
    return d - datetime.timedelta(days=d.weekday())


def _semanas_do_ano(ano: int):
    """Retorna {mes: [segunda-feira, ...]} para o ano dado."""
    resultado = defaultdict(list)
    d = datetime.date(ano, 1, 1)
    d = _segunda_feira(d)
    while True:
        if d.year > ano:
            break
        if d.year == ano:
            resultado[d.month].append(d)
        d += datetime.timedelta(weeks=1)
    return resultado


def _medicamentos_por_semana(prescricoes, ano: int):
    """Retorna ({seg: [(nome_med, prescricao_id), ...]}, {seg: prescricao_id_topo})."""
    resultado      = defaultdict(list)   # seg -> [(nome, presc_id), ...]
    presc_id_topo  = {}                  # seg -> presc_id da primeira prescrição ativa
    mes_semanas    = _semanas_do_ano(ano)
    todas_semanas  = [seg for segs in mes_semanas.values() for seg in segs]
    for presc in prescricoes:
        if not presc.semana_inicio:
            continue
        fim  = presc.semana_fim or datetime.date.today()
        meds = [
            f"{it.medicamento.nome}" + (f" {it.dose}" if it.dose else "")
            for it in presc.itens if it.medicamento
        ]
        if not meds:
            continue
        for seg in todas_semanas:
            if presc.semana_inicio <= seg <= fim:
                for m in meds:
                    resultado[seg].append((m, presc.id))
                if seg not in presc_id_topo:
                    presc_id_topo[seg] = presc.id
    return resultado, presc_id_topo


class CelulaCalendario(QLabel):
    duplo_clique = pyqtSignal(datetime.date, datetime.date)

    def __init__(self, seg: datetime.date, dom: datetime.date, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._seg = seg
        self._dom = dom
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mouseDoubleClickEvent(self, event):
        self.duplo_clique.emit(self._seg, self._dom)
        super().mouseDoubleClickEvent(event)


class CelulaTratamento(QLabel):
    """Célula do calendário de tratamentos — emite o prescricao_id no duplo clique."""
    duplo_clique = pyqtSignal(int)

    def __init__(self, prescricao_id: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._prescricao_id = prescricao_id
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mouseDoubleClickEvent(self, event):
        self.duplo_clique.emit(self._prescricao_id)
        super().mouseDoubleClickEvent(event)


class TelaPacientes(QWidget):
    # Sinais emitidos para abrir telas filtradas
    abrir_consultas_semana  = pyqtSignal(datetime.date, datetime.date)
    abrir_exames_semana     = pyqtSignal(datetime.date, datetime.date)
    abrir_adesao_prescricao = pyqtSignal(int)   # prescricao_id

    def __init__(self):
        super().__init__()
        self.db              = SessionLocal()
        self.service         = PacienteService(self.db)
        self.svc_consulta    = ConsultaService(self.db)
        self.repo_exame      = ExameRepository(self.db)
        self.repo_prescricao = PrescricaoRepository(self.db)
        self.svc_adesao      = AdesaoService(self.db)
        self.paciente_sel    = None
        self._ano_exibido    = datetime.date.today().year
        self._todos_pacientes = []
        self._setup_ui()
        self._carregar_pacientes()

    # ── UI ────────────────────────────────────────────

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(15, 15, 15, 15)

        titulo = QLabel("👴 Pacientes")
        titulo.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        titulo.setFixedHeight(32)
        layout.addWidget(titulo)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # ── Painel esquerdo: lista de pacientes ────────
        esq = QWidget()
        esq.setMinimumWidth(200)
        esq.setMaximumWidth(300)
        esq_lay = QVBoxLayout(esq)
        esq_lay.setContentsMargins(0, 0, 0, 0)
        esq_lay.setSpacing(6)

        self.input_busca = QLineEdit()
        self.input_busca.setPlaceholderText("🔍 Buscar por nome...")
        self.input_busca.setFixedHeight(30)
        self.input_busca.textChanged.connect(self._filtrar_lista)

        # Tabela: Nome | Idade  (ID guardado em UserRole, coluna 0 oculta)
        from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(3)
        self.tabela.setHorizontalHeaderLabels(["", "Nome", "Idade"])
        self.tabela.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.tabela.setColumnWidth(0, 0)
        self.tabela.setColumnHidden(0, True)
        self.tabela.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabela.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.tabela.setColumnWidth(2, 44)
        self.tabela.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabela.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabela.setStyleSheet("""
            QTableWidget { border: 0.5px solid #ccc; border-radius: 6px; }
            QTableWidget::item:selected { background: #d6eaf8; color: #1a5276; }
        """)
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.currentCellChanged.connect(self._ao_selecionar)
        self.tabela.doubleClicked.connect(self._abrir_dialog_editar)

        # Linha de botões principais
        btn_row1 = QHBoxLayout()
        btn_novo      = QPushButton("+ Novo")
        btn_editar    = QPushButton("✏️ Editar")
        btn_relatorio = QPushButton("📄 Relatório PDF")
        btn_relatorio.setStyleSheet("background:#1a5276; color:white; border-radius:4px; padding: 0 12px;")
        btn_relatorio.setMinimumWidth(130)
        for b in (btn_novo, btn_editar, btn_relatorio):
            b.setFixedHeight(28)
        btn_novo.clicked.connect(self._abrir_dialog_novo)
        btn_editar.clicked.connect(self._abrir_dialog_editar)
        btn_relatorio.clicked.connect(self._abrir_relatorio)
        btn_row1.addWidget(btn_novo)
        btn_row1.addWidget(btn_editar)
        btn_row1.addStretch()
        btn_row1.addWidget(btn_relatorio)

        # Separador visual + botão destrutivo isolado
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color:#e0e0e0;")

        btn_excluir = QPushButton("🗑 Excluir paciente")
        btn_excluir.setFixedHeight(26)
        btn_excluir.setStyleSheet(
            "color:#922b21; background:transparent; border:1px solid #e74c3c;"
            "border-radius:4px; font-size:11px;"
        )
        btn_excluir.clicked.connect(self._desativar_paciente)
        btn_row2 = QHBoxLayout()
        btn_row2.addStretch()
        btn_row2.addWidget(btn_excluir)

        # Label de carregando
        esq_lay.addWidget(self.input_busca)
        esq_lay.addWidget(self.tabela)
        esq_lay.addLayout(btn_row1)
        esq_lay.addWidget(sep)
        esq_lay.addLayout(btn_row2)

        # ── Painel direito: calendário anual ──────────
        dir_scroll = QScrollArea()
        dir_scroll.setWidgetResizable(True)
        dir_scroll.setFrameShape(QFrame.Shape.NoFrame)

        # Widget externo que empilha loading + conteúdo
        dir_outer = QWidget()
        dir_outer_lay = QVBoxLayout(dir_outer)
        dir_outer_lay.setContentsMargins(0, 0, 0, 0)
        dir_outer_lay.setSpacing(0)

        self.lbl_loading = QLabel("⏳  Carregando...")
        self.lbl_loading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_loading.setStyleSheet(
            "color:#1a5276; font-size:15px; font-weight:bold; padding:40px;"
        )
        self.lbl_loading.setVisible(False)
        dir_outer_lay.addWidget(self.lbl_loading)

        self.cal_container = QWidget()
        self.cal_lay = QVBoxLayout(self.cal_container)
        self.cal_lay.setContentsMargins(12, 0, 0, 0)
        self.cal_lay.setSpacing(6)
        self.cal_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._mostrar_placeholder()
        dir_outer_lay.addWidget(self.cal_container)

        dir_scroll.setWidget(dir_outer)

        splitter.addWidget(esq)
        splitter.addWidget(dir_scroll)
        splitter.setSizes([240, 760])
        layout.addWidget(splitter)

    # ── Lista de pacientes ─────────────────────────────

    def _carregar_pacientes(self):
        self._todos_pacientes = self.service.buscar_ativos()
        self._popular_tabela(self._todos_pacientes)

    def _popular_tabela(self, pacientes):
        from PyQt6.QtWidgets import QTableWidgetItem
        self.tabela.setRowCount(0)
        for p in pacientes:
            row = self.tabela.rowCount()
            self.tabela.insertRow(row)
            # Col 0 oculta: guarda o ID via UserRole
            id_item = QTableWidgetItem()
            id_item.setData(Qt.ItemDataRole.UserRole, p.id)
            self.tabela.setItem(row, 0, id_item)
            self.tabela.setItem(row, 1, QTableWidgetItem(p.nome))
            idade_item = QTableWidgetItem(str(p.idade) if hasattr(p, 'idade') else "—")
            idade_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela.setItem(row, 2, idade_item)

    def _filtrar_lista(self):
        txt = self.input_busca.text().strip().lower()
        filtrados = [p for p in self._todos_pacientes
                     if not txt or txt in p.nome.lower()]
        self._popular_tabela(filtrados)

    # ── Seleção de paciente ────────────────────────────

    def _ao_selecionar(self, row, *_):
        if row < 0:
            return
        id_item = self.tabela.item(row, 0)
        if not id_item:
            return
        pac_id = id_item.data(Qt.ItemDataRole.UserRole)
        if pac_id is None:
            return

        self.tabela.selectRow(row)
        self.lbl_loading.setVisible(True)
        self.cal_container.setVisible(False)
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()

        self.paciente_sel = self.service.buscar_por_id(pac_id)
        self._renderizar_calendario()
        self.lbl_loading.setVisible(False)
        self.cal_container.setVisible(True)

    # ── Calendário anual ───────────────────────────────

    def _limpar_cal(self):
        while self.cal_lay.count():
            child = self.cal_lay.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self._limpar_layout(child.layout())

    @staticmethod
    def _limpar_layout(lay):
        while lay.count():
            c = lay.takeAt(0)
            if c.widget():
                c.widget().deleteLater()

    def _mostrar_placeholder(self):
        lbl = QLabel("← Selecione um paciente para ver o calendário de consultas.")
        lbl.setStyleSheet("color:#888; font-size:13px;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cal_lay.addWidget(lbl)

    def _renderizar_calendario(self):
        self._limpar_cal()
        p = self.paciente_sel
        if not p:
            self._mostrar_placeholder()
            return

        self.db.rollback()
        self.db.expire_all()
        consultas    = self.svc_consulta.svc_por_paciente(p.id)
        exames       = self.repo_exame.buscar_por_paciente(p.id)
        prescricoes  = self.repo_prescricao.buscar_por_paciente(p.id)

        # Agrupa por segunda-feira da semana
        por_semana  = defaultdict(list)
        exs_semana  = defaultdict(list)
        for c in consultas:
            if c.data_hora:
                seg = _segunda_feira(c.data_hora.date())
                por_semana[seg].append(c)
        for e in exames:
            if e.data_hora:
                seg = _segunda_feira(e.data_hora.date())
                exs_semana[seg].append(e)

        trat_semana, presc_id_topo = _medicamentos_por_semana(prescricoes, self._ano_exibido)
        adesao_por_semana = {}
        for presc in prescricoes:
            for a in self.svc_adesao.buscar_por_prescricao(presc.id):
                nivel_str = a.nivel.value if hasattr(a.nivel, 'value') else a.nivel
                adesao_por_semana[(presc.id, a.semana)] = NIVEL_PCT.get(nivel_str, 0)

        # Cabeçalho com navegação de ano
        nav = QHBoxLayout()
        nav.setSpacing(4)
        lbl_pac = QLabel(f"📅  {p.nome}")
        lbl_pac.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        btn_prev = QPushButton("‹ " + str(self._ano_exibido - 1))
        btn_prev.setFixedSize(60, 22)
        btn_prev.setStyleSheet(
            "QPushButton{background:transparent;border:0.5px solid #ccc;"
            "border-radius:4px;color:#999;font-size:11px;}"
            "QPushButton:hover{background:#f0f0f0;color:#555;}"
        )
        btn_prev.clicked.connect(lambda: self._mudar_ano(-1))
        self._lbl_ano = QLabel(str(self._ano_exibido))
        self._lbl_ano.setFixedWidth(40)
        self._lbl_ano.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_ano.setStyleSheet("font-size:12px; color:#555; font-weight:bold;")
        btn_next = QPushButton(str(self._ano_exibido + 1) + " ›")
        btn_next.setFixedSize(60, 22)
        btn_next.setStyleSheet(
            "QPushButton{background:transparent;border:0.5px solid #ccc;"
            "border-radius:4px;color:#999;font-size:11px;}"
            "QPushButton:hover{background:#f0f0f0;color:#555;}"
        )
        btn_next.clicked.connect(lambda: self._mudar_ano(+1))
        # Título à esquerda, nav à direita
        lbl_titulo_cal = QLabel("Histórico de Consultas")
        lbl_titulo_cal.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        lbl_titulo_cal.setStyleSheet("color:#2c3e50;")
        nav.addWidget(lbl_titulo_cal)
        nav.addStretch()
        nav.addWidget(btn_prev)
        nav.addWidget(self._lbl_ano)
        nav.addWidget(btn_next)
        nav_w = QWidget()
        nav_w.setLayout(nav)
        self.cal_lay.addWidget(nav_w)

        # Matriz de consultas
        self._matriz_container = QWidget()
        self._matriz_lay = QVBoxLayout(self._matriz_container)
        self._matriz_lay.setContentsMargins(0, 0, 0, 0)
        self._matriz_lay.addWidget(self._widget_matriz_consultas(por_semana))
        self.cal_lay.addWidget(self._matriz_container)

        # Título exames
        lbl_ex = QLabel("▶  Exames realizados")
        lbl_ex.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        lbl_ex.setStyleSheet("color:#6e2fa0; margin-top:10px;")
        self.cal_lay.addWidget(lbl_ex)

        # Matriz de exames
        self._matriz_ex_container = QWidget()
        self._matriz_ex_lay = QVBoxLayout(self._matriz_ex_container)
        self._matriz_ex_lay.setContentsMargins(0, 0, 0, 0)
        self._matriz_ex_lay.addWidget(self._widget_matriz_exames(exs_semana))
        self.cal_lay.addWidget(self._matriz_ex_container)

        # Título tratamentos
        lbl_trat = QLabel("💊  Tratamentos")
        lbl_trat.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        lbl_trat.setStyleSheet("color:#b7770d; margin-top:10px;")
        self.cal_lay.addWidget(lbl_trat)

        # Matriz de tratamentos
        self._matriz_trat_container = QWidget()
        self._matriz_trat_lay = QVBoxLayout(self._matriz_trat_container)
        self._matriz_trat_lay.setContentsMargins(0, 0, 0, 0)
        self._matriz_trat_lay.addWidget(self._widget_matriz_tratamentos((trat_semana, presc_id_topo, adesao_por_semana)))
        self.cal_lay.addWidget(self._matriz_trat_container)
        self.cal_lay.addStretch()

    def _widget_matriz_consultas(self, por_semana: dict) -> QWidget:
        semana_hoje = _segunda_feira(datetime.date.today())
        mes_semanas = _semanas_do_ano(self._ano_exibido)
        max_linhas  = max((len(v) for v in mes_semanas.values()), default=0)

        frame = QFrame()
        grid  = QGridLayout(frame)
        grid.setSpacing(3)
        grid.setContentsMargins(0, 0, 0, 0)

        for col, nome_mes in enumerate(MESES_PT):
            lbl = QLabel(nome_mes)
            lbl.setFixedSize(QSize(CW, 20))
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(
                "background:#2c3e50; color:white; font-size:11px;"
                "font-weight:bold; border-radius:4px;"
            )
            grid.addWidget(lbl, 0, col)

        for linha in range(max_linhas):
            for col in range(12):
                mes = col + 1
                semanas_do_mes = mes_semanas.get(mes, [])
                if linha >= len(semanas_do_mes):
                    vazio = QLabel()
                    vazio.setFixedSize(QSize(CW, CH))
                    grid.addWidget(vazio, linha + 1, col)
                    continue

                seg = semanas_do_mes[linha]
                dom = seg + datetime.timedelta(days=6)
                iso_sem = seg.isocalendar()[1]
                hoje = seg == semana_hoje
                consultas_sem = por_semana.get(seg, [])

                cel = CelulaCalendario(seg, dom)
                cel.duplo_clique.connect(self._abrir_consultas_semana)
                cel.setFixedSize(QSize(CW, CH))
                cel.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
                cel.setWordWrap(True)
                cel.setContentsMargins(4, 3, 2, 2)

                linhas_txt = [f"<span style='color:#aaa;font-size:9px'>Sem. {iso_sem:02d}  {seg.strftime('%d/%m')}</span>"]
                for c in consultas_sem:
                    esp = ""
                    if c.medico and c.medico.especialidade:
                        esp = c.medico.especialidade.nome
                    elif c.medico:
                        esp = c.medico.nome
                    if esp:
                        linhas_txt.append(
                            f"<span style='color:#1a5276;font-size:9px'>• {esp}</span>"
                        )
                cel.setText("<br>".join(linhas_txt))

                borda_hoje = "border: 2px solid #111;" if hoje else "border: 0.5px solid #ddd;"
                bg, cor_txt = ("#d5f5e3", "#1e8449") if consultas_sem else ("#f8f9fa", "#888")
                cel.setStyleSheet(
                    f"background:{bg}; border-radius:5px; {borda_hoje}"
                    f"color:{cor_txt}; font-size:10px;"
                )
                grid.addWidget(cel, linha + 1, col)

        return frame

    def _widget_matriz_exames(self, exs_semana: dict) -> QWidget:
        semana_hoje = _segunda_feira(datetime.date.today())
        mes_semanas = _semanas_do_ano(self._ano_exibido)
        max_linhas  = max((len(v) for v in mes_semanas.values()), default=0)

        frame = QFrame()
        grid  = QGridLayout(frame)
        grid.setSpacing(3)
        grid.setContentsMargins(0, 0, 0, 0)

        for col, nome_mes in enumerate(MESES_PT):
            lbl = QLabel(nome_mes)
            lbl.setFixedSize(QSize(CW, 20))
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(
                "background:#5b2c8d; color:white; font-size:11px;"
                "font-weight:bold; border-radius:4px;"
            )
            grid.addWidget(lbl, 0, col)

        for linha in range(max_linhas):
            for col in range(12):
                mes = col + 1
                semanas_do_mes = mes_semanas.get(mes, [])
                if linha >= len(semanas_do_mes):
                    vazio = QLabel()
                    vazio.setFixedSize(QSize(CW, CH_EX))
                    grid.addWidget(vazio, linha + 1, col)
                    continue

                seg = semanas_do_mes[linha]
                dom = seg + datetime.timedelta(days=6)
                iso_sem = seg.isocalendar()[1]
                hoje = seg == semana_hoje
                exames_sem = exs_semana.get(seg, [])

                cel = CelulaCalendario(seg, dom)
                cel.duplo_clique.connect(self._abrir_exames_semana)
                cel.setFixedSize(QSize(CW, CH_EX))
                cel.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
                cel.setWordWrap(True)
                cel.setContentsMargins(4, 3, 2, 2)

                linhas_txt = [f"<b>Sem. {iso_sem:02d}</b>  {seg.strftime('%d/%m')}"]
                for e in exames_sem:
                    nome_ex = e.tipo_exame.nome if e.tipo_exame else "Exame"
                    linhas_txt.append(
                        f"<span style='color:#6e2fa0;font-size:9px;font-style:italic'>"
                        f"▶ {nome_ex}</span>"
                    )
                cel.setText("<br>".join(linhas_txt))

                borda_hoje = "border: 2px solid #111;" if hoje else "border: 0.5px solid #ddd;"
                bg, cor_txt = ("#ede0f7", "#6e2fa0") if exames_sem else ("#faf8fc", "#bbb")
                cel.setStyleSheet(
                    f"background:{bg}; border-radius:5px; {borda_hoje}"
                    f"color:{cor_txt}; font-size:10px;"
                )
                grid.addWidget(cel, linha + 1, col)

        return frame

    def _widget_matriz_tratamentos(self, args) -> QWidget:
        trat_semana, presc_id_topo, adesao_por_semana = args
        semana_hoje = _segunda_feira(datetime.date.today())
        mes_semanas = _semanas_do_ano(self._ano_exibido)
        max_linhas  = max((len(v) for v in mes_semanas.values()), default=0)

        frame = QFrame()
        grid  = QGridLayout(frame)
        grid.setSpacing(3)
        grid.setContentsMargins(0, 0, 0, 0)

        for col, nome_mes in enumerate(MESES_PT):
            lbl = QLabel(nome_mes)
            lbl.setFixedSize(QSize(CW, 20))
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(
                "background:#7d5a0a; color:white; font-size:11px;"
                "font-weight:bold; border-radius:4px;"
            )
            grid.addWidget(lbl, 0, col)

        from PyQt6.QtGui import QFontMetrics

        for linha in range(max_linhas):
            for col in range(12):
                mes = col + 1
                semanas_do_mes = mes_semanas.get(mes, [])
                if linha >= len(semanas_do_mes):
                    vazio = QLabel()
                    vazio.setFixedSize(QSize(CW, CH_EX))
                    grid.addWidget(vazio, linha + 1, col)
                    continue

                seg = semanas_do_mes[linha]
                iso_sem = seg.isocalendar()[1]
                hoje = seg == semana_hoje
                meds = trat_semana.get(seg, [])          # [(nome, presc_id), ...]
                presc_id = presc_id_topo.get(seg)

                media    = adesao_por_semana.get((presc_id, seg)) if presc_id else None
                cor_ad   = _cor_adesao(media) if (meds and presc_id and media is not None) else None
                cor_clar = _cor_clara(cor_ad) if cor_ad else None

                borda_hoje = "border: 2px solid #111;" if hoje else "border: 0.5px solid #ddd;"
                bg = "#fef3d0" if meds else "#fdfaf3"

                # Contentor clicável
                if presc_id:
                    container = CelulaTratamento(presc_id)
                    container.duplo_clique.connect(self._abrir_adesao)
                else:
                    container = QLabel()

                container.setFixedSize(QSize(CW, CH_EX))
                container.setStyleSheet(
                    f"background:{bg}; border-radius:5px; {borda_hoje} border-style:solid;"
                )

                inner = QVBoxLayout(container)
                inner.setContentsMargins(4, 3, 4, 2)
                inner.setSpacing(1)

                # Cabeçalho discreto
                lbl_sem = QLabel(f"Sem. {iso_sem:02d}  {seg.strftime('%d/%m')}")
                lbl_sem.setWordWrap(False)
                lbl_sem.setStyleSheet("color:#bbb; font-size:9px; background:transparent; border:none;")
                inner.addWidget(lbl_sem)

                # Nomes dos medicamentos
                fm = QFontMetrics(container.font())
                max_px = CW - 10
                for nome, _ in meds:
                    txt = fm.elidedText(f"• {nome}", Qt.TextElideMode.ElideRight, max_px)
                    lm = QLabel(txt)
                    lm.setWordWrap(False)
                    lm.setStyleSheet("color:#7d5a0a; font-size:9px; background:transparent; border:none;")
                    inner.addWidget(lm)

                inner.addStretch()

                # Barra grossa com percentual sobreposto
                if cor_ad and media is not None:
                    cor_pct = _cor_clara(cor_ad, 0.65)  # bem claro para ficar legível dentro da barra
                    barra_w = QWidget()
                    barra_w.setFixedHeight(14)
                    barra_w.setStyleSheet("background:transparent; border:none;")
                    barra_lay = QHBoxLayout(barra_w)
                    barra_lay.setContentsMargins(0, 0, 0, 0)
                    barra_lay.setSpacing(0)

                    # Fundo da barra (container relativo)
                    barra_outer = QFrame()
                    barra_outer.setFixedHeight(14)
                    barra_outer.setStyleSheet(
                        "background:#e8e0cc; border-radius:3px; border:none;"
                    )
                    b_lay = QHBoxLayout(barra_outer)
                    b_lay.setContentsMargins(0, 0, 0, 0)
                    b_lay.setSpacing(0)

                    fill_w = max(4, int((CW - 8) * media / 100))
                    barra_fill = QFrame(barra_outer)
                    barra_fill.setFixedSize(fill_w, 14)
                    barra_fill.move(0, 0)
                    barra_fill.setStyleSheet(
                        f"background:{cor_ad}; border-radius:3px; border:none;"
                    )

                    pct_lbl = QLabel(f"{media:.0f}%", barra_outer)
                    pct_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    pct_lbl.setGeometry(0, 0, CW - 8, 14)
                    pct_lbl.setStyleSheet(
                        f"font-size:9px; font-weight:bold; color:{cor_pct};"
                        f"background:transparent; border:none;"
                    )

                    barra_lay.addWidget(barra_outer)
                    inner.addWidget(barra_w)

                grid.addWidget(container, linha + 1, col)

        return frame

    def _mudar_ano(self, delta: int):
        self._ano_exibido += delta
        if hasattr(self, '_lbl_ano'):
            self._lbl_ano.setText(str(self._ano_exibido))
        if not self.paciente_sel:
            return
        self.db.rollback()
        self.db.expire_all()
        consultas   = self.svc_consulta.svc_por_paciente(self.paciente_sel.id)
        exames      = self.repo_exame.buscar_por_paciente(self.paciente_sel.id)
        prescricoes = self.repo_prescricao.buscar_por_paciente(self.paciente_sel.id)
        por_semana  = defaultdict(list)
        exs_semana  = defaultdict(list)
        for c in consultas:
            if c.data_hora:
                seg = _segunda_feira(c.data_hora.date())
                por_semana[seg].append(c)
        for e in exames:
            if e.data_hora:
                seg = _segunda_feira(e.data_hora.date())
                exs_semana[seg].append(e)
        trat_semana, presc_id_topo = _medicamentos_por_semana(prescricoes, self._ano_exibido)
        adesao_por_semana = {}
        for presc in prescricoes:
            for a in self.svc_adesao.buscar_por_prescricao(presc.id):
                nivel_str = a.nivel.value if hasattr(a.nivel, 'value') else a.nivel
                adesao_por_semana[(presc.id, a.semana)] = NIVEL_PCT.get(nivel_str, 0)
        for lay, widget_fn, arg in [
            (self._matriz_lay,      self._widget_matriz_consultas,               por_semana),
            (self._matriz_ex_lay,   self._widget_matriz_exames,                  exs_semana),
            (self._matriz_trat_lay, self._widget_matriz_tratamentos, (trat_semana, presc_id_topo, adesao_por_semana)),
        ]:
            while lay.count():
                child = lay.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            lay.addWidget(widget_fn(arg))

    def _abrir_consultas_semana(self, seg: datetime.date, dom: datetime.date):
        self.abrir_consultas_semana.emit(seg, dom)

    def _abrir_exames_semana(self, seg: datetime.date, dom: datetime.date):
        self.abrir_exames_semana.emit(seg, dom)

    def _abrir_adesao(self, prescricao_id: int):
        self.abrir_adesao_prescricao.emit(prescricao_id)

    # ── Ações CRUD ────────────────────────────────────

    def _abrir_dialog_novo(self):
        dlg = DialogPaciente(self.db)
        if dlg.exec():
            self._carregar_pacientes()

    def _abrir_dialog_editar(self):
        row = self.tabela.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione um paciente.")
            return
        pac_id  = self.tabela.item(row, 0).data(Qt.ItemDataRole.UserRole)
        paciente = self.service.buscar_por_id(pac_id)
        dlg = DialogPaciente(self.db, paciente)
        if dlg.exec():
            self._carregar_pacientes()

    def _desativar_paciente(self):
        row = self.tabela.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione um paciente.")
            return
        nome   = self.tabela.item(row, 1).text()
        pac_id = self.tabela.item(row, 0).data(Qt.ItemDataRole.UserRole)

        # Passo 1 — aviso geral
        r1 = QMessageBox.warning(
            self, "⚠️ Atenção",
            f"Você está prestes a <b>excluir permanentemente</b> o paciente:<br><br>"
            f"<b>{nome}</b><br><br>"
            "Esta ação removerá <b>todas</b> as consultas, prescrições, exames e "
            "registros de adesão vinculados a este paciente.<br><br>"
            "<b>Não há como desfazer esta operação.</b>",
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
        )
        if r1 != QMessageBox.StandardButton.Ok:
            return

        # Passo 2 — aviso de backup
        r2 = QMessageBox.warning(
            self, "⚠️ Sem backup automático",
            "Você realizou um backup recente do banco de dados?<br><br>"
            "<b>Não há backup automático.</b> Se excluir agora sem ter feito backup, "
            "os dados de <b>{}</b> serão perdidos para sempre.".format(nome),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if r2 != QMessageBox.StandardButton.Yes:
            QMessageBox.information(
                self, "Operação cancelada",
                "Faça um backup pelo menu <b>💾 Backup</b> antes de excluir o paciente."
            )
            return

        # Passo 3 — confirmação final
        r3 = QMessageBox.critical(
            self, "Confirmação final",
            f"ÚLTIMA CHANCE — confirma a exclusão permanente de <b>{nome}</b>?<br><br>"
            "Clique em <b>Sim</b> para excluir definitivamente.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if r3 != QMessageBox.StandardButton.Yes:
            return

        self.service.desativar(pac_id)
        self._carregar_pacientes()

    def _abrir_relatorio(self):
        row = self.tabela.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione um paciente.")
            return
        nome   = self.tabela.item(row, 1).text()
        pac_id = self.tabela.item(row, 0).data(Qt.ItemDataRole.UserRole)
        dlg = DialogRelatorio(pac_id, nome, parent=self)
        dlg.exec()
