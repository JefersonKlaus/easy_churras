"""Datas e horas como aparecem para a pessoa: '14:00' e 'sábado, 21/11 às 14:00'."""
from __future__ import annotations

from datetime import datetime

DIAS_DA_SEMANA = ("segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo")


def formatar_hora(hora: datetime) -> str:
    return hora.strftime("%H:%M")


def descrever_data(hora: datetime) -> str:
    """'sábado, 21/11 às 14:00'."""
    return f"{DIAS_DA_SEMANA[hora.weekday()]}, {hora:%d/%m} às {formatar_hora(hora)}"
