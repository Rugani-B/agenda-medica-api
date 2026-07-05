from fastapi import APIRouter, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from datetime import date, timedelta
from collections import defaultdict
import calendar
import json
import os

from jinja2 import Environment, FileSystemLoader

from api.database import get_db
from api.auth import verificar_token
import app.models
from app.models.responsavel import Responsavel
from app.models.pedido_exame import PedidoExame
from app.models.anexo_exame import AnexoExame
from app.models.pacientes import Paciente
from app.models.consulta import Consulta
from app.models.exame import Exame
from app.models.prescricao import Prescricao
from app.models.adesao_tratamento import AdesaoTratamento, NivelAdesao
from app.models.base_enums import StatusAgendamento

router = APIRouter(prefix="/familia", tags=["familia"])

_templates_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
_jinja_env = Environment(loader=FileSystemLoader(_templates_dir), autoescape=True)

MESES_PT = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho",
            "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]


def _render(name: str, context: dict):
    t = _jinja_env.get_template(name)
    return HTMLResponse(t.render(**context), media_type="text/html; charset=utf-8")


def _get_responsavel(token: str, db: Session) -> Responsavel:
    for r in db.query(Responsavel).all():
        if verificar_token(token, r.id):
            return r
    raise HTTPException(status_code=403, detail="Token inválido")


def _segunda(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _semanas_do_mes(ano: int, mes: int):
    """Segundas-feiras que começam dentro do mês."""
    primeiro = date(ano, mes, 1)
    ultimo = date(ano, mes, calendar.monthrange(ano, mes)[1])
    seg = _segunda(primeiro)
    if seg < primeiro:   # segunda cai no mês anterior — pula para a próxima
        seg += timedelta(weeks=1)
    resultado = []
    while seg <= ultimo:
        resultado.append(seg)
        seg += timedelta(weeks=1)
    return resultado


def _build_mes_eventos(paciente_id: int, ano: int, mes: int, db: Session) -> dict:
    primeiro = date(ano, mes, 1)
    ultimo = date(ano, mes, calendar.monthrange(ano, mes)[1])

    consultas = db.query(Consulta).filter(
        Consulta.paciente_id == paciente_id,
        Consulta.data_hora >= primeiro,
        Consulta.data_hora <= ultimo,
    ).all()

    exames = db.query(Exame).filter(
        Exame.paciente_id == paciente_id,
        Exame.data_hora >= primeiro,
        Exame.data_hora <= ultimo,
    ).all()

    prescricoes = db.query(Prescricao).filter(
        Prescricao.paciente_id == paciente_id,
        Prescricao.semana_inicio <= ultimo,
        Prescricao.semana_fim >= primeiro,
    ).all()

    adesoes = {a.semana: a for p in prescricoes for a in p.adesoes if primeiro <= a.semana <= ultimo}

    eventos = defaultdict(lambda: {"consultas": [], "exames": [], "tratamentos": []})

    for c in consultas:
        dia = c.data_hora.date().isoformat()
        esp = c.medico.especialidade.nome if c.medico and c.medico.especialidade else (c.medico.nome if c.medico else "Médico n/i")
        eventos[dia]["consultas"].append({
            "id": c.id, "medico": c.medico.nome if c.medico else "n/i",
            "especialidade": esp, "status": c.status.value,
            "hora": c.data_hora.strftime("%H:%M"), "observacoes": c.observacoes or "",
        })

    for e in exames:
        dia = e.data_hora.date().isoformat()
        eventos[dia]["exames"].append({
            "id": e.id, "tipo": e.tipo_exame.nome if e.tipo_exame else "Exame",
            "local": e.local.nome if e.local else "",
            "status": e.status.value, "hora": e.data_hora.strftime("%H:%M"),
            "resultado": e.resultado or "",
        })

    for p in prescricoes:
        seg = _segunda(primeiro)
        while seg <= ultimo:
            if p.semana_inicio <= seg <= p.semana_fim:
                dom = seg + timedelta(days=6)
                adesao = adesoes.get(seg)
                meds = [f"{i.medicamento.nome} {i.dose or ''}".strip() for i in p.itens]
                dia = max(seg, primeiro).isoformat()
                eventos[dia]["tratamentos"].append({
                    "prescricao_id": p.id,
                    "medicamentos": meds,
                    "semana_seg": seg.isoformat(),
                    "semana_dom": dom.isoformat(),
                    "adesao": adesao.nivel.value if adesao else None,
                })
            seg += timedelta(weeks=1)

    return dict(eventos)


def _build_ano_calendarios(paciente_id: int, ano: int, db: Session) -> dict:
    """Dados anuais para os 3 calendários de semanas."""
    inicio = date(ano, 1, 1)
    fim = date(ano, 12, 31)

    consultas = db.query(Consulta).filter(
        Consulta.paciente_id == paciente_id,
        Consulta.data_hora >= inicio,
        Consulta.data_hora <= fim,
    ).all()

    exames = db.query(Exame).filter(
        Exame.paciente_id == paciente_id,
        Exame.data_hora >= inicio,
        Exame.data_hora <= fim,
    ).all()

    prescricoes = db.query(Prescricao).filter(
        Prescricao.paciente_id == paciente_id,
        Prescricao.semana_inicio <= fim,
        Prescricao.semana_fim >= inicio,
    ).all()

    # Agrupa por semana (segunda-feira)
    cons_sem = defaultdict(list)
    for c in consultas:
        seg = _segunda(c.data_hora.date())
        esp = c.medico.especialidade.nome if c.medico and c.medico.especialidade else (c.medico.nome if c.medico else "")
        cons_sem[seg].append(esp or c.medico.nome if c.medico else "Consulta")

    exam_sem = defaultdict(list)
    for e in exames:
        seg = _segunda(e.data_hora.date())
        exam_sem[seg].append(e.tipo_exame.nome if e.tipo_exame else "Exame")

    # adesões do ano indexadas por (prescricao_id, semana)
    adesoes_ano = {}
    for p in prescricoes:
        for a in p.adesoes:
            if inicio <= a.semana <= fim:
                adesoes_ano[(p.id, a.semana)] = a.nivel.value

    NIVEL_COR = {
        "nenhuma": "#888780", "baixa": "#E24B4A",
        "parcial": "#EF9F27", "boa":   "#378ADD", "total": "#639922",
    }
    NIVEL_PCT = {"nenhuma": 0, "baixa": 25, "parcial": 50, "boa": 75, "total": 100}

    trat_sem = defaultdict(lambda: {"prescricoes": [], "n_meds": 0})
    for p in prescricoes:
        meds = [i.medicamento.nome for i in p.itens]
        seg = _segunda(inicio)
        while seg <= fim:
            if p.semana_inicio <= seg <= p.semana_fim:
                nivel = adesoes_ano.get((p.id, seg))
                trat_sem[seg]["prescricoes"].append({
                    "id": p.id,
                    "medicamentos": meds,
                    "nivel": nivel,
                    "cor": NIVEL_COR.get(nivel, "#ccc") if nivel else None,
                    "pct": NIVEL_PCT.get(nivel, 0) if nivel else 0,
                })
                trat_sem[seg]["n_meds"] += len(meds)
            seg += timedelta(weeks=1)

    # Monta estrutura: meses como colunas, semanas do mês como linhas
    def montar_meses(dados_por_semana, tipo="lista"):
        meses = []
        max_sem = 0
        for mes in range(1, 13):
            semanas = _semanas_do_mes(ano, mes)
            max_sem = max(max_sem, len(semanas))
            cells = []
            for s in semanas:
                dado = dados_por_semana.get(s)
                if tipo == "trat":
                    conteudo = dado if dado else {"prescricoes": [], "n_meds": 0}
                else:
                    conteudo = dado if dado else []
                cells.append({
                    "seg": s.isoformat(),
                    "label_num": s.isocalendar().week,
                    "label_data": s.strftime("%d/%m"),
                    "conteudo": conteudo,
                })
            meses.append({"nome": MESES_PT[mes - 1][:3], "semanas": cells})
        return {"meses": meses, "max_semanas": max_sem}

    MESES_ABR = ["jan","fev","mar","abr","mai","jun","jul","ago","set","out","nov","dez"]
    def fmt_data(dt): return f"{dt.day:02d}/{MESES_ABR[dt.month-1]}"

    lista_consultas = sorted([
        {
            "id": c.id,
            "seg": _segunda(c.data_hora.date()).isoformat(),
            "data": fmt_data(c.data_hora),
            "data_ord": c.data_hora.date().isoformat(),
            "especialidade": c.medico.especialidade.nome if c.medico and c.medico.especialidade else "",
            "medico": c.medico.nome if c.medico else "",
            "status": c.status.value,
        }
        for c in consultas
    ], key=lambda x: x["data_ord"], reverse=True)

    lista_exames = sorted([
        {
            "seg": _segunda(e.data_hora.date()).isoformat(),
            "data": fmt_data(e.data_hora),
            "data_ord": e.data_hora.date().isoformat(),
            "tipo": e.tipo_exame.nome if e.tipo_exame else "Exame",
            "local": e.local.nome if e.local else "",
            "status": e.status.value,
        }
        for e in exames
    ], key=lambda x: x["data_ord"], reverse=True)

    hoje = date.today()
    seg_atual = _segunda(hoje)

    lista_tratamentos = []
    for p in sorted(prescricoes, key=lambda x: x.semana_inicio or date.min, reverse=True):
        if p.semana_inicio and p.semana_fim:
            if p.semana_inicio <= seg_atual <= p.semana_fim:
                status_trat = "ativa"
            elif seg_atual < p.semana_inicio:
                status_trat = "futura"
            else:
                status_trat = "encerrada"
        else:
            status_trat = "encerrada"
        ativa = status_trat == "ativa"
        adesao_atual = adesoes_ano.get((p.id, seg_atual))
        meds = [
            f"{i.medicamento.nome} {i.dose or ''}".strip()
            + (f" — {i.frequencia}" if i.frequencia else "")
            for i in p.itens
        ]
        lista_tratamentos.append({
            "id": p.id,
            "medico": p.medico.nome if p.medico else "",
            "periodo": f"{p.semana_inicio.strftime('%d/%m/%Y')} → {p.semana_fim.strftime('%d/%m/%Y')}" if p.semana_inicio and p.semana_fim else "",
            "ativa": ativa,
            "status_trat": status_trat,
            "medicamentos": meds,
            "adesao_atual": adesao_atual,
            "adesao_cor": NIVEL_COR.get(adesao_atual, "#ccc") if adesao_atual else None,
            "adesao_pct": NIVEL_PCT.get(adesao_atual, 0) if adesao_atual else 0,
            "seg_atual": seg_atual.isoformat(),
        })

    return {
        "consultas":         montar_meses(cons_sem),
        "exames":            montar_meses(exam_sem),
        "tratamentos":       montar_meses(trat_sem, tipo="trat"),
        "lista_consultas":   lista_consultas,
        "lista_exames":      lista_exames,
        "lista_tratamentos": lista_tratamentos,
    }


def _resumo_semana(paciente_id: int, db: Session) -> dict:
    hoje = date.today()
    seg = _segunda(hoje)
    dom = seg + timedelta(days=6)

    consultas = db.query(Consulta).filter(
        Consulta.paciente_id == paciente_id,
        Consulta.data_hora >= seg, Consulta.data_hora <= dom,
    ).order_by(Consulta.data_hora).all()

    exames = db.query(Exame).filter(
        Exame.paciente_id == paciente_id,
        Exame.data_hora >= seg, Exame.data_hora <= dom,
    ).order_by(Exame.data_hora).all()

    prescricoes = db.query(Prescricao).filter(
        Prescricao.paciente_id == paciente_id,
        Prescricao.semana_inicio <= seg, Prescricao.semana_fim >= seg,
    ).all()

    return {
        "consultas": len(consultas),
        "exames": len(exames),
        "tratamentos_ativos": len(prescricoes),
        "semana_seg": seg.strftime("%d/%m"),
        "semana_dom": dom.strftime("%d/%m"),
        "lista_consultas": [
            {
                "data": c.data_hora.strftime("%a %d/%m %H:%M"),
                "medico": c.medico.nome if c.medico else "n/i",
                "especialidade": c.medico.especialidade.nome if c.medico and c.medico.especialidade else "",
                "status": c.status.value,
            }
            for c in consultas
        ],
        "lista_exames": [
            {
                "data": e.data_hora.strftime("%a %d/%m %H:%M"),
                "tipo": e.tipo_exame.nome if e.tipo_exame else "Exame",
                "local": e.local.nome if e.local else "",
                "status": e.status.value,
            }
            for e in exames
        ],
        "lista_tratamentos": [
            {
                "medicamentos": [f"{i.medicamento.nome} {i.dose or ''}".strip() for i in p.itens],
            }
            for p in prescricoes
        ],
    }


@router.get("/", response_class=HTMLResponse)
def agenda(token: str, ano: int = None, mes: int = None, db: Session = Depends(get_db)):
    responsavel = _get_responsavel(token, db)
    paciente = db.query(Paciente).filter_by(id=responsavel.paciente_id).first()

    hoje = date.today()
    ano = ano or hoje.year
    mes = mes or hoje.month

    cal_mensal = calendar.monthcalendar(ano, mes)
    mes_ant = mes - 1 if mes > 1 else 12
    ano_ant = ano if mes > 1 else ano - 1
    mes_prox = mes + 1 if mes < 12 else 1
    ano_prox = ano if mes < 12 else ano + 1

    import time
    return _render("agenda.html", {
        "cache_bust": int(time.time()),
        "token": token,
        "paciente": paciente,
        "responsavel": responsavel,
        "resumo": _resumo_semana(paciente.id, db),
        "eventos_json": json.dumps(_build_mes_eventos(paciente.id, ano, mes, db), ensure_ascii=False),
        "anual_json": json.dumps(_build_ano_calendarios(paciente.id, ano, db), ensure_ascii=False),
        "cal": cal_mensal,
        "ano": ano, "mes": mes,
        "mes_nome": MESES_PT[mes - 1],
        "hoje": hoje.isoformat(),
        "mes_ant": mes_ant, "ano_ant": ano_ant,
        "mes_prox": mes_prox, "ano_prox": ano_prox,
    })


@router.get("/semana/{seg_str}", response_class=HTMLResponse)
def detalhe_semana(seg_str: str, token: str, db: Session = Depends(get_db)):
    from datetime import datetime as dt
    responsavel = _get_responsavel(token, db)
    seg = dt.strptime(seg_str, "%Y-%m-%d").date()
    dom = seg + timedelta(days=6)

    consultas = db.query(Consulta).filter(
        Consulta.paciente_id == responsavel.paciente_id,
        Consulta.data_hora >= seg,
        Consulta.data_hora <= dom,
    ).order_by(Consulta.data_hora).all()

    prescricoes_ativas = db.query(Prescricao).filter(
        Prescricao.paciente_id == responsavel.paciente_id,
        Prescricao.semana_inicio <= seg,
        Prescricao.semana_fim >= seg,
    ).all()

    dados = []
    for c in consultas:
        pedidos = [
            {
                "tipo": p.tipo_exame.nome if p.tipo_exame else "Exame",
                "status": p.status.value,
                "urgente": p.urgente,
                "observacoes": p.observacoes or "",
            }
            for p in c.pedidos_exame
        ]
        prescs = [
            {
                "medico": c.medico.nome if c.medico else "",
                "itens": [
                    f"{i.medicamento.nome} {i.dose or ''}".strip()
                    + (f" — {i.frequencia}" if i.frequencia else "")
                    for i in p.itens
                ],
                "observacoes": p.observacoes or "",
            }
            for p in c.prescricoes
        ]
        dados.append({
            "id": c.id,
            "data": c.data_hora.strftime("%a %d/%m"),
            "hora": c.data_hora.strftime("%H:%M"),
            "medico": c.medico.nome if c.medico else "Médico n/i",
            "especialidade": c.medico.especialidade.nome if c.medico and c.medico.especialidade else "",
            "status": c.status.value,
            "observacoes": c.observacoes or "",
            "pedidos": pedidos,
            "prescricoes": prescs,
        })

    presc_ativas = [
        {
            "medico": p.medico.nome if p.medico else "",
            "periodo": f"{p.semana_inicio.strftime('%d/%m')} → {p.semana_fim.strftime('%d/%m')}",
            "itens": [
                f"{i.medicamento.nome} {i.dose or ''}".strip()
                + (f" — {i.frequencia}" if i.frequencia else "")
                for i in p.itens
            ],
        }
        for p in prescricoes_ativas
    ]

    return _render("modal_semana.html", {
        "seg": seg.strftime("%d/%m"),
        "dom": dom.strftime("%d/%m"),
        "consultas": dados,
        "prescricoes_ativas": presc_ativas,
        "token": token,
    })


@router.get("/consulta/{consulta_id}/detalhe", response_class=HTMLResponse)
def detalhe_consulta(consulta_id: int, token: str, db: Session = Depends(get_db)):
    responsavel = _get_responsavel(token, db)
    c = db.query(Consulta).filter_by(id=consulta_id).first()
    if not c or c.paciente_id != responsavel.paciente_id:
        raise HTTPException(status_code=404)

    pedidos = [
        {
            "tipo": p.tipo_exame.nome if p.tipo_exame else "Exame",
            "status": p.status.value,
            "urgente": p.urgente,
            "observacoes": p.observacoes or "",
        }
        for p in c.pedidos_exame
    ]
    prescs = [
        {
            "itens": [
                f"{i.medicamento.nome} {i.dose or ''}".strip()
                + (f" — {i.frequencia}" if i.frequencia else "")
                for i in p.itens
            ],
            "observacoes": p.observacoes or "",
        }
        for p in c.prescricoes
    ]
    dado = {
        "id": c.id,
        "data": c.data_hora.strftime("%a %d/%m"),
        "hora": c.data_hora.strftime("%H:%M"),
        "medico": c.medico.nome if c.medico else "Médico n/i",
        "especialidade": c.medico.especialidade.nome if c.medico and c.medico.especialidade else "",
        "status": c.status.value,
        "observacoes": c.observacoes or "",
        "pedidos": pedidos,
        "prescricoes": prescs,
    }
    return _render("modal_consulta.html", {"consulta": dado, "token": token})


@router.get("/semana-exames/{seg_str}", response_class=HTMLResponse)
def detalhe_semana_exames(seg_str: str, token: str, db: Session = Depends(get_db)):
    from datetime import datetime as dt
    responsavel = _get_responsavel(token, db)
    seg = dt.strptime(seg_str, "%Y-%m-%d").date()
    dom = seg + timedelta(days=6)

    exames = db.query(Exame).filter(
        Exame.paciente_id == responsavel.paciente_id,
        Exame.data_hora >= seg,
        Exame.data_hora <= dom,
    ).order_by(Exame.data_hora).all()

    dados = []
    for e in exames:
        anexos = [
            {
                "id": a.id,
                "nome": a.nome,
                "tipo": a.tipo,
                "ext": a.caminho.rsplit(".", 1)[-1].lower() if "." in a.caminho else "bin",
            }
            for a in e.anexos
        ]
        dados.append({
            "id": e.id,
            "data": e.data_hora.strftime("%a %d/%m"),
            "hora": e.data_hora.strftime("%H:%M"),
            "tipo": e.tipo_exame.nome if e.tipo_exame else "Exame",
            "local": e.local.nome if e.local else "",
            "medico": e.medico.nome if e.medico else "",
            "status": e.status.value,
            "observacoes": e.observacoes or "",
            "resultado": e.resultado or "",
            "anexos": anexos,
        })

    return _render("modal_semana_exames.html", {
        "seg": seg.strftime("%d/%m"),
        "dom": dom.strftime("%d/%m"),
        "exames": dados,
        "token": token,
    })


@router.get("/anexo/{anexo_id}")
def servir_anexo(anexo_id: int, token: str, db: Session = Depends(get_db)):
    from fastapi.responses import FileResponse
    responsavel = _get_responsavel(token, db)
    anexo = db.query(AnexoExame).filter_by(id=anexo_id).first()
    if not anexo:
        raise HTTPException(status_code=404)
    exame = db.query(Exame).filter_by(id=anexo.exame_id).first()
    if not exame or exame.paciente_id != responsavel.paciente_id:
        raise HTTPException(status_code=403)
    import mimetypes, os
    if not os.path.exists(anexo.caminho):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado no servidor")
    mt, _ = mimetypes.guess_type(anexo.caminho)
    return FileResponse(
        path=anexo.caminho,
        media_type=mt or "application/octet-stream",
        filename=anexo.nome,
    )


@router.post("/consulta/{consulta_id}/confirmar", response_class=RedirectResponse)
def confirmar_consulta(consulta_id: int, token: str = Form(...), db: Session = Depends(get_db)):
    responsavel = _get_responsavel(token, db)
    consulta = db.query(Consulta).filter_by(id=consulta_id).first()
    if not consulta or consulta.paciente_id != responsavel.paciente_id:
        raise HTTPException(status_code=404)
    consulta.status = StatusAgendamento.realizada
    db.commit()
    return RedirectResponse(url=f"/familia/?token={token}", status_code=303)


@router.post("/adesao/{prescricao_id}/registrar", response_class=RedirectResponse)
def registrar_adesao(
    prescricao_id: int,
    token: str = Form(...),
    nivel: str = Form(...),
    observacoes: str = Form(""),
    semana_override: str = Form(""),
    db: Session = Depends(get_db),
):
    responsavel = _get_responsavel(token, db)
    prescricao = db.query(Prescricao).filter_by(id=prescricao_id).first()
    if not prescricao or prescricao.paciente_id != responsavel.paciente_id:
        raise HTTPException(status_code=404)

    from datetime import datetime
    if semana_override:
        seg = datetime.strptime(semana_override, "%Y-%m-%d").date()
    else:
        seg = _segunda(date.today())

    adesao = db.query(AdesaoTratamento).filter_by(prescricao_id=prescricao_id, semana=seg).first()
    if adesao:
        adesao.nivel = NivelAdesao[nivel]
        adesao.observacoes = observacoes
    else:
        db.add(AdesaoTratamento(
            prescricao_id=prescricao_id, semana=seg,
            nivel=NivelAdesao[nivel], observacoes=observacoes,
        ))
    db.commit()
    return RedirectResponse(url=f"/familia/?token={token}", status_code=303)
