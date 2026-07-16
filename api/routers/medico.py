from fastapi import APIRouter, Depends, Form, Query, Cookie, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from datetime import date, timedelta, datetime
import os
import hmac
import hashlib

from jinja2 import Environment, FileSystemLoader

from api.database import get_db
import app.models
from app.models.medico import Medico
from app.models.pacientes import Paciente
from app.models.consulta import Consulta
from app.models.exame import Exame
from app.models.prescricao import Prescricao, PrescricaoItem
from app.models.pedido_exame import PedidoExame, StatusPedido
from app.models.medicamento import Medicamento
from app.models.tipo_exame import TipoExame
from app.models.usuario import Usuario, PerfilUsuario

router = APIRouter(prefix="/medico", tags=["medico"])

_templates_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
_jinja_env = Environment(loader=FileSystemLoader(_templates_dir), autoescape=True)

_COOKIE_NAME    = "medico_session"
_COOKIE_MAX_AGE = 60 * 60 * 24 * 30
_SECRET         = os.getenv("SECRET_KEY", "chave-secreta-padrao")


# ── Sessão ────────────────────────────────────────────────────────────────────

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


def _get_usuario_medico(session: str | None, db: Session) -> tuple[Usuario, Medico] | tuple[None, None]:
    uid = _verificar_sessao(session)
    if not uid:
        return None, None
    u = db.query(Usuario).filter_by(id=uid, ativo=True).first()
    if not u or u.perfil != PerfilUsuario.medico or not u.medico_id:
        return None, None
    m = db.query(Medico).filter_by(id=u.medico_id).first()
    if not m:
        return None, None
    return u, m


def _login_redirect():
    return RedirectResponse(url="/medico/login", status_code=303)


def _render(name: str, context: dict):
    t = _jinja_env.get_template(name)
    return HTMLResponse(t.render(**context), media_type="text/html; charset=utf-8")


# ── Pacientes do médico ───────────────────────────────────────────────────────

def _pacientes_do_medico(medico_id: int, db: Session) -> list[Paciente]:
    ids = (
        db.query(Consulta.paciente_id)
        .filter(Consulta.medico_id == medico_id)
        .distinct()
        .all()
    )
    if not ids:
        return []
    id_list = [r[0] for r in ids]
    return db.query(Paciente).filter(Paciente.id.in_(id_list)).order_by(Paciente.nome).all()


def _segunda(d: date) -> date:
    return d - timedelta(days=d.weekday())


# ── Auth ──────────────────────────────────────────────────────────────────────

@router.get("/login", response_class=HTMLResponse)
def login_page(erro: str = Query(default=None)):
    msgs = {
        "credenciais": "E-mail ou senha inválidos.",
        "acesso":      "Este usuário não tem perfil de médico.",
        "sem_medico":  "Nenhum médico vinculado a este usuário. Contate o administrador.",
    }
    msg_erro = f"<p class='erro'>{msgs[erro]}</p>" if erro in msgs else ""
    html = f"""<!doctype html><html><head><meta charset="utf-8">
    <title>Acesso Médico — Agenda</title>
    <style>
      *{{box-sizing:border-box;margin:0;padding:0}}
      body{{font-family:sans-serif;display:flex;justify-content:center;align-items:center;
            min-height:100vh;background:#eaf4fb}}
      .card{{background:white;padding:2.5rem;border-radius:10px;
             box-shadow:0 4px 16px rgba(0,0,0,.12);width:340px}}
      h2{{color:#0d6e8a;margin-bottom:.25rem;font-size:1.4rem}}
      .sub{{color:#666;font-size:.85rem;margin-bottom:1.5rem}}
      .erro{{color:#c0392b;font-size:.87rem;margin-bottom:1rem;
             background:#fdecea;padding:.5rem .75rem;border-radius:4px}}
      label{{font-size:.85rem;color:#444;display:block;margin-bottom:3px;margin-top:.75rem}}
      input{{width:100%;padding:.55rem .75rem;border:1px solid #ccc;
             border-radius:5px;font-size:.95rem}}
      input:focus{{outline:none;border-color:#0d6e8a}}
      button{{width:100%;margin-top:1.5rem;padding:.7rem;background:#0d6e8a;
              color:white;border:none;border-radius:5px;font-size:1rem;cursor:pointer}}
      button:hover{{background:#0a5870}}
      .icon{{font-size:2rem;text-align:center;margin-bottom:.75rem}}
    </style></head><body>
    <div class="card">
      <div class="icon">🩺</div>
      <h2>Portal do Médico</h2>
      <p class="sub">Agenda Médica — acesso profissional</p>
      {msg_erro}
      <form method="post" action="/medico/login">
        <label>E-mail</label>
        <input type="email" name="email" required autofocus autocomplete="username">
        <label>Senha</label>
        <input type="password" name="senha" required autocomplete="current-password">
        <button type="submit">Entrar</button>
      </form>
    </div></body></html>"""
    return HTMLResponse(html)


@router.post("/login")
def login(
    email: str = Form(...),
    senha: str = Form(...),
    db: Session = Depends(get_db),
):
    u = db.query(Usuario).filter_by(email=email.strip().lower(), ativo=True).first()
    if not u or not u.verificar_senha(senha):
        return RedirectResponse(url="/medico/login?erro=credenciais", status_code=303)
    if u.perfil != PerfilUsuario.medico:
        return RedirectResponse(url="/medico/login?erro=acesso", status_code=303)
    if not u.medico_id:
        return RedirectResponse(url="/medico/login?erro=sem_medico", status_code=303)

    resp = RedirectResponse(url="/medico/", status_code=303)
    resp.set_cookie(_COOKIE_NAME, _assinar(u.id),
                    httponly=True, secure=True, samesite="lax", max_age=_COOKIE_MAX_AGE)
    return resp


@router.get("/logout")
def logout():
    resp = RedirectResponse(url="/medico/login", status_code=303)
    resp.delete_cookie(_COOKIE_NAME)
    return resp


# ── Dashboard: lista de pacientes ─────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse)
def dashboard(
    medico_session: str = Cookie(default=None),
    db: Session = Depends(get_db),
):
    usuario, medico = _get_usuario_medico(medico_session, db)
    if not usuario:
        return _login_redirect()

    pacientes = _pacientes_do_medico(medico.id, db)

    hoje = date.today()
    resumo = []
    for p in pacientes:
        proxima = (
            db.query(Consulta)
            .filter(Consulta.paciente_id == p.id, Consulta.medico_id == medico.id,
                    Consulta.data_hora >= hoje)
            .order_by(Consulta.data_hora)
            .first()
        )
        ultima = (
            db.query(Consulta)
            .filter(Consulta.paciente_id == p.id, Consulta.medico_id == medico.id,
                    Consulta.data_hora < hoje)
            .order_by(Consulta.data_hora.desc())
            .first()
        )
        resumo.append({
            "id": p.id, "nome": p.nome, "idade": p.idade,
            "proxima_consulta": proxima.data_hora.strftime("%d/%m/%Y %H:%M") if proxima else None,
            "ultima_consulta":  ultima.data_hora.strftime("%d/%m/%Y")        if ultima  else None,
        })

    return _render("medico_dashboard.html", {
        "medico": medico, "usuario": usuario, "pacientes": resumo,
    })


# ── Detalhe do paciente ───────────────────────────────────────────────────────

@router.get("/paciente/{paciente_id}", response_class=HTMLResponse)
def detalhe_paciente(
    paciente_id: int,
    request: Request,
    ok: str = Query(default=None),
    medico_session: str = Cookie(default=None),
    db: Session = Depends(get_db),
):
    usuario, medico = _get_usuario_medico(medico_session, db)
    if not usuario:
        return _login_redirect()

    # Verifica que este médico tem consulta com o paciente
    tem_acesso = db.query(Consulta).filter_by(
        paciente_id=paciente_id, medico_id=medico.id
    ).first()
    if not tem_acesso:
        return RedirectResponse(url="/medico/", status_code=303)

    paciente = db.query(Paciente).filter_by(id=paciente_id).first()

    consultas = (
        db.query(Consulta)
        .filter(Consulta.paciente_id == paciente_id, Consulta.medico_id == medico.id)
        .order_by(Consulta.data_hora.desc())
        .all()
    )
    prescricoes = (
        db.query(Prescricao)
        .filter(Prescricao.paciente_id == paciente_id, Prescricao.medico_id == medico.id)
        .order_by(Prescricao.criado_em.desc())
        .all()
    )
    pedidos = (
        db.query(PedidoExame)
        .filter(PedidoExame.paciente_id == paciente_id, PedidoExame.medico_id == medico.id)
        .order_by(PedidoExame.criado_em.desc())
        .all()
    )
    exames = (
        db.query(Exame)
        .filter(Exame.paciente_id == paciente_id, Exame.medico_id == medico.id)
        .order_by(Exame.data_hora.desc())
        .limit(20)
        .all()
    )
    medicamentos = db.query(Medicamento).order_by(Medicamento.nome).all()
    tipos_exame  = db.query(TipoExame).order_by(TipoExame.nome).all()

    return _render("medico_paciente.html", {
        "medico": medico, "usuario": usuario, "paciente": paciente,
        "consultas": consultas, "prescricoes": prescricoes,
        "pedidos": pedidos, "exames": exames,
        "medicamentos": medicamentos, "tipos_exame": tipos_exame,
        "ok": ok,
    })


# ── Criar prescrição ──────────────────────────────────────────────────────────

@router.post("/paciente/{paciente_id}/prescricao")
def criar_prescricao(
    paciente_id: int,
    medico_session: str = Cookie(default=None),
    consulta_id: int = Form(...),
    semana_inicio: str = Form(...),
    semana_fim: str = Form(...),
    observacoes: str = Form(""),
    med_ids:  list[int]  = Form(default=[]),
    doses:    list[str]  = Form(default=[]),
    freqs:    list[str]  = Form(default=[]),
    db: Session = Depends(get_db),
):
    usuario, medico = _get_usuario_medico(medico_session, db)
    if not usuario:
        return _login_redirect()

    consulta = db.query(Consulta).filter_by(id=consulta_id, paciente_id=paciente_id,
                                             medico_id=medico.id).first()
    if not consulta:
        return RedirectResponse(url=f"/medico/paciente/{paciente_id}", status_code=303)

    d_ini = datetime.strptime(semana_inicio, "%Y-%m-%d").date()
    d_fim = datetime.strptime(semana_fim,    "%Y-%m-%d").date()
    # Garante que são segundas-feiras
    d_ini = _segunda(d_ini)
    d_fim = _segunda(d_fim)

    presc = Prescricao(
        consulta_id=consulta_id, paciente_id=paciente_id,
        medico_id=medico.id, observacoes=observacoes or None,
        semana_inicio=d_ini, semana_fim=d_fim,
    )
    db.add(presc)
    db.flush()

    for med_id, dose, freq in zip(med_ids, doses, freqs):
        if med_id:
            db.add(PrescricaoItem(
                prescricao_id=presc.id, medicamento_id=med_id,
                dose=dose or None, frequencia=freq or None,
            ))
    db.commit()
    return RedirectResponse(url=f"/medico/paciente/{paciente_id}?ok=prescricao", status_code=303)


# ── Criar pedido de exame ─────────────────────────────────────────────────────

@router.post("/paciente/{paciente_id}/pedido")
def criar_pedido(
    paciente_id: int,
    medico_session: str = Cookie(default=None),
    tipo_exame_id: int = Form(...),
    urgente: str = Form("0"),
    observacoes: str = Form(""),
    consulta_id: str = Form(""),
    db: Session = Depends(get_db),
):
    usuario, medico = _get_usuario_medico(medico_session, db)
    if not usuario:
        return _login_redirect()

    # Confirma acesso ao paciente
    tem_acesso = db.query(Consulta).filter_by(
        paciente_id=paciente_id, medico_id=medico.id
    ).first()
    if not tem_acesso:
        return RedirectResponse(url="/medico/", status_code=303)

    c_id = int(consulta_id) if consulta_id.strip() else None
    db.add(PedidoExame(
        paciente_id=paciente_id, medico_id=medico.id,
        tipo_exame_id=tipo_exame_id,
        urgente=urgente == "1",
        observacoes=observacoes or None,
        consulta_id=c_id,
        status=StatusPedido.solicitado,
    ))
    db.commit()
    return RedirectResponse(url=f"/medico/paciente/{paciente_id}?ok=pedido", status_code=303)
