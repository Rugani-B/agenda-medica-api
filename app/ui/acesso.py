from app.models.usuario import PerfilUsuario

_PERFIS_ASSISTENTE = {
    PerfilUsuario.assistente,
    PerfilUsuario.enfermeira,
    PerfilUsuario.secretaria,
    PerfilUsuario.operador,
}


def eh_admin(usuario) -> bool:
    return usuario and usuario.perfil == PerfilUsuario.admin


def eh_assistente(usuario) -> bool:
    return usuario and usuario.perfil in _PERFIS_ASSISTENTE


def pode_editar(usuario) -> bool:
    return eh_admin(usuario) or eh_assistente(usuario)


def pode_excluir_paciente(usuario) -> bool:
    return eh_admin(usuario)


def pode_gerenciar_usuarios(usuario) -> bool:
    return eh_admin(usuario)
