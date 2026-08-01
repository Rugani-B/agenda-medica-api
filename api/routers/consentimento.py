import os
import re
import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session

from api.database import get_db
from app.models.consentimento import Consentimento
from app.models.pacientes import Paciente
from app.models.usuario import Usuario, PerfilUsuario
from app.models.usuario_paciente import UsuarioPaciente

router = APIRouter(tags=["consentimento"])

# Hash SHA-256 oficial do texto do termo (versão 1.0).
# Para recalcular: abra consentimento.html no browser, execute no console:
#   document.getElementById('termo-texto').innerText.replace(/\s+/g,' ').trim()
# Depois calcule SHA-256 do resultado e cole aqui.
# Deixando None em desenvolvimento — aceita qualquer hash enviado.
TERMOS_VALIDOS: dict[str, str | None] = {
    "1.0": None,   # None = não valida (substitua pelo hash real em produção)
}

_CPF_RE = re.compile(r"^\d{11}$")


def _validar_cpf(cpf: str) -> bool:
    cpf = re.sub(r"\D", "", cpf)
    if len(cpf) != 11 or len(set(cpf)) == 1:
        return False
    for t in (9, 10):
        soma = sum(int(cpf[i]) * (t + 1 - i) for i in range(t))
        if ((soma * 10) % 11) % 10 != int(cpf[t]):
            return False
    return True


def _gerar_protocolo() -> str:
    ano = datetime.now(timezone.utc).year
    num = secrets.randbelow(10 ** 8)
    return f"CST-{ano}-{num:08d}"


def _ip_do_request(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "0.0.0.0"


# ── Servir o formulário de consentimento ─────────────────────────────────────

_HTML_PATH = os.path.join(os.path.dirname(__file__), "..", "templates", "consentimento.html")


@router.get("/consentimento", response_class=HTMLResponse)
def pagina_consentimento():
    with open(_HTML_PATH, encoding="utf-8") as f:
        return HTMLResponse(f.read())


# ── Endpoint de registro ──────────────────────────────────────────────────────

@router.post("/api/consentimentos", status_code=201)
async def registrar_consentimento(request: Request, db: Session = Depends(get_db)):
    try:
        b = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="JSON inválido")

    # ── Validações mínimas ────────────────────────────────────────────────────
    titular = b.get("titular") or {}
    if not titular.get("nome") or len(titular["nome"].strip()) < 5:
        raise HTTPException(status_code=422, detail="Nome do titular incompleto")

    cpf_titular = re.sub(r"\D", "", titular.get("cpf", ""))
    if not _validar_cpf(cpf_titular):
        raise HTTPException(status_code=422, detail="CPF do titular inválido")

    cons = b.get("consentimentos") or {}
    if not cons.get("dados_comuns") or not cons.get("dados_sensiveis_saude"):
        raise HTTPException(status_code=422, detail="Consentimentos essenciais ausentes (4.1 e 4.2)")

    versao = b.get("versao_termo", "")
    if versao not in TERMOS_VALIDOS:
        raise HTTPException(status_code=409, detail="Versão do termo não reconhecida. Recarregue a página.")

    hash_esperado = TERMOS_VALIDOS[versao]
    hash_recebido = b.get("hash_termo_sha256", "")
    if hash_esperado is not None and hash_recebido != hash_esperado:
        raise HTTPException(status_code=409, detail="Hash do termo não confere. Recarregue a página.")

    # Representante legal (se houver)
    rep = b.get("representante_legal")
    if rep:
        if not rep.get("nome") or len(rep["nome"].strip()) < 5:
            raise HTTPException(status_code=422, detail="Nome do representante incompleto")
        if not _validar_cpf(re.sub(r"\D", "", rep.get("cpf", ""))):
            raise HTTPException(status_code=422, detail="CPF do representante inválido")

    pessoas = b.get("pessoas_autorizadas") or []
    if cons.get("compartilhamento_autorizados") and not pessoas:
        raise HTTPException(status_code=422, detail="Consentimento 4.3 marcado mas nenhuma pessoa adicionada")

    # ── Evidências do servidor ────────────────────────────────────────────────
    ip          = _ip_do_request(request)
    user_agent  = request.headers.get("user-agent")
    protocolo   = _gerar_protocolo()

    # ── Tenta vincular ao paciente cadastrado pelo CPF ────────────────────────
    titular_id = None
    paciente = db.query(Paciente).filter(Paciente.cpf == cpf_titular).first()
    if paciente:
        titular_id = paciente.id

    # ── Grava o consentimento ─────────────────────────────────────────────────
    registro = Consentimento(
        protocolo           = protocolo,
        titular_id          = titular_id,
        versao_termo        = versao,
        hash_termo_sha256   = hash_recebido or "",
        consentimentos_json = cons,
        pessoas_autorizadas = pessoas,
        assinatura_png_b64  = b.get("assinatura_png_base64"),
        titular_snapshot    = {
            "nome":       titular.get("nome", "").strip(),
            "cpf":        cpf_titular,
            "nascimento": titular.get("nascimento"),
            "telefone":   titular.get("telefone"),
            "email":      titular.get("email"),
        },
        representante_legal = rep,
        ip                  = ip,
        ip_localizacao      = None,   # GeoIP pode ser adicionado futuramente
        user_agent          = user_agent,
        evidencias_cliente  = b.get("evidencias_cliente"),
    )
    db.add(registro)
    db.flush()  # obtém registro.id sem commitar ainda

    # ── Ativa vínculos RBAC das pessoas autorizadas ───────────────────────────
    if cons.get("compartilhamento_autorizados") and paciente:
        for pessoa in pessoas:
            nivel = pessoa.get("nivel")
            if not nivel:
                continue
            cpf_p = re.sub(r"\D", "", pessoa.get("cpf", ""))
            # Busca usuário pelo CPF (via snapshot do nome como fallback)
            usuario = None
            if cpf_p and len(cpf_p) == 11:
                # Tenta achar usuário cujo paciente vinculado tem esse CPF
                pac_p = db.query(Paciente).filter(Paciente.cpf == cpf_p).first()
                if pac_p:
                    vp = db.query(UsuarioPaciente).filter_by(paciente_id=pac_p.id).first()
                    if vp:
                        usuario = db.query(Usuario).filter_by(id=vp.usuario_id, ativo=True).first()

            # Se achou usuário, cria/atualiza vínculo com o paciente titular
            if usuario:
                vinculo = db.query(UsuarioPaciente).filter_by(
                    usuario_id=usuario.id, paciente_id=paciente.id
                ).first()
                if vinculo:
                    vinculo.nivel            = nivel
                    vinculo.protocolo_origem = protocolo
                else:
                    db.add(UsuarioPaciente(
                        usuario_id       = usuario.id,
                        paciente_id      = paciente.id,
                        nivel            = nivel,
                        protocolo_origem = protocolo,
                    ))

    db.commit()
    db.refresh(registro)

    return JSONResponse(status_code=201, content={
        "protocolo":    protocolo,
        "registrado_em": registro.registrado_em.strftime("%d/%m/%Y %H:%M:%S UTC"),
        "ip_registrado": ip,
    })


# ── Revogar consentimento (autenticado como paciente/familiar) ────────────────

@router.post("/api/consentimentos/{protocolo}/revogar", status_code=200)
async def revogar_consentimento(
    protocolo: str,
    request: Request,
    db: Session = Depends(get_db),
):
    registro = db.query(Consentimento).filter_by(protocolo=protocolo).first()
    if not registro:
        raise HTTPException(status_code=404, detail="Protocolo não encontrado")
    if registro.revogado_em:
        raise HTTPException(status_code=409, detail="Consentimento já revogado")

    body = {}
    try:
        body = await request.json()
    except Exception:
        pass

    registro.revogado_em       = datetime.now(timezone.utc)
    registro.revogacao_detalhe = {
        "motivo":   body.get("motivo", "Revogação pelo titular"),
        "canal":    "web",
        "por_quem": body.get("por_quem", "titular"),
        "ip":       _ip_do_request(request),
    }

    # Desativa vínculos RBAC que vieram deste protocolo
    vinculos = db.query(UsuarioPaciente).filter_by(protocolo_origem=protocolo).all()
    for v in vinculos:
        db.delete(v)

    db.commit()
    return {"revogado_em": registro.revogado_em.isoformat()}
