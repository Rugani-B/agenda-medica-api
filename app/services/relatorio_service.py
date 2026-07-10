import datetime
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from app.database.connection import SessionLocal
from app.models.pacientes import Paciente
from app.models.consulta import Consulta
from app.models.prescricao import Prescricao
from app.models.exame import Exame
from app.models.confirmacao import Confirmacao, StatusConfirmacao
from app.models.pedido_exame import PedidoExame
from app.models.adesao_tratamento import NIVEL_PCT


def gerar_relatorio_paciente(
    paciente_id: int,
    data_inicio: datetime.date,
    data_fim: datetime.date,
    secoes: dict,
    caminho_saida: str,
) -> str:
    """
    Gera PDF do paciente no período informado.
    secoes: dict com chaves 'consultas', 'exames', 'prescricoes', 'adesao'
    Retorna caminho_saida.
    """
    db = SessionLocal()
    try:
        paciente = db.query(Paciente).filter(Paciente.id == paciente_id).first()
        if not paciente:
            raise ValueError("Paciente não encontrado")

        doc = SimpleDocTemplate(
            caminho_saida,
            pagesize=A4,
            leftMargin=2 * cm,
            rightMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )

        styles = getSampleStyleSheet()
        s_titulo = ParagraphStyle("titulo", parent=styles["Title"], fontSize=14,
                                   alignment=TA_CENTER, spaceAfter=10)
        s_subtit = ParagraphStyle("subtit", parent=styles["Normal"], fontSize=8,
                                   textColor=colors.HexColor("#666666"),
                                   alignment=TA_CENTER, spaceBefore=6, spaceAfter=14)
        s_secao  = ParagraphStyle("secao", parent=styles["Heading2"], fontSize=12, textColor=colors.HexColor("#1a5276"), spaceBefore=14, spaceAfter=6)
        s_body   = ParagraphStyle("body", parent=styles["Normal"], fontSize=9, leading=13)
        s_vazio  = ParagraphStyle("vazio", parent=styles["Normal"], fontSize=9, textColor=colors.grey, leftIndent=8)

        story = []

        # ── Cabeçalho ──
        story.append(Paragraph(f"Relatório — {paciente.nome}", s_titulo))
        periodo = f"{data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}"
        story.append(Paragraph(f"Período: {periodo}", s_subtit))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#aaaaaa")))
        story.append(Spacer(1, 10))

        # ── Consultas ──
        if secoes.get("consultas"):
            story.append(Paragraph("Consultas", s_secao))
            consultas = (
                db.query(Consulta)
                .filter(
                    Consulta.paciente_id == paciente_id,
                    Consulta.data_hora >= datetime.datetime.combine(data_inicio, datetime.time.min),
                    Consulta.data_hora <= datetime.datetime.combine(data_fim, datetime.time.max),
                )
                .order_by(Consulta.data_hora)
                .all()
            )
            if consultas:
                conf_ids = {
                    c.consulta_id
                    for c in db.query(Confirmacao)
                    .filter(Confirmacao.status == StatusConfirmacao.realizada)
                    .all()
                }

                # Estilos para texto dentro das células
                s_cel = ParagraphStyle("cel", parent=s_body, fontSize=8, leading=11)
                s_cel_neg = ParagraphStyle("cel_neg", parent=s_body, fontSize=8,
                                           leading=11, fontName="Helvetica-Bold",
                                           textColor=colors.white)
                s_label = ParagraphStyle("label", parent=s_body, fontSize=7.5,
                                         fontName="Helvetica-Oblique",
                                         textColor=colors.HexColor("#555555"), leading=11)
                s_item = ParagraphStyle("item", parent=s_body, fontSize=7.5,
                                        textColor=colors.HexColor("#222222"), leading=11,
                                        leftIndent=18, firstLineIndent=-8)  # bullet hang + indent

                # Larguras: Data | Médica(o) | Especialidade | Status  (total 16.7 cm)
                COL_W = [2.2 * cm, 7.3 * cm, 4.5 * cm, 2.7 * cm]
                N_COLS = len(COL_W)

                # Cabeçalho único
                rows = [[
                    Paragraph("<b>Data</b>", s_cel_neg),
                    Paragraph("<b>Médica(o)</b>", s_cel_neg),
                    Paragraph("<b>Especialidade</b>", s_cel_neg),
                    Paragraph("<b>Status</b>", s_cel_neg),
                ]]
                extra_style = [
                    # Fundo branco em todas as linhas de dados (cancela ROWBACKGROUNDS)
                    ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                ]

                def _add_subrow(label_txt, item_txt):
                    """Adiciona linha com col-0 vazia, cols 1-3 em span."""
                    r = len(rows)
                    rows.append([
                        "",
                        Paragraph(item_txt, s_item if label_txt is None else s_label),
                        "", "",
                    ])
                    extra_style.extend([
                        ("SPAN", (1, r), (N_COLS - 1, r)),
                        ("BACKGROUND", (0, r), (-1, r), colors.white),
                        ("TOPPADDING", (0, r), (-1, r), 1),
                        ("BOTTOMPADDING", (0, r), (-1, r), 1),
                        ("LEFTPADDING", (1, r), (-1, r), 4),
                        ("LINEAFTER", (0, r), (0, r), 0, colors.white),
                    ])

                for idx, c in enumerate(consultas):
                    # Separador entre consultas: linha acima da linha de dados
                    # cap=0 (butt) evita semicírculos
                    r_dados = len(rows)
                    if idx > 0:
                        extra_style += [
                            ("LINEABOVE", (0, r_dados), (-1, r_dados),
                             2.5, colors.HexColor("#2e86c1"), 0),
                        ]

                    medico_nome = c.medico.nome if c.medico else "—"
                    # Primeiro nome em negrito, restante normal
                    partes = medico_nome.split(" ", 1)
                    medico_fmt = f"<b>{partes[0]}</b> {partes[1]}" if len(partes) > 1 else f"<b>{partes[0]}</b>"
                    especialidade = (
                        c.medico.especialidade.nome
                        if c.medico and c.medico.especialidade else "—"
                    )
                    status_val = c.status.value.capitalize() if c.status else "—"

                    rows.append([
                        Paragraph(c.data_hora.strftime("%d/%m/%Y"), s_cel),
                        Paragraph(medico_fmt, s_cel),
                        Paragraph(especialidade, s_cel),
                        Paragraph(status_val, s_cel),
                    ])
                    extra_style += [
                        ("TOPPADDING", (0, r_dados), (-1, r_dados), 8),
                        ("BOTTOMPADDING", (0, r_dados), (-1, r_dados), 8),
                    ]

                    # Prescrições — label depois itens com bullet
                    itens_med = [
                        it for p in c.prescricoes for it in p.itens
                    ]
                    if itens_med:
                        _add_subrow("label", "Prescrições:")
                        for it in itens_med:
                            nome_med = it.medicamento.nome if it.medicamento else "?"
                            dose_freq = f"{it.dose or ''} {it.frequencia or ''}".strip()
                            texto = nome_med + (f" — {dose_freq}" if dose_freq else "")
                            _add_subrow(None, f"• {texto}")

                    # Exames solicitados — label depois itens com bullet
                    if c.pedidos_exame:
                        _add_subrow("label", "Exames solicitados:")
                        for pe in c.pedidos_exame:
                            tipo = pe.tipo_exame.nome if pe.tipo_exame else "?"
                            urg = " <i>(urgente)</i>" if pe.urgente else ""
                            _add_subrow(None, f"• {tipo}{urg}")

                t = Table(rows, colWidths=COL_W)
                t.setStyle(TableStyle(_estilo_tabela_cmds() + extra_style))
                story.append(t)
            else:
                story.append(Paragraph("Nenhuma consulta no período.", s_vazio))
            story.append(Spacer(1, 4))

        # ── Exames ──
        if secoes.get("exames"):
            story.append(Paragraph("Exames", s_secao))
            exames = (
                db.query(Exame)
                .filter(
                    Exame.paciente_id == paciente_id,
                    Exame.data_hora >= datetime.datetime.combine(data_inicio, datetime.time.min),
                    Exame.data_hora <= datetime.datetime.combine(data_fim, datetime.time.max),
                )
                .order_by(Exame.data_hora)
                .all()
            )
            if exames:
                s_res = ParagraphStyle("res", parent=s_body, fontSize=8, leading=11)
                s_res_hdr = ParagraphStyle("res_hdr", parent=s_body, fontSize=9,
                                           fontName="Helvetica-Bold", textColor=colors.white)
                data_rows = [[
                    Paragraph("<b>Data</b>", s_res_hdr),
                    Paragraph("<b>Tipo</b>", s_res_hdr),
                    Paragraph("<b>Resultado</b>", s_res_hdr),
                ]]
                import re as _re
                def _strip_html(txt):
                    return _re.sub(r"<[^>]+>", " ", txt or "").strip() or "—"

                for e in exames:
                    data_rows.append([
                        Paragraph(e.data_hora.strftime("%d/%m/%Y") if e.data_hora else "—", s_res),
                        Paragraph(e.tipo_exame.nome if e.tipo_exame else "—", s_res),
                        Paragraph(_strip_html(e.resultado), s_res),
                    ])
                t = Table(data_rows, colWidths=[3.0 * cm, 5.0 * cm, 8.7 * cm])
                t.setStyle(_estilo_tabela())
                story.append(t)
            else:
                story.append(Paragraph("Nenhum exame no período.", s_vazio))
            story.append(Spacer(1, 6))

        # ── Prescrições ──
        if secoes.get("prescricoes"):
            story.append(Paragraph("Prescrições / Tratamentos", s_secao))
            prescricoes = (
                db.query(Prescricao)
                .filter(Prescricao.paciente_id == paciente_id)
                .order_by(Prescricao.semana_inicio.desc())
                .all()
            )
            ativas = [p for p in prescricoes if not p.semana_fim or p.semana_fim >= data_inicio]
            if ativas:
                data_rows = [["Medicamento(s)", "Dose / Frequência", "Início", "Fim"]]
                for p in ativas:
                    nomes = ", ".join(
                        f"{it.medicamento.nome}" if it.medicamento else "—"
                        for it in p.itens
                    ) or "—"
                    dose_freq = ", ".join(
                        f"{it.dose or ''} {it.frequencia or ''}".strip()
                        for it in p.itens
                        if it.dose or it.frequencia
                    ) or "—"
                    data_rows.append([
                        nomes,
                        dose_freq,
                        p.semana_inicio.strftime("%d/%m/%Y") if p.semana_inicio else "—",
                        p.semana_fim.strftime("%d/%m/%Y") if p.semana_fim else "Em curso",
                    ])
                t = Table(data_rows, colWidths=[6.7 * cm, 5.0 * cm, 2.5 * cm, 2.5 * cm])
                t.setStyle(_estilo_tabela())
                story.append(t)
            else:
                story.append(Paragraph("Nenhuma prescrição ativa no período.", s_vazio))
            story.append(Spacer(1, 6))

        # ── Adesão ──
        if secoes.get("adesao"):
            story.append(Paragraph("Adesão ao Tratamento", s_secao))
            prescricoes_todas = (
                db.query(Prescricao)
                .filter(Prescricao.paciente_id == paciente_id)
                .all()
            )
            teve_adesao = False
            for p in prescricoes_todas:
                adesoes = [
                    a for a in p.adesoes
                    if data_inicio <= a.semana <= data_fim
                ]
                if not adesoes:
                    continue
                teve_adesao = True
                label = ", ".join(
                    it.medicamento.nome for it in p.itens if it.medicamento
                ) or f"Prescrição #{p.id}"
                story.append(Paragraph(f"<b>{label}</b>", s_body))
                data_rows = [["Semana", "Nível", "% Adesão"]]
                for a in sorted(adesoes, key=lambda x: x.semana):
                    pct = NIVEL_PCT.get(a.nivel.value, 0)
                    data_rows.append([
                        a.semana.strftime("%d/%m/%Y"),
                        a.nivel.value.replace("_", " ").title(),
                        f"{pct}%",
                    ])
                t = Table(data_rows, colWidths=[3 * cm, 3.5 * cm, 2.5 * cm])
                t.setStyle(_estilo_tabela())
                story.append(t)
                story.append(Spacer(1, 4))
            if not teve_adesao:
                story.append(Paragraph("Nenhum registro de adesão no período.", s_vazio))

        # ── Rodapé ──
        story.append(Spacer(1, 16))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc")))
        gerado = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        story.append(Paragraph(f"<font size='8' color='#888888'>Gerado em {gerado}</font>", s_body))

        doc.build(story)
    finally:
        db.close()

    return caminho_saida


def _estilo_tabela_cmds():
    return [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a5276")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4f8")]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]


def _estilo_tabela():
    return TableStyle(_estilo_tabela_cmds())
