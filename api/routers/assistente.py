from fastapi import APIRouter, Depends, Request, Response, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
import os, hmac, hashlib

from jinja2 import Environment, FileSystemLoader

from api.database import get_db
import app.models  # garante registro de todos os modelos
from app.models.usuario import Usuario, PerfilUsuario
from app.models.pacientes import Paciente
from app.models.consulta import Consulta
from app.models.exame import Exame, StatusExame
from app.models.prescricao import Prescricao
from app.models.adesao_tratamento import NivelAdesao, NIVEL_LABELS
from app.models.medico import Medico
from app.models.tipo_exame import TipoExame
from app.models.local_exame import LocalExame
from app.models.base_enums import StatusAgendamento
from app.services.auditoria_service import registrar_log

router = APIRouter(prefix="/assistente", tags=["assistente"])

_templates_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
_jinja = Environment(loader=FileSystemLoader(_templates_dir), autoescape=True)

_COOKIE     = "assistente_session"
_MAX_AGE    = 60 * 60 * 24 * 30
_SECRET     = os.getenv("SECRET_KEY", "chave-secreta-padrao")


# ── Sessão ───────────────────────────────────────────────────────────────────

def _assinar(uid: int) -> str:
    sig = hmac.new(_SECRET.encode(), str(uid).encode(), hashlib.sha256).hexdigest()[:24]
    return f"{uid}:{sig}"

def _verificar(valor: str | None) -> int | None:
    if not valor:
        return None
    try:
        uid_str, sig = valor.split(":", 1)
        if hmac.compare_digest(valor, _assinar(int(uid_str))):
            return int(uid_str)
    except Exception:
        pass
    return None

def _get_assistente(request: Request, db: Session) -> Usuario | None:
    uid = _verificar(request.cookies.get(_COOKIE))
    if not uid:
        return None
    u = db.query(Usuario).filter_by(id=uid, ativo=True).first()
    if u and u.perfil == PerfilUsuario.assistente:
        return u
    return None

def _login_required(request: Request, db: Session = Depends(get_db)):
    u = _get_assistente(request, db)
    if not u:
        raise HTTPException(status_code=307, headers={"Location": "/assistente/login"})
    return u, db

def _ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")
    return xff.split(",")[0].strip() if xff else (request.client.host if request.client else "0.0.0.0")

def _render(tpl: str, **ctx) -> HTMLResponse:
    return HTMLResponse(_jinja.get_template(tpl).render(**ctx))


# ── Login / Logout ────────────────────────────────────────────────────────────

@router.get("/login", response_class=HTMLResponse)
def login_page(erro: str = ""):
    return _render("assistente_login.html", erro=erro)

@router.post("/login")
async def login_post(request: Request, db: Session = Depends(get_db),
                     email: str = Form(""), senha: str = Form("")):
    u = db.query(Usuario).filter_by(email=email.strip(), ativo=True).first()
    if not u or u.perfil != PerfilUsuario.assistente or not u.verificar_senha(senha):
        return _render("assistente_login.html", erro="E-mail ou senha incorretos.")
    resp = RedirectResponse("/assistente/", status_code=303)
    resp.set_cookie(_COOKIE, _assinar(u.id), max_age=_MAX_AGE, httponly=True, samesite="lax")
    registrar_log(db, "login", "assistente", usuario_id=u.id, ip=_ip(request))
    return resp

@router.get("/logout")
def logout():
    resp = RedirectResponse("/assistente/login", status_code=303)
    resp.delete_cookie(_COOKIE)
    return resp


# ── Dashboard — agenda do dia ─────────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    u = _get_assistente(request, db)
    if not u:
        return RedirectResponse("/assistente/login", status_code=303)

    hoje = date.today()
    amanha = hoje + timedelta(days=1)

    consultas_hoje = (
        db.query(Consulta)
        .filter(Consulta.data_hora >= datetime.combine(hoje, datetime.min.time()),
                Consulta.data_hora <  datetime.combine(amanha, datetime.min.time()))
        .order_by(Consulta.data_hora)
        .all()
    )
    exames_hoje = (
        db.query(Exame)
        .filter(Exame.data_hora >= datetime.combine(hoje, datetime.min.time()),
                Exame.data_hora <  datetime.combine(amanha, datetime.min.time()))
        .order_by(Exame.data_hora)
        .all()
    )

    eventos = []
    for c in consultas_hoje:
        esp = c.medico.especialidade.nome if c.medico and c.medico.especialidade else ""
        eventos.append({
            "hora":     c.data_hora.strftime("%H:%M"),
            "tipo":     "consulta",
            "paciente": c.paciente.nome if c.paciente else "—",
            "pac_id":   c.paciente_id,
            "detalhe":  c.medico.nome if c.medico else "Sem médico",
            "extra":    esp,
            "status":   c.status.value if c.status else "",
        })
    for e in exames_hoje:
        eventos.append({
            "hora":     e.data_hora.strftime("%H:%M"),
            "tipo":     "exame",
            "paciente": e.paciente.nome if e.paciente else "—",
            "pac_id":   e.paciente_id,
            "detalhe":  e.tipo_exame.nome if e.tipo_exame else "Exame",
            "extra":    e.local.nome if e.local else "",
            "status":   e.status.value if e.status else "",
        })
    eventos.sort(key=lambda x: x["hora"])

    # Próximos 7 dias
    proximos = (
        db.query(Consulta)
        .filter(Consulta.data_hora >= datetime.combine(amanha, datetime.min.time()),
                Consulta.data_hora <  datetime.combine(hoje + timedelta(days=8), datetime.min.time()))
        .order_by(Consulta.data_hora)
        .limit(15)
        .all()
    )

    return _render("assistente_dashboard.html",
                   assistente=u.nome,
                   hoje=hoje.strftime("%d/%m/%Y"),
                   dia_semana=["Segunda","Terça","Quarta","Quinta","Sexta","Sábado","Domingo"][hoje.weekday()],
                   eventos=eventos,
                   proximos=proximos)


# ── Lista de pacientes ────────────────────────────────────────────────────────

@router.get("/pacientes", response_class=HTMLResponse)
def lista_pacientes(request: Request, q: str = "", db: Session = Depends(get_db)):
    u = _get_assistente(request, db)
    if not u:
        return RedirectResponse("/assistente/login", status_code=303)

    query = db.query(Paciente).filter_by(ativo=True)
    if q.strip():
        query = query.filter(Paciente.nome.ilike(f"%{q.strip()}%"))
    pacientes = query.order_by(Paciente.nome).all()

    return _render("assistente_pacientes.html",
                   assistente=u.nome, q=q, pacientes=pacientes)


# ── Detalhe do paciente ───────────────────────────────────────────────────────

@router.get("/paciente/{pid}", response_class=HTMLResponse)
def detalhe_paciente(pid: int, request: Request, aba: str = "agenda",
                     db: Session = Depends(get_db)):
    u = _get_assistente(request, db)
    if not u:
        return RedirectResponse("/assistente/login", status_code=303)

    pac = db.query(Paciente).filter_by(id=pid, ativo=True).first()
    if not pac:
        raise HTTPException(404, "Paciente não encontrado")

    hoje = date.today()

    # Agenda: próximas consultas e exames
    consultas = (
        db.query(Consulta)
        .filter(Consulta.paciente_id == pid)
        .order_by(Consulta.data_hora.desc())
        .limit(20).all()
    )
    exames = (
        db.query(Exame)
        .filter(Exame.paciente_id == pid)
        .order_by(Exame.data_hora.desc())
        .limit(20).all()
    )

    # Prescrições ativas
    prescricoes = (
        db.query(Prescricao)
        .filter(Prescricao.paciente_id == pid,
                Prescricao.semana_fim >= hoje)
        .order_by(Prescricao.semana_inicio.desc())
        .all()
    )
    presc_data = []
    for p in prescricoes:
        ultima_adesao = sorted(p.adesoes, key=lambda a: a.semana, reverse=True)
        nivel = ultima_adesao[0].nivel.value if ultima_adesao else None
        label, pct_str, cor = NIVEL_LABELS.get(nivel, ("—", "—", "#ccc")) if nivel else ("—", "—", "#ccc")
        presc_data.append({
            "id":          p.id,
            "medico":      p.medico.nome if p.medico else "—",
            "inicio":      p.semana_inicio.strftime("%d/%m/%Y") if p.semana_inicio else "—",
            "fim":         p.semana_fim.strftime("%d/%m/%Y")   if p.semana_fim   else "—",
            "observacoes": p.observacoes or "",
            "itens": [
                {"med": i.medicamento.nome, "dose": i.dose or "", "freq": i.frequencia or "", "dur": i.duracao or ""}
                for i in p.itens
            ],
            "adesao_nivel": nivel,
            "adesao_label": label,
            "adesao_cor":   cor,
        })

    # Dados auxiliares para formulários
    medicos      = db.query(Medico).order_by(Medico.nome).all()
    tipos_exame  = db.query(TipoExame).order_by(TipoExame.nome).all()
    locais_exame = db.query(LocalExame).order_by(LocalExame.nome).all()

    registrar_log(db, "leitura", "paciente", usuario_id=u.id, paciente_id=pid,
                  ip=_ip(request), detalhes={"aba": aba})

    ok = request.query_params.get("ok", "")
    return _render("assistente_paciente.html",
                   assistente=u.nome, pac=pac, aba=aba, ok=ok,
                   hoje=hoje,
                   consultas=consultas, exames=exames,
                   prescricoes=presc_data,
                   medicos=medicos, tipos_exame=tipos_exame, locais_exame=locais_exame,
                   StatusAgendamento=StatusAgendamento,
                   StatusExame=StatusExame)


# ── Agendar consulta ──────────────────────────────────────────────────────────

@router.post("/paciente/{pid}/consulta")
async def agendar_consulta(pid: int, request: Request, db: Session = Depends(get_db),
                           medico_id: int = Form(None), data_hora: str = Form(""),
                           observacoes: str = Form("")):
    u = _get_assistente(request, db)
    if not u:
        return RedirectResponse("/assistente/login", status_code=303)

    pac = db.query(Paciente).filter_by(id=pid, ativo=True).first()
    if not pac:
        raise HTTPException(404)

    try:
        dt = datetime.fromisoformat(data_hora)
    except ValueError:
        raise HTTPException(422, "Data/hora inválida")

    c = Consulta(paciente_id=pid, medico_id=medico_id or None,
                 data_hora=dt, observacoes=observacoes.strip() or None)
    db.add(c)
    db.commit()

    registrar_log(db, "criacao", "consulta", usuario_id=u.id, paciente_id=pid,
                  ip=_ip(request), detalhes={"medico_id": medico_id, "data_hora": data_hora})

    return RedirectResponse(f"/assistente/paciente/{pid}?aba=agenda&ok=consulta", status_code=303)


# ── Agendar exame ─────────────────────────────────────────────────────────────

@router.post("/paciente/{pid}/exame")
async def agendar_exame(pid: int, request: Request, db: Session = Depends(get_db),
                        tipo_exame_id: int = Form(...), local_id: int = Form(...),
                        medico_id: int = Form(None), data_hora: str = Form(""),
                        observacoes: str = Form("")):
    u = _get_assistente(request, db)
    if not u:
        return RedirectResponse("/assistente/login", status_code=303)

    pac = db.query(Paciente).filter_by(id=pid, ativo=True).first()
    if not pac:
        raise HTTPException(404)

    try:
        dt = datetime.fromisoformat(data_hora)
    except ValueError:
        raise HTTPException(422, "Data/hora inválida")

    e = Exame(paciente_id=pid, tipo_exame_id=tipo_exame_id, local_id=local_id,
              medico_id=medico_id or None, data_hora=dt,
              observacoes=observacoes.strip() or None)
    db.add(e)
    db.commit()

    registrar_log(db, "criacao", "exame", usuario_id=u.id, paciente_id=pid,
                  ip=_ip(request), detalhes={"tipo_exame_id": tipo_exame_id, "data_hora": data_hora})

    return RedirectResponse(f"/assistente/paciente/{pid}?aba=agenda&ok=exame", status_code=303)


# ── Cancelar consulta ─────────────────────────────────────────────────────────

@router.post("/paciente/{pid}/consulta/{cid}/cancelar")
async def cancelar_consulta(pid: int, cid: int, request: Request, db: Session = Depends(get_db)):
    u = _get_assistente(request, db)
    if not u:
        raise HTTPException(401)
    c = db.query(Consulta).filter_by(id=cid, paciente_id=pid).first()
    if not c:
        raise HTTPException(404)
    c.status = StatusAgendamento.cancelada
    db.commit()
    registrar_log(db, "edicao", "consulta", usuario_id=u.id, paciente_id=pid,
                  recurso_id=cid, ip=_ip(request), detalhes={"acao": "cancelar"})
    return JSONResponse({"ok": True})
