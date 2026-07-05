# utils/constants.py ou models/base_enums.py
import enum


class StatusAgendamento(enum.Enum):
    agendada    = "agendada"
    confirmada  = "confirmada"
    reagendada  = "reagendada"
    cancelada   = "cancelada"
    realizada   = "realizada"
