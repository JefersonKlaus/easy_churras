"""Leitura e validação do que o usuário digita (datas e horas)."""
from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Optional


def ler_data(texto: str, hoje: Optional[date] = None) -> date:
    """Aceita 'dd/mm/aaaa' ou 'dd/mm' (assume este ano, ou o próximo se já passou)."""
    hoje = hoje or date.today()
    partes = texto.strip().replace("-", "/").replace(".", "/").split("/")
    try:
        numeros = [int(p) for p in partes]
    except ValueError:
        raise ValueError("escreva a data assim: 21/11/2026") from None
    if len(numeros) == 2:
        dia, mes = numeros
        try:
            data = date(hoje.year, mes, dia)
        except ValueError:
            raise ValueError("essa data não existe") from None
        return data if data >= hoje else date(hoje.year + 1, mes, dia)
    if len(numeros) == 3:
        dia, mes, ano = numeros
        if ano < 100:
            ano += 2000
        try:
            return date(ano, mes, dia)
        except ValueError:
            raise ValueError("essa data não existe") from None
    raise ValueError("escreva a data assim: 21/11/2026")


def ler_hora(texto: str) -> time:
    """Aceita '14:00', '14h', '14h30' ou '14'."""
    limpo = texto.strip().lower().replace("h", ":").replace(".", ":")
    if limpo.endswith(":"):
        limpo += "00"
    partes = limpo.split(":")
    try:
        horas = int(partes[0])
        minutos = int(partes[1]) if len(partes) > 1 and partes[1] else 0
        if len(partes) > 2:
            raise ValueError
        return time(horas, minutos)
    except (ValueError, IndexError):
        raise ValueError("escreva a hora assim: 14:00") from None


def combinar(data: date, hora: time) -> datetime:
    return datetime.combine(data, hora)


def proximo_sabado(hoje: Optional[date] = None) -> date:
    """O próximo sábado (hoje, se hoje for sábado)."""
    hoje = hoje or date.today()
    return hoje + timedelta(days=(5 - hoje.weekday()) % 7)


def formatar_data(data: date) -> str:
    return data.strftime("%d/%m/%Y")
