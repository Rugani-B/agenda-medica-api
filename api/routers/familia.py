from fastapi import APIRouter, Depends, HTTPException, Form, Query, Request, Response, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from sqlalchemy.orm import Session
from datetime import date, timedelta
from collections import defaultdict
import calendar
import json
import os
import re
import hmac
import hashlib

from jinja2 import Environment, FileSystemLoader

from api.database import get_db
import app.models
from app.models.pacientes import Paciente
from app.models.consulta import Consulta
from app.models.exame import Exame
from app.models.prescricao import Prescricao
from app.models.adesao_tratamento import AdesaoTratamento, NivelAdesao
from app.models.base_enums import StatusAgendamento
from app.models.pedido_exame import PedidoExame
from app.models.anexo_exame import AnexoExame
from app.models.usuario import Usuario, PerfilUsuario
from app.models.usuario_paciente import UsuarioPaciente

router = APIRouter(prefix="/familia", tags=["familia"])

_templates_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
_jinja_env = Environment(loader=FileSystemLoader(_templates_dir), autoescape=True)

MESES_PT = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho",
            "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]

_COOKIE_NAME  = "session"
_COOKIE_MAX_AGE = 60 * 60 * 24 * 30          # 30 dias
_SECRET       = os.getenv("SECRET_KEY", "chave-secreta-padrao")


# ── Sessão assinada ───────────────────────────────────────────────────────────

def _assinar(usuario_id: int) -> str:
    msg = str(usuario_id).encode()
    sig = hmac.new(_SECRET.encode(), msg, hashlib.sha256).hexdigest()[:24]
    return f"{usuario_id}:{sig}"


def _verificar_sessao(valor: str | None) -> int | None:
    if not valor:
        return None
    try:
        uid_str, sig = valor.split(":", 1)
        esperado = _assinar(int(uid_str))
        if hmac.compare_digest(valor, esperado):
            return int(uid_str)
    except Exception:
        pass
    return None


_PERFIS_PORTAL_FAMILIA = {PerfilUsuario.familiar, PerfilUsuario.paciente}


def _get_usuario(session: str | None, db: Session) -> Usuario | None:
    uid = _verificar_sessao(session)
    if not uid:
        return None
    u = db.query(Usuario).filter_by(id=uid, ativo=True).first()
    if not u or u.perfil not in _PERFIS_PORTAL_FAMILIA:
        return None
    return u


def _get_paciente_id(usuario_id: int, db: Session) -> int | None:
    v = db.query(UsuarioPaciente).filter_by(usuario_id=usuario_id).first()
    return v.paciente_id if v else None


def _login_redirect():
    return RedirectResponse(url="/familia/login", status_code=303)


# ── Helpers HTML ──────────────────────────────────────────────────────────────

def _limpar_html(txt: str) -> str:
    if not txt:
        return ""
    txt = re.sub(r"<style[^>]*>.*?</style>", "", txt, flags=re.DOTALL | re.IGNORECASE)
    txt = re.sub(r"<head[^>]*>.*?</head>",   "", txt, flags=re.DOTALL | re.IGNORECASE)
    txt = re.sub(r"<script[^>]*>.*?</script>","", txt, flags=re.DOTALL | re.IGNORECASE)
    return txt.strip()


def _render(name: str, context: dict):
    t = _jinja_env.get_template(name)
    return HTMLResponse(t.render(**context), media_type="text/html; charset=utf-8")


# ── Utilitários de agenda ─────────────────────────────────────────────────────

def _segunda(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _semanas_do_mes(ano: int, mes: int):
    primeiro = date(ano, mes, 1)
    ultimo   = date(ano, mes, calendar.monthrange(ano, mes)[1])
    seg = _segunda(primeiro)
    if seg < primeiro:
        seg += timedelta(weeks=1)
    resultado = []
    while seg <= ultimo:
        resultado.append(seg)
        seg += timedelta(weeks=1)
    return resultado


def _build_mes_eventos(paciente_id: int, ano: int, mes: int, db: Session) -> dict:
    primeiro = date(ano, mes, 1)
    ultimo   = date(ano, mes, calendar.monthrange(ano, mes)[1])

    consultas   = db.query(Consulta).filter(
        Consulta.paciente_id == paciente_id,
        Consulta.data_hora >= primeiro, Consulta.data_hora <= ultimo,
    ).all()
    exames = db.query(Exame).filter(
        Exame.paciente_id == paciente_id,
        Exame.data_hora >= primeiro, Exame.data_hora <= ultimo,
    ).all()
    prescricoes = db.query(Prescricao).filter(
        Prescricao.paciente_id == paciente_id,
        Prescricao.semana_inicio <= ultimo, Prescricao.semana_fim >= primeiro,
    ).all()

    adesoes = {a.semana: a for p in prescricoes for a in p.adesoes if primeiro <= a.semana <= ultimo}
    eventos = defaultdict(lambda: {"consultas": [], "exames": [], "tratamentos": []})

    for c in consultas:
        dia = c.data_hora.date().isoformat()
        esp = (c.medico.especialidade.nome if c.medico and c.medico.especialidade
               else (c.medico.nome if c.medico else "Médico n/i"))
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
            "resultado": _limpar_html(e.resultado),
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
                    "prescricao_id": p.id, "medicamentos": meds,
                    "semana_seg": seg.isoformat(), "semana_dom": dom.isoformat(),
                    "adesao": adesao.nivel.value if adesao else None,
                })
            seg += timedelta(weeks=1)

    return dict(eventos)


def _build_ano_calendarios(paciente_id: int, ano: int, db: Session) -> dict:
    inicio = date(ano, 1, 1)
    fim    = date(ano, 12, 31)

    consultas   = db.query(Consulta).filter(
        Consulta.paciente_id == paciente_id,
        Consulta.data_hora >= inicio, Consulta.data_hora <= fim,
    ).all()
    exames = db.query(Exame).filter(
        Exame.paciente_id == paciente_id,
        Exame.data_hora >= inicio, Exame.data_hora <= fim,
    ).all()
    prescricoes = db.query(Prescricao).filter(
        Prescricao.paciente_id == paciente_id,
        Prescricao.semana_inicio <= fim, Prescricao.semana_fim >= inicio,
    ).all()

    cons_sem  = defaultdict(list)
    for c in consultas:
        seg = _segunda(c.data_hora.date())
        esp = c.medico.especialidade.nome if c.medico and c.medico.especialidade else ""
        cons_sem[seg].append(esp or (c.medico.nome if c.medico else "Consulta"))

    exam_sem = defaultdict(list)
    for e in exames:
        seg = _segunda(e.data_hora.date())
        exam_sem[seg].append(e.tipo_exame.nome if e.tipo_exame else "Exame")

    adesoes_ano = {}
    for p in prescricoes:
        for a in p.adesoes:
            if inicio <= a.semana <= fim:
                adesoes_ano[(p.id, a.semana)] = a.nivel.value

    NIVEL_COR = {"nenhuma":"#888780","baixa":"#E24B4A","parcial":"#EF9F27","boa":"#378ADD","total":"#639922"}
    NIVEL_PCT = {"nenhuma":0,"baixa":25,"parcial":50,"boa":75,"total":100}

    trat_sem = defaultdict(lambda: {"prescricoes": [], "n_meds": 0})
    for p in prescricoes:
        meds = [i.medicamento.nome for i in p.itens]
        seg  = _segunda(inicio)
        while seg <= fim:
            if p.semana_inicio <= seg <= p.semana_fim:
                nivel = adesoes_ano.get((p.id, seg))
                trat_sem[seg]["prescricoes"].append({
                    "id": p.id, "medicamentos": meds, "nivel": nivel,
                    "cor": NIVEL_COR.get(nivel, "#ccc") if nivel else None,
                    "pct": NIVEL_PCT.get(nivel, 0) if nivel else 0,
                })
                trat_sem[seg]["n_meds"] += len(meds)
            seg += timedelta(weeks=1)

    def montar_meses(dados_por_semana, tipo="lista"):
        meses   = []
        max_sem = 0
        for mes in range(1, 13):
            semanas = _semanas_do_mes(ano, mes)
            max_sem = max(max_sem, len(semanas))
            cells = []
            for s in semanas:
                dado = dados_por_semana.get(s)
                conteudo = dado if dado else ({"prescricoes":[],"n_meds":0} if tipo=="trat" else [])
                cells.append({
                    "seg": s.isoformat(),
                    "label_num":  s.isocalendar().week,
                    "label_data": s.strftime("%d/%m"),
                    "conteudo": conteudo,
                })
            meses.append({"nome": MESES_PT[mes-1][:3], "semanas": cells})
        return {"meses": meses, "max_semanas": max_sem}

    MESES_ABR = ["jan","fev","mar","abr","mai","jun","jul","ago","set","out","nov","dez"]
    def fmt_data(dt): return f"{dt.day:02d}/{MESES_ABR[dt.month-1]}"

    lista_consultas = sorted([
        {"id": c.id, "seg": _segunda(c.data_hora.date()).isoformat(),
         "data": fmt_data(c.data_hora), "data_ord": c.data_hora.date().isoformat(),
         "especialidade": c.medico.especialidade.nome if c.medico and c.medico.especialidade else "",
         "medico": c.medico.nome if c.medico else "", "status": c.status.value}
        for c in consultas
    ], key=lambda x: x["data_ord"], reverse=True)

    lista_exames = sorted([
        {"seg": _segunda(e.data_hora.date()).isoformat(),
         "data": fmt_data(e.data_hora), "data_ord": e.data_hora.date().isoformat(),
         "tipo": e.tipo_exame.nome if e.tipo_exame else "Exame",
         "local": e.local.nome if e.local else "", "status": e.status.value}
        for e in exames
    ], key=lambda x: x["data_ord"], reverse=True)

    hoje       = date.today()
    seg_atual  = _segunda(hoje)

    historico_adesao = {}
    for p in prescricoes:
        historico_adesao[p.id] = sorted(
            [{"seg": a.semana.isoformat(),
              "pct": NIVEL_PCT.get(a.nivel.value, 0),
              "cor": NIVEL_COR.get(a.nivel.value, "#ccc")}
             for a in p.adesoes],
            key=lambda x: x["seg"]
        )

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
        adesao_atual = adesoes_ano.get((p.id, seg_atual))
        meds = [
            f"{i.medicamento.nome} {i.dose or ''}".strip()
            + (f" — {i.frequencia}" if i.frequencia else "")
            for i in p.itens
        ]
        lista_tratamentos.append({
            "id": p.id,
            "medico": p.medico.nome if p.medico else "",
            "periodo": f"{p.semana_inicio.strftime('%d/%m/%Y')} → {p.semana_fim.strftime('%d/%m/%Y')}"
                       if p.semana_inicio and p.semana_fim else "",
            "ativa": status_trat == "ativa",
            "status_trat": status_trat,
            "medicamentos": meds,
            "adesao_atual": adesao_atual,
            "adesao_cor":   NIVEL_COR.get(adesao_atual, "#ccc") if adesao_atual else None,
            "adesao_pct":   NIVEL_PCT.get(adesao_atual, 0) if adesao_atual else 0,
            "seg_atual": seg_atual.isoformat(),
            "historico": historico_adesao.get(p.id, []),
        })

    return {
        "consultas":       montar_meses(cons_sem),
        "exames":          montar_meses(exam_sem),
        "tratamentos":     montar_meses(trat_sem, tipo="trat"),
        "lista_consultas": lista_consultas,
        "lista_exames":    lista_exames,
        "lista_tratamentos": lista_tratamentos,
    }


def _resumo_semana(paciente_id: int, db: Session) -> dict:
    hoje = date.today()
    seg  = _segunda(hoje)
    dom  = seg + timedelta(days=6)

    consultas   = db.query(Consulta).filter(
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
        "consultas": len(consultas), "exames": len(exames),
        "tratamentos_ativos": len(prescricoes),
        "semana_seg": seg.strftime("%d/%m"), "semana_dom": dom.strftime("%d/%m"),
        "lista_consultas": [
            {"data": c.data_hora.strftime("%a %d/%m %H:%M"),
             "medico": c.medico.nome if c.medico else "n/i",
             "especialidade": c.medico.especialidade.nome if c.medico and c.medico.especialidade else "",
             "status": c.status.value}
            for c in consultas
        ],
        "lista_exames": [
            {"data": e.data_hora.strftime("%a %d/%m %H:%M"),
             "tipo": e.tipo_exame.nome if e.tipo_exame else "Exame",
             "local": e.local.nome if e.local else "", "status": e.status.value}
            for e in exames
        ],
        "lista_tratamentos": [
            {"medicamentos": [f"{i.medicamento.nome} {i.dose or ''}".strip() for i in p.itens]}
            for p in prescricoes
        ],
    }


# ── Rotas de autenticação ─────────────────────────────────────────────────────

@router.get("/login", response_class=HTMLResponse)
def login_page(erro: str = Query(default=None)):
    msg_erro = ""
    if erro == "credenciais":
        msg_erro = "<p style='color:#c0392b;margin:0 0 1rem'>E-mail ou senha inválidos.</p>"
    elif erro == "acesso":
        msg_erro = "<p style='color:#c0392b;margin:0 0 1rem'>Acesso negado para este perfil de usuário.</p>"
    elif erro == "sem_paciente":
        msg_erro = "<p style='color:#c0392b;margin:0 0 1rem'>Nenhum paciente vinculado a este usuário.</p>"

    html = f"""<!doctype html><html><head><meta charset="utf-8">
    <title>Acesso — Agenda Médica</title>
    <style>
      body{{font-family:sans-serif;display:flex;justify-content:center;align-items:center;
            height:100vh;margin:0;background:#f0f4f8}}
      form{{background:white;padding:2rem;border-radius:8px;
            box-shadow:0 2px 8px rgba(0,0,0,.15);min-width:320px}}
      h2{{margin:0 0 .5rem;color:#1a5276}}
      p.sub{{color:#666;font-size:.85rem;margin:0 0 1.5rem}}
      label{{font-size:.85rem;color:#444;display:block;margin-bottom:2px}}
      input{{width:100%;padding:.6rem;margin-bottom:1rem;box-sizing:border-box;
             border:1px solid #ccc;border-radius:4px;font-size:.95rem}}
      button{{width:100%;padding:.7rem;background:#1a5276;color:white;border:none;
              border-radius:4px;cursor:pointer;font-size:1rem}}
      button:hover{{background:#1f618d}}
    </style></head><body>
    <form method="post" action="/familia/login">
      <h2>Agenda Médica</h2>
      <p class="sub">Acesso para pacientes, familiares e responsáveis</p>
      {msg_erro}
      <label>E-mail</label>
      <input type="email" name="email" required autofocus autocomplete="username">
      <label>Senha</label>
      <input type="password" name="senha" required autocomplete="current-password">
      <button type="submit">Entrar</button>
    </form></body></html>"""
    return HTMLResponse(html)


@router.post("/login")
def login(
    email: str = Form(...),
    senha: str = Form(...),
    db: Session = Depends(get_db),
):
    u = db.query(Usuario).filter_by(email=email.strip().lower(), ativo=True).first()

    if not u or not u.verificar_senha(senha):
        return RedirectResponse(url="/familia/login?erro=credenciais", status_code=303)

    if u.perfil not in _PERFIS_PORTAL_FAMILIA:
        return RedirectResponse(url="/familia/login?erro=acesso", status_code=303)

    paciente_id = _get_paciente_id(u.id, db)
    if not paciente_id:
        return RedirectResponse(url="/familia/login?erro=sem_paciente", status_code=303)

    resp = RedirectResponse(url="/familia/", status_code=303)
    resp.set_cookie(_COOKIE_NAME, _assinar(u.id),
                    httponly=True, secure=True, samesite="lax", max_age=_COOKIE_MAX_AGE)
    return resp


@router.get("/logout")
def logout():
    resp = RedirectResponse(url="/familia/login", status_code=303)
    resp.delete_cookie(_COOKIE_NAME)
    return resp


# ── Rotas principais ──────────────────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse)
def agenda(
    request: Request,
    session: str = Cookie(default=None),
    ano: int = Query(default=None),
    mes: int = Query(default=None),
    db: Session = Depends(get_db),
):
    usuario = _get_usuario(session, db)
    if not usuario:
        return _login_redirect()

    paciente_id = _get_paciente_id(usuario.id, db)
    if not paciente_id:
        return _login_redirect()

    paciente = db.query(Paciente).filter_by(id=paciente_id).first()
    hoje = date.today()
    ano  = ano or hoje.year
    mes  = mes or hoje.month

    cal_mensal = calendar.monthcalendar(ano, mes)
    mes_ant  = mes - 1 if mes > 1 else 12
    ano_ant  = ano if mes > 1 else ano - 1
    mes_prox = mes + 1 if mes < 12 else 1
    ano_prox = ano if mes < 12 else ano + 1

    import time
    return _render("agenda.html", {
        "cache_bust":   int(time.time()),
        "paciente":     paciente,
        "responsavel":  usuario,          # templates usam responsavel.nome
        "resumo":       _resumo_semana(paciente_id, db),
        "eventos_json": json.dumps(_build_mes_eventos(paciente_id, ano, mes, db), ensure_ascii=False),
        "anual_json":   json.dumps(_build_ano_calendarios(paciente_id, ano, db), ensure_ascii=False),
        "cal": cal_mensal, "ano": ano, "mes": mes,
        "mes_nome": MESES_PT[mes - 1], "hoje": hoje.isoformat(),
        "mes_ant": mes_ant, "ano_ant": ano_ant,
        "mes_prox": mes_prox, "ano_prox": ano_prox,
    })


@router.get("/semana/{seg_str}", response_class=HTMLResponse)
def detalhe_semana(
    seg_str: str,
    session: str = Cookie(default=None),
    db: Session = Depends(get_db),
):
    from datetime import datetime as dt
    usuario = _get_usuario(session, db)
    if not usuario:
        return _login_redirect()
    paciente_id = _get_paciente_id(usuario.id, db)

    seg = dt.strptime(seg_str, "%Y-%m-%d").date()
    dom = seg + timedelta(days=6)

    consultas = db.query(Consulta).filter(
        Consulta.paciente_id == paciente_id,
        Consulta.data_hora >= seg, Consulta.data_hora <= dom,
    ).order_by(Consulta.data_hora).all()

    prescricoes_ativas = db.query(Prescricao).filter(
        Prescricao.paciente_id == paciente_id,
        Prescricao.semana_inicio <= seg, Prescricao.semana_fim >= seg,
    ).all()

    dados = []
    for c in consultas:
        pedidos = [{"tipo": p.tipo_exame.nome if p.tipo_exame else "Exame",
                    "status": p.status.value, "urgente": p.urgente,
                    "observacoes": p.observacoes or ""}
                   for p in c.pedidos_exame]
        prescs  = [{"medico": c.medico.nome if c.medico else "",
                    "itens": [f"{i.medicamento.nome} {i.dose or ''}".strip()
                              + (f" — {i.frequencia}" if i.frequencia else "")
                              for i in p.itens],
                    "observacoes": p.observacoes or ""}
                   for p in c.prescricoes]
        dados.append({
            "id": c.id, "data": c.data_hora.strftime("%a %d/%m"),
            "hora": c.data_hora.strftime("%H:%M"),
            "medico": c.medico.nome if c.medico else "Médico n/i",
            "especialidade": c.medico.especialidade.nome if c.medico and c.medico.especialidade else "",
            "status": c.status.value, "observacoes": c.observacoes or "",
            "pedidos": pedidos, "prescricoes": prescs,
        })

    presc_ativas = [
        {"medico": p.medico.nome if p.medico else "",
         "periodo": f"{p.semana_inicio.strftime('%d/%m')} → {p.semana_fim.strftime('%d/%m')}",
         "itens": [f"{i.medicamento.nome} {i.dose or ''}".strip()
                   + (f" — {i.frequencia}" if i.frequencia else "")
                   for i in p.itens]}
        for p in prescricoes_ativas
    ]

    return _render("modal_semana.html", {
        "seg": seg.strftime("%d/%m"), "dom": dom.strftime("%d/%m"),
        "consultas": dados, "prescricoes_ativas": presc_ativas,
    })


@router.get("/consulta/{consulta_id}/detalhe", response_class=HTMLResponse)
def detalhe_consulta(
    consulta_id: int,
    session: str = Cookie(default=None),
    db: Session = Depends(get_db),
):
    usuario = _get_usuario(session, db)
    if not usuario:
        return _login_redirect()
    paciente_id = _get_paciente_id(usuario.id, db)

    c = db.query(Consulta).filter_by(id=consulta_id).first()
    if not c or c.paciente_id != paciente_id:
        raise HTTPException(status_code=404)

    pedidos = [{"tipo": p.tipo_exame.nome if p.tipo_exame else "Exame",
                "status": p.status.value, "urgente": p.urgente,
                "observacoes": p.observacoes or ""}
               for p in c.pedidos_exame]
    prescs  = [{"itens": [f"{i.medicamento.nome} {i.dose or ''}".strip()
                           + (f" — {i.frequencia}" if i.frequencia else "")
                           for i in p.itens],
                "observacoes": p.observacoes or ""}
               for p in c.prescricoes]
    dado = {
        "id": c.id, "data": c.data_hora.strftime("%a %d/%m"),
        "hora": c.data_hora.strftime("%H:%M"),
        "medico": c.medico.nome if c.medico else "Médico n/i",
        "especialidade": c.medico.especialidade.nome if c.medico and c.medico.especialidade else "",
        "status": c.status.value, "observacoes": c.observacoes or "",
        "pedidos": pedidos, "prescricoes": prescs,
    }
    return _render("modal_consulta.html", {"consulta": dado})


@router.get("/semana-exames/{seg_str}", response_class=HTMLResponse)
def detalhe_semana_exames(
    seg_str: str,
    session: str = Cookie(default=None),
    db: Session = Depends(get_db),
):
    from datetime import datetime as dt
    usuario = _get_usuario(session, db)
    if not usuario:
        return _login_redirect()
    paciente_id = _get_paciente_id(usuario.id, db)

    seg = dt.strptime(seg_str, "%Y-%m-%d").date()
    dom = seg + timedelta(days=6)

    exames = db.query(Exame).filter(
        Exame.paciente_id == paciente_id,
        Exame.data_hora >= seg, Exame.data_hora <= dom,
    ).order_by(Exame.data_hora).all()

    dados = []
    for e in exames:
        anexos = [{"id": a.id, "nome": a.nome, "tipo": a.tipo,
                   "ext": a.caminho.rsplit(".", 1)[-1].lower() if "." in a.caminho else "bin"}
                  for a in e.anexos]
        dados.append({
            "id": e.id, "data": e.data_hora.strftime("%a %d/%m"),
            "hora": e.data_hora.strftime("%H:%M"),
            "tipo": e.tipo_exame.nome if e.tipo_exame else "Exame",
            "local": e.local.nome if e.local else "",
            "medico": e.medico.nome if e.medico else "",
            "status": e.status.value, "observacoes": e.observacoes or "",
            "resultado": _limpar_html(e.resultado), "anexos": anexos,
        })

    return _render("modal_semana_exames.html", {
        "seg": seg.strftime("%d/%m"), "dom": dom.strftime("%d/%m"), "exames": dados,
    })


@router.get("/anexo/{anexo_id}")
def servir_anexo(
    anexo_id: int,
    session: str = Cookie(default=None),
    db: Session = Depends(get_db),
):
    from fastapi.responses import RedirectResponse as Redirect
    usuario = _get_usuario(session, db)
    if not usuario:
        return _login_redirect()
    paciente_id = _get_paciente_id(usuario.id, db)

    anexo = db.query(AnexoExame).filter_by(id=anexo_id).first()
    if not anexo:
        raise HTTPException(status_code=404)
    exame = db.query(Exame).filter_by(id=anexo.exame_id).first()
    if not exame or exame.paciente_id != paciente_id:
        raise HTTPException(status_code=403)

    caminho = anexo.caminho or ""
    if caminho.startswith("http"):
        return Redirect(url=caminho, status_code=302)

    import mimetypes
    if not os.path.exists(caminho):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    mt, _ = mimetypes.guess_type(caminho)
    return FileResponse(path=caminho, media_type=mt or "application/octet-stream",
                        filename=anexo.nome)


@router.post("/consulta/{consulta_id}/confirmar", response_class=RedirectResponse)
def confirmar_consulta(
    consulta_id: int,
    session: str = Cookie(default=None),
    db: Session = Depends(get_db),
):
    usuario = _get_usuario(session, db)
    if not usuario:
        return _login_redirect()
    paciente_id = _get_paciente_id(usuario.id, db)

    consulta = db.query(Consulta).filter_by(id=consulta_id).first()
    if not consulta or consulta.paciente_id != paciente_id:
        raise HTTPException(status_code=404)

    from datetime import datetime as dt
    from app.models.confirmacao import Confirmacao, StatusConfirmacao
    consulta.status = StatusAgendamento.realizada
    conf = db.query(Confirmacao).filter_by(consulta_id=consulta_id).first()
    if not conf:
        conf = Confirmacao(consulta_id=consulta_id)
        db.add(conf)
    conf.status       = StatusConfirmacao.realizada
    conf.respondido_em = dt.utcnow()
    conf.respondido    = usuario.nome
    conf.canal         = "web"
    db.commit()
    return RedirectResponse(url="/familia/", status_code=303)


@router.post("/adesao/{prescricao_id}/registrar", response_class=RedirectResponse)
def registrar_adesao(
    prescricao_id: int,
    session: str = Cookie(default=None),
    nivel: str = Form(...),
    observacoes: str = Form(""),
    semana_override: str = Form(""),
    db: Session = Depends(get_db),
):
    usuario = _get_usuario(session, db)
    if not usuario:
        return _login_redirect()
    paciente_id = _get_paciente_id(usuario.id, db)

    prescricao = db.query(Prescricao).filter_by(id=prescricao_id).first()
    if not prescricao or prescricao.paciente_id != paciente_id:
        raise HTTPException(status_code=404)

    from datetime import datetime
    seg = datetime.strptime(semana_override, "%Y-%m-%d").date() if semana_override else _segunda(date.today())

    adesao = db.query(AdesaoTratamento).filter_by(prescricao_id=prescricao_id, semana=seg).first()
    if adesao:
        adesao.nivel       = NivelAdesao[nivel]
        adesao.observacoes = observacoes
    else:
        db.add(AdesaoTratamento(
            prescricao_id=prescricao_id, semana=seg,
            nivel=NivelAdesao[nivel], observacoes=observacoes,
        ))
    db.commit()
    return RedirectResponse(url="/familia/", status_code=303)


@router.get("/relatorio")
def baixar_relatorio(
    session: str = Cookie(default=None),
    inicio: str = Query(default=None),
    fim: str = Query(default=None),
    db: Session = Depends(get_db),
):
    from datetime import datetime as dt
    import tempfile
    from app.services.relatorio_service import gerar_relatorio_paciente

    usuario = _get_usuario(session, db)
    if not usuario:
        return _login_redirect()
    paciente_id = _get_paciente_id(usuario.id, db)

    paciente = db.query(Paciente).filter_by(id=paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")

    hoje  = date.today()
    d_ini = dt.strptime(inicio, "%Y-%m-%d").date() if inicio else hoje - timedelta(days=90)
    d_fim = dt.strptime(fim,    "%Y-%m-%d").date() if fim    else hoje

    secoes = {"consultas": True, "exames": True, "prescricoes": True, "adesao": True}
    nome_arquivo = f"relatorio_{paciente.nome.replace(' ', '_')}_{d_ini.strftime('%Y%m%d')}.pdf"
    caminho = os.path.join(tempfile.gettempdir(), nome_arquivo)

    gerar_relatorio_paciente(paciente.id, d_ini, d_fim, secoes, caminho)

    return FileResponse(
        path=caminho, media_type="application/pdf", filename=nome_arquivo,
        headers={"Content-Disposition": f'attachment; filename="{nome_arquivo}"'},
    )
