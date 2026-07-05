import datetime
from collections import defaultdict

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QListWidget, QListWidgetItem, QMessageBox,
    QFrame, QScrollArea, QSizePolicy, QGridLayout,
    QLineEdit, QSplitter, QDateEdit
)
from PyQt6.QtCore import Qt, QSize, QDate, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from app.database.connection import SessionLocal
from app.services.adesao_service import AdesaoService
from app.services.prescricao_service import PrescricaoService
from app.models.adesao_tratamento import NIVEL_LABELS, NIVEL_PCT, NivelAdesao

MESES_PT = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
            "Jul", "Ago", "Set", "Out", "Nov", "Dez"]


class CelulaMatriz(QLabel):
    """QLabel com sinal de duplo clique, carregando a data da semana."""
    duplo_clique = pyqtSignal(datetime.date)

    def __init__(self, semana: datetime.date, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._semana = semana
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mouseDoubleClickEvent(self, event):
        self.duplo_clique.emit(self._semana)
        super().mouseDoubleClickEvent(event)

COR_NIVEL = {
    "nenhuma": "#888780",
    "baixa"  : "#E24B4A",
    "parcial": "#EF9F27",
    "boa"    : "#378ADD",
    "total"  : "#639922",
}
COR_TRATAMENTO   = "#d4eaf7"   # dentro do tratamento, sem registro
COR_FORA         = "#f0f0f0"   # fora do período de tratamento
COR_FORA_TEXTO   = "#c8c8c8"
COR_DENTRO_TEXTO = "#7fb3d3"


def _segunda_feira(d: datetime.date) -> datetime.date:
    return d - datetime.timedelta(days=d.weekday())


def _semanas_do_ano(ano: int):
    """Retorna todas as segundas-feiras cujo mês (da segunda-feira) cai no ano dado,
    agrupadas por mês.  Dicionário {mes: [date, ...]}."""
    resultado = defaultdict(list)
    d = datetime.date(ano, 1, 1)
    d = _segunda_feira(d)          # recua até a segunda da semana de 1/jan
    while True:
        if d.year > ano:
            break
        if d.year == ano:          # só inclui semanas cujo início é neste ano
            resultado[d.month].append(d)
        d += datetime.timedelta(weeks=1)
    return resultado


class TelAdesao(QWidget):
    def __init__(self):
        super().__init__()
        self.db             = SessionLocal()
        self.service        = AdesaoService(self.db)
        self.svc_prescricao = PrescricaoService(self.db)
        self.prescricao_sel = None
        self._ano_exibido   = datetime.date.today().year
        self._setup_ui()
        self._carregar_prescricoes()

    # ── UI principal ──────────────────────────────────

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(15, 15, 15, 15)

        titulo = QLabel("💊 Adesão ao Tratamento")
        titulo.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        titulo.setFixedHeight(32)
        layout.addWidget(titulo)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # ── Painel esquerdo ────────────────────────────
        esq = QWidget()
        esq_lay = QVBoxLayout(esq)
        esq_lay.setContentsMargins(0, 0, 0, 0)
        esq_lay.setSpacing(6)

        self.input_busca = QLineEdit()
        self.input_busca.setPlaceholderText("🔍 Buscar paciente...")
        self.input_busca.setFixedHeight(30)
        self.input_busca.textChanged.connect(self._filtrar_lista)

        self.lista = QListWidget()
        self.lista.setMinimumWidth(240)
        self.lista.setStyleSheet("""
            QListWidget { border: 0.5px solid #ccc; border-radius: 8px; background: #f8f9fa; }
            QListWidget::item { padding: 8px 12px; border-bottom: 0.5px solid #eee; min-height: 58px; }
            QListWidget::item:selected { background: #d6eaf8; color: #1a5276; }
            QListWidget::item:hover { background: #eaf4fb; }
        """)
        self.lista.currentRowChanged.connect(self._ao_selecionar)

        btn_atualizar = QPushButton("🔃 Atualizar")
        btn_atualizar.setFixedHeight(30)
        btn_atualizar.clicked.connect(self._atualizar)

        esq_lay.addWidget(self.input_busca)
        esq_lay.addWidget(self.lista)
        esq_lay.addWidget(btn_atualizar)

        # ── Painel direito (scroll) ────────────────────
        dir_scroll = QScrollArea()
        dir_scroll.setWidgetResizable(True)
        dir_scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.detalhe = QWidget()
        self.detalhe_lay = QVBoxLayout(self.detalhe)
        self.detalhe_lay.setContentsMargins(12, 0, 0, 0)
        self.detalhe_lay.setSpacing(5)
        self.detalhe_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._mostrar_placeholder()

        dir_scroll.setWidget(self.detalhe)

        splitter.addWidget(esq)
        splitter.addWidget(dir_scroll)
        splitter.setSizes([260, 700])
        layout.addWidget(splitter)

    # ── Lista de prescrições ──────────────────────────

    def _carregar_prescricoes(self):
        self._todas = self.svc_prescricao.buscar_todas()
        self._popular_lista(self._todas)

    def _popular_lista(self, prescricoes):
        self.lista.clear()
        for p in prescricoes:
            pac   = p.paciente.nome if p.paciente else "—"
            data  = p.criado_em.strftime("%d/%m/%Y") if p.criado_em else "s/d"
            adesoes = self.service.buscar_por_prescricao(p.id)
            media   = self.service.media_percentual(adesoes)
            meds    = ", ".join(
                f"{it.medicamento.nome} {it.dose or ''}".strip()
                for it in p.itens if it.medicamento
            ) or "sem medicamentos"
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, p)
            item.setText(f"{pac}\n#{p.id}  ·  {data}  ·  {media:.0f}% adesão\n💊 {meds}")
            item.setForeground(QColor("#1a252f"))
            self.lista.addItem(item)

    def _filtrar_lista(self):
        txt = self.input_busca.text().strip().lower()
        self._popular_lista([p for p in self._todas
                             if not txt or txt in (p.paciente.nome or "").lower()])

    # ── Detalhe ───────────────────────────────────────

    def _limpar_detalhe(self):
        def _clear_layout(lay):
            while lay.count():
                child = lay.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
                elif child.layout():
                    _clear_layout(child.layout())
        _clear_layout(self.detalhe_lay)

    def _mostrar_placeholder(self):
        lbl = QLabel("← Selecione uma prescrição para ver o histórico de adesão.")
        lbl.setStyleSheet("color:#888; font-size:13px;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.detalhe_lay.addWidget(lbl)

    def _ao_selecionar(self, row):
        if row < 0:
            return
        item = self.lista.item(row)
        if not item:
            return
        self.prescricao_sel = item.data(Qt.ItemDataRole.UserRole)
        # Ano exibido = ano da semana_inicio ou ano atual
        if self.prescricao_sel and self.prescricao_sel.semana_inicio:
            self._ano_exibido = self.prescricao_sel.semana_inicio.year
        else:
            self._ano_exibido = datetime.date.today().year
        self._renderizar_detalhe()

    def _renderizar_detalhe(self):
        self._limpar_detalhe()
        p = self.prescricao_sel
        if not p:
            self._mostrar_placeholder()
            return

        self.db.expire_all()
        adesoes = self.service.buscar_por_prescricao(p.id)
        media   = self.service.media_percentual(adesoes)

        # ── Cabeçalho ─────────────────────────────────
        cab = QFrame()
        cab.setStyleSheet("background:#eaf4fb; border-radius:10px;")
        cl  = QVBoxLayout(cab)
        cl.setContentsMargins(14, 10, 14, 10)
        cl.setSpacing(4)
        pac  = p.paciente.nome if p.paciente else "—"
        med  = p.medico.nome   if p.medico   else "—"
        data = p.criado_em.strftime("%d/%m/%Y") if p.criado_em else "s/d"
        lbl1 = QLabel(f"👴 {pac}")
        lbl1.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        lbl2 = QLabel(f"👨‍⚕️ {med}   ·   Prescrição #{p.id}   ·   Criada em {data}")
        lbl2.setStyleSheet("color:#555; font-size:12px;")
        cl.addWidget(lbl1)
        cl.addWidget(lbl2)
        if p.observacoes:
            lo = QLabel(f"📝 {p.observacoes}")
            lo.setWordWrap(True)
            lo.setStyleSheet("color:#666; font-size:11px; font-style:italic;")
            cl.addWidget(lo)
        self.detalhe_lay.addWidget(cab)

        # ── Cards de medicamentos ──────────────────────
        if p.itens:
            lbl_m = QLabel("Medicamentos prescritos")
            lbl_m.setFont(QFont("Arial", 11, QFont.Weight.Bold))
            self.detalhe_lay.addWidget(lbl_m)
            self.detalhe_lay.addWidget(self._widget_cards_medicamentos(p.itens))

        # ── Período do tratamento ──────────────────────
        self.detalhe_lay.addWidget(self._widget_periodo(p))

        # ── Matriz anual ──────────────────────────────
        nav = QHBoxLayout()
        nav.setSpacing(4)

        lbl_titulo_nav = QLabel("Histórico de adesão")
        lbl_titulo_nav.setStyleSheet("font-size:11px; color:#888;")

        btn_prev = QPushButton("‹ " + str(self._ano_exibido - 1))
        btn_prev.setFixedHeight(22)
        btn_prev.setFixedWidth(54)
        btn_prev.setStyleSheet(
            "QPushButton{background:transparent;border:0.5px solid #ccc;"
            "border-radius:4px;color:#999;font-size:11px;}"
            "QPushButton:hover{background:#f0f0f0;color:#555;}"
        )
        btn_prev.clicked.connect(lambda: self._mudar_ano(-1))

        self._lbl_ano = QLabel(str(self._ano_exibido))
        self._lbl_ano.setFixedWidth(38)
        self._lbl_ano.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_ano.setStyleSheet("font-size:12px; color:#555; font-weight:bold;")

        btn_next = QPushButton(str(self._ano_exibido + 1) + " ›")
        btn_next.setFixedHeight(22)
        btn_next.setFixedWidth(54)
        btn_next.setStyleSheet(
            "QPushButton{background:transparent;border:0.5px solid #ccc;"
            "border-radius:4px;color:#999;font-size:11px;}"
            "QPushButton:hover{background:#f0f0f0;color:#555;}"
        )
        btn_next.clicked.connect(lambda: self._mudar_ano(+1))

        nav.addWidget(lbl_titulo_nav)
        nav.addStretch()
        nav.addWidget(btn_prev)
        nav.addWidget(self._lbl_ano)
        nav.addWidget(btn_next)

        nav_widget = QWidget()
        nav_widget.setLayout(nav)
        self.detalhe_lay.addWidget(nav_widget)

        self._matriz_container = QWidget()
        self._matriz_lay = QVBoxLayout(self._matriz_container)
        self._matriz_lay.setContentsMargins(0, 0, 0, 0)
        self._matriz_lay.addWidget(self._widget_matriz_anual(p, adesoes))
        self.detalhe_lay.addWidget(self._matriz_container)

        # ── Legenda ───────────────────────────────────
        self.detalhe_lay.addWidget(self._widget_legenda())


        self.detalhe_lay.addStretch()

    def _mudar_ano(self, delta: int):
        self._ano_exibido += delta
        self._lbl_ano.setText(str(self._ano_exibido))
        # Resubstitui apenas a matriz
        p       = self.prescricao_sel
        adesoes = self.service.buscar_por_prescricao(p.id)
        while self._matriz_lay.count():
            child = self._matriz_lay.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self._matriz_lay.addWidget(self._widget_matriz_anual(p, adesoes))

    # ── Widgets de componentes ────────────────────────

    def _widget_periodo(self, p) -> QWidget:
        """Linha com QDateEdit para definir início e fim do tratamento."""
        frame = QFrame()
        frame.setStyleSheet(
            "background:#f4f6f7; border:0.5px solid #ddd; border-radius:6px;"
        )
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(10, 4, 10, 4)
        lay.setSpacing(8)

        lbl_titulo = QLabel("📅 Período do tratamento:")
        lbl_titulo.setStyleSheet("font-size:11px; color:#666;")
        lay.addWidget(lbl_titulo)

        lbl_ini = QLabel("Início:")
        lbl_ini.setStyleSheet("font-size:11px; color:#777;")
        self._date_inicio = QDateEdit()
        self._date_inicio.setCalendarPopup(True)
        self._date_inicio.setDisplayFormat("dd/MM/yyyy")
        self._date_inicio.setFixedHeight(22)
        self._date_inicio.setStyleSheet("font-size:11px;")
        if p.semana_inicio:
            self._date_inicio.setDate(QDate(p.semana_inicio.year,
                                            p.semana_inicio.month,
                                            p.semana_inicio.day))
        else:
            self._date_inicio.setDate(QDate.currentDate())
        self._date_inicio.dateChanged.connect(
            lambda d: self._corrigir_segunda(self._date_inicio, d))

        lbl_fim = QLabel("Fim:")
        lbl_fim.setStyleSheet("font-size:11px; color:#777;")
        self._date_fim = QDateEdit()
        self._date_fim.setCalendarPopup(True)
        self._date_fim.setDisplayFormat("dd/MM/yyyy")
        self._date_fim.setFixedHeight(22)
        self._date_fim.setStyleSheet("font-size:11px;")
        if p.semana_fim:
            self._date_fim.setDate(QDate(p.semana_fim.year,
                                         p.semana_fim.month,
                                         p.semana_fim.day))
        else:
            self._date_fim.setDate(QDate.currentDate().addMonths(1))
        self._date_fim.dateChanged.connect(
            lambda d: self._corrigir_segunda(self._date_fim, d))

        btn_salvar = QPushButton("💾 Salvar")
        btn_salvar.setFixedHeight(22)
        btn_salvar.setStyleSheet(
            "QPushButton{background:#2980b9;color:white;border-radius:4px;font-size:10px;padding:0 8px;}"
            "QPushButton:hover{background:#3498db;}"
        )
        btn_salvar.clicked.connect(self._salvar_periodo)

        lay.addWidget(lbl_ini)
        lay.addWidget(self._date_inicio)
        lay.addWidget(lbl_fim)
        lay.addWidget(self._date_fim)
        lay.addWidget(btn_salvar)
        lay.addStretch()
        return frame

    @staticmethod
    def _corrigir_segunda(widget: QDateEdit, qdate: QDate):
        d = qdate.toPyDate()
        seg = _segunda_feira(d)
        if seg != d:
            widget.blockSignals(True)
            widget.setDate(QDate(seg.year, seg.month, seg.day))
            widget.blockSignals(False)

    def _salvar_periodo(self):
        p = self.prescricao_sel
        if not p:
            return
        inicio = self._date_inicio.date().toPyDate()
        fim    = self._date_fim.date().toPyDate()
        if fim < inicio:
            QMessageBox.warning(self, "Atenção", "A data de fim deve ser após o início.")
            return
        try:
            self.svc_prescricao.atualizar(p.id, {
                "semana_inicio": inicio,
                "semana_fim"   : fim,
            })
            self.db.expire_all()
            self.prescricao_sel = self.svc_prescricao.buscar_por_id(p.id)
            # Atualiza ano exibido para o do início
            self._ano_exibido = inicio.year
            self._renderizar_detalhe()
        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))

    def _widget_matriz_anual(self, prescricao, adesoes) -> QWidget:
        """Matriz 12 colunas (meses) × N linhas (semanas por mês)."""
        adesao_map   = {a.semana: a for a in adesoes}
        semana_ini   = prescricao.semana_inicio
        semana_fim   = prescricao.semana_fim
        semana_hoje  = AdesaoService.semana_atual()

        mes_semanas = _semanas_do_ano(self._ano_exibido)
        max_linhas  = max((len(v) for v in mes_semanas.values()), default=0)

        frame = QFrame()
        grid  = QGridLayout(frame)
        grid.setSpacing(3)
        grid.setContentsMargins(0, 0, 0, 0)

        CW = 72   # largura da célula
        CH = 52   # altura da célula

        # Linha 0 — cabeçalhos dos meses
        for col, nome_mes in enumerate(MESES_PT):
            lbl = QLabel(nome_mes)
            lbl.setFixedSize(QSize(CW, 20))
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(
                "background:#2c3e50; color:white; font-size:11px;"
                "font-weight:bold; border-radius:4px;"
            )
            grid.addWidget(lbl, 0, col)

        # Linhas 1..max_linhas — células de semana
        for linha in range(max_linhas):
            for col in range(12):
                mes = col + 1
                semanas_do_mes = mes_semanas.get(mes, [])
                if linha < len(semanas_do_mes):
                    seg = semanas_do_mes[linha]
                    dom = seg + datetime.timedelta(days=6)
                    iso_sem = seg.isocalendar()[1]

                    # Determina estado
                    no_tratamento = (
                        semana_ini is not None and
                        semana_fim is not None and
                        semana_ini <= seg <= semana_fim
                    )
                    a = adesao_map.get(seg)

                    cel = CelulaMatriz(seg)
                    cel.duplo_clique.connect(self._registrar_adesao_semana)
                    cel.setFixedSize(QSize(CW, CH))
                    cel.setAlignment(Qt.AlignmentFlag.AlignCenter)

                    linha1 = f"Sem. {iso_sem:02d}"
                    linha2 = f"{seg.strftime('%d/%m')} {dom.strftime('%d/%m')}"
                    cel.setText(f"{linha1}\n{linha2}")

                    hoje = seg == semana_hoje
                    borda_hoje = "border: 2.5px solid #111;" if hoje else ""

                    if a:
                        nivel_v = a.nivel.value if hasattr(a.nivel, 'value') else a.nivel
                        cor_bg  = COR_NIVEL.get(nivel_v, "#ccc")
                        label_t, pct_t, _ = NIVEL_LABELS.get(nivel_v, ("", "", ""))
                        cel.setStyleSheet(
                            f"background:{cor_bg}; border-radius:6px;"
                            f"color:white; font-size:9px; font-weight:bold; {borda_hoje}"
                        )
                        cel.setToolTip(
                            f"Sem. {iso_sem}  ·  {seg.strftime('%d/%m/%Y')} – {dom.strftime('%d/%m/%Y')}\n"
                            f"Adesão: {label_t} ({pct_t})"
                            + (f"\nObs: {a.observacoes}" if a.observacoes else "")
                        )
                    elif no_tratamento and seg <= semana_hoje:
                        borda = borda_hoje or "border:1.5px dashed #7fb3d3;"
                        cel.setStyleSheet(
                            f"background:{COR_TRATAMENTO}; {borda}"
                            f"border-radius:6px; color:#3a7ca5; font-size:9px;"
                        )
                        cel.setToolTip(
                            f"Sem. {iso_sem}  ·  {seg.strftime('%d/%m/%Y')} – {dom.strftime('%d/%m/%Y')}\n"
                            f"Sem registro de adesão"
                        )
                    elif no_tratamento:
                        cel.setStyleSheet(
                            f"background:#e8f8f5; border-radius:6px;"
                            f"color:#3a8a78; font-size:9px; {borda_hoje}"
                            + ("" if hoje else "border:0.5px solid #a2d9ce;")
                        )
                        cel.setToolTip(
                            f"Sem. {iso_sem}  ·  {seg.strftime('%d/%m/%Y')} – {dom.strftime('%d/%m/%Y')}\n"
                            f"Semana futura do tratamento"
                        )
                    else:
                        cel.setStyleSheet(
                            f"background:{COR_FORA}; border-radius:6px;"
                            f"color:#999; font-size:9px; {borda_hoje}"
                        )
                        cel.setToolTip(
                            f"Sem. {iso_sem}  ·  {seg.strftime('%d/%m/%Y')} – {dom.strftime('%d/%m/%Y')}\n"
                            f"Fora do período de tratamento"
                        )
                    grid.addWidget(cel, linha + 1, col)
                else:
                    # Mês com menos semanas nesta linha
                    vazio = QLabel()
                    vazio.setFixedSize(QSize(CW, CH))
                    grid.addWidget(vazio, linha + 1, col)

        return frame

    def _widget_cards_medicamentos(self, itens) -> QWidget:
        frame = QFrame()
        grid  = QGridLayout(frame)
        grid.setSpacing(8)
        grid.setContentsMargins(0, 0, 0, 0)
        cores = ["#eaf4fb", "#eaf6ee", "#fef9e7", "#fdf2f8", "#f0f3ff"]
        for i, it in enumerate(itens):
            if not it.medicamento:
                continue
            card = QFrame()
            card.setStyleSheet(
                f"background:{cores[i % len(cores)]}; border:0.5px solid #ddd; border-radius:8px;"
            )
            row = QHBoxLayout(card)
            row.setContentsMargins(10, 6, 10, 6)
            row.setSpacing(16)

            # Nome + apresentação
            nome_col = QVBoxLayout()
            nome_col.setSpacing(1)
            ln = QLabel(f"💊 {it.medicamento.nome}")
            ln.setFont(QFont("Arial", 11, QFont.Weight.Bold))
            nome_col.addWidget(ln)
            if it.medicamento.apresentacao:
                la = QLabel(it.medicamento.apresentacao)
                la.setStyleSheet("color:#7f8c8d; font-size:10px;")
                nome_col.addWidget(la)
            row.addLayout(nome_col, 3)

            # Dose, Frequência, Duração — cada um com label + valor
            for lbl_t, val in [("Dose", it.dose), ("Frequência", it.frequencia), ("Duração", it.duracao)]:
                if val:
                    cw = QVBoxLayout()
                    cw.setSpacing(1)
                    cw.addWidget(self._mini_label(lbl_t, "#95a5a6", 10))
                    cw.addWidget(self._mini_label(val, "#2c3e50", 11, bold=True))
                    row.addLayout(cw, 1)

            if it.instrucoes:
                li = QLabel(f"ℹ️ {it.instrucoes}")
                li.setStyleSheet("font-size:10px; color:#666;")
                li.setWordWrap(True)
                row.addWidget(li, 2)

            grid.addWidget(card, i, 0)
        return frame

    @staticmethod
    def _mini_label(txt, cor, size, bold=False):
        l = QLabel(txt)
        l.setStyleSheet(
            f"font-size:{size}px; color:{cor};"
            + ("font-weight:bold;" if bold else "")
        )
        return l

    def _widget_barra_media(self, media: float) -> QWidget:
        frame = QFrame()
        lay   = QHBoxLayout(frame)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)
        lbl = QLabel("Média geral:")
        lbl.setStyleSheet("font-size:12px; color:#555;")
        lbl.setFixedWidth(90)
        outer = QFrame()
        outer.setFixedHeight(14)
        outer.setStyleSheet("background:#e0e0e0; border-radius:7px;")
        outer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        inner = QFrame(outer)
        inner.setFixedHeight(14)
        inner.setFixedWidth(max(int(media / 100 * 400), 6))
        inner.setStyleSheet(f"background:{self._cor_media(media)}; border-radius:7px;")
        pct = QLabel(f"{media:.0f}%")
        pct.setStyleSheet(f"font-size:14px; font-weight:bold; color:{self._cor_media(media)};")
        pct.setFixedWidth(42)
        lay.addWidget(lbl)
        lay.addWidget(outer)
        lay.addWidget(pct)
        return frame

    def _widget_legenda(self) -> QWidget:
        frame = QFrame()
        lay   = QHBoxLayout(frame)
        lay.setContentsMargins(0, 4, 0, 0)
        lay.setSpacing(12)
        itens = [
            (COR_FORA,         COR_FORA_TEXTO, "Fora do tratamento"),
            (COR_TRATAMENTO,   "#4a86a8",      "Sem registro"),
            ("#e8f8f5",        "#76b5a8",      "Semana futura"),
            ("#888780",        "white",        "Nenhuma (0%)"),
            ("#E24B4A",        "white",        "Baixa (25%)"),
            ("#EF9F27",        "white",        "Parcial (50%)"),
            ("#378ADD",        "white",        "Boa (75%)"),
            ("#639922",        "white",        "Total (100%)"),
        ]
        for bg, fg, label in itens:
            sq = QLabel()
            sq.setFixedSize(QSize(20, 20))
            sq.setStyleSheet(f"background:{bg}; border-radius:4px;")
            lb = QLabel(label)
            lb.setStyleSheet("font-size:10px; color:#555;")
            lay.addWidget(sq)
            lay.addWidget(lb)
        lay.addStretch()
        return frame

    def _widget_historico(self, adesoes) -> QWidget:
        frame = QFrame()
        frame.setStyleSheet("background:#f8f9fa; border:0.5px solid #ddd; border-radius:8px;")
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(4)
        for a in reversed(adesoes):
            nivel_v = a.nivel.value if hasattr(a.nivel, 'value') else a.nivel
            cor = COR_NIVEL.get(nivel_v, "#ccc")
            label_t, pct_t, _ = NIVEL_LABELS.get(nivel_v, ("", "", ""))
            dom = a.semana + datetime.timedelta(days=6)
            iso_sem = a.semana.isocalendar()[1]
            row = QHBoxLayout()
            row.setSpacing(10)
            ld = QLabel(
                f"Sem. {iso_sem:02d}  ·  "
                f"{a.semana.strftime('%d/%m/%y')} – {dom.strftime('%d/%m/%y')}"
            )
            ld.setStyleSheet("font-size:12px; color:#444; min-width:210px;")
            badge = QLabel(f"{label_t}  {pct_t}")
            badge.setFixedHeight(22)
            badge.setStyleSheet(
                f"background:{cor}; color:white; border-radius:5px;"
                f"padding:0 10px; font-size:11px; font-weight:bold;"
            )
            lo = QLabel(a.observacoes or "")
            lo.setStyleSheet("font-size:11px; color:#777;")
            lo.setWordWrap(True)
            btn_del = QPushButton("✖")
            btn_del.setFixedSize(22, 22)
            btn_del.setStyleSheet(
                "QPushButton{border:none;color:#bbb;font-size:14px;}"
                "QPushButton:hover{color:#e74c3c;}"
            )
            btn_del.clicked.connect(lambda _, aid=a.id: self._remover_adesao(aid))
            row.addWidget(ld)
            row.addWidget(badge)
            row.addWidget(lo, 1)
            row.addWidget(btn_del)
            lay.addLayout(row)
        return frame

    # ── Ações ─────────────────────────────────────────

    def _registrar_adesao_semana(self, semana: datetime.date):
        if not self.prescricao_sel:
            return
        from app.ui.components.dialogs.dialog_adesao import DialogAdesao
        dlg = DialogAdesao(self.db, self.prescricao_sel, semana=semana, parent=self)
        if dlg.exec():
            self.db.expire_all()
            self.prescricao_sel = self.svc_prescricao.buscar_por_id(self.prescricao_sel.id)
            self._renderizar_detalhe()
            self._carregar_prescricoes()

    def _remover_adesao(self, adesao_id: int):
        resp = QMessageBox.question(
            self, "Remover registro",
            "Deseja remover este registro de adesão?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if resp == QMessageBox.StandardButton.Yes:
            self.service.deletar(adesao_id)
            self.db.expire_all()
            self.prescricao_sel = self.svc_prescricao.buscar_por_id(self.prescricao_sel.id)
            self._renderizar_detalhe()
            self._carregar_prescricoes()

    def selecionar_prescricao(self, prescricao_id: int):
        """Navega para a prescrição com o id dado na lista."""
        self.db.rollback()
        self.db.expire_all()
        self._carregar_prescricoes()
        for i in range(self.lista.count()):
            item = self.lista.item(i)
            p = item.data(Qt.ItemDataRole.UserRole)
            if p and p.id == prescricao_id:
                self.lista.setCurrentRow(i)
                break

    def _atualizar(self):
        self.db.rollback()
        self.db.expire_all()
        self._carregar_prescricoes()
        if self.prescricao_sel:
            self.prescricao_sel = self.svc_prescricao.buscar_por_id(self.prescricao_sel.id)
            self._renderizar_detalhe()

    @staticmethod
    def _cor_media(media: float) -> str:
        if media == 0:   return "#888780"
        if media <= 25:  return "#E24B4A"
        if media <= 50:  return "#EF9F27"
        if media <= 75:  return "#378ADD"
        return "#639922"
