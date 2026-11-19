"""Ler um pedido escrito livremente ("12 pessoas, 3 crianças, 1 vegetariano") sem IA."""
from __future__ import annotations

import re
from typing import Optional

from ..convidados import MAX_PESSOAS
from ..esquemas import PedidoInterpretado
from .texto import normalizar

NUMEROS_POR_EXTENSO = {
    "um": 1, "uma": 1, "dois": 2, "duas": 2, "tres": 3, "quatro": 4, "cinco": 5, "seis": 6,
    "sete": 7, "oito": 8, "nove": 9, "dez": 10, "onze": 11, "doze": 12, "treze": 13,
    "quatorze": 14, "quinze": 15, "vinte": 20,
}
_NUMERO = r"(\d{1,3}|" + "|".join(NUMEROS_POR_EXTENSO) + r")"


def _como_inteiro(texto: str) -> Optional[int]:
    if texto.isdigit():
        valor = int(texto)
    else:
        valor = NUMEROS_POR_EXTENSO.get(texto)
    if valor is None or not 0 <= valor <= MAX_PESSOAS:
        return None
    return valor


def _achar_inteiro(texto: str, palavras: str) -> Optional[int]:
    achado = re.search(_NUMERO + r"\s+(?:" + palavras + r")\b", texto)
    return _como_inteiro(achado.group(1)) if achado else None


def _achar_duracao(texto: str) -> Optional[float]:
    """'4 horas' de duração; ignora horário como 'às 14 horas'."""
    for achado in re.finditer(r"(\d{1,2}(?:[.,]\d)?)\s*horas?\b", texto):
        antes = texto[:achado.start()].rstrip()
        if re.search(r"\b(as|a|ate|apos|depois das|por volta das)$", antes):
            continue
        horas = float(achado.group(1).replace(",", "."))
        if 1 <= horas <= 12:
            return horas
    return None


def interpretar_pedido_local(texto: str) -> PedidoInterpretado:
    """Lê "12 pessoas, 3 crianças, 1 vegetariano, 5 horas" sem usar IA."""
    t = normalizar(texto)
    criancas = _achar_inteiro(t, r"criancas?|crianca|pequenos|kids|filhos")
    vegetarianos = _achar_inteiro(t, r"vegetarian[oa]s?|veggies?")
    adultos = _achar_inteiro(t, r"adultos?|marmanjos?")
    total = _achar_inteiro(t, r"pessoas?|convidados?|amigos?|gente")
    bebem = _achar_inteiro(t, r"bebem|bebe|tomam|toma cerveja|bebedores?")
    if bebem is None and re.search(
            r"(ninguem bebe|sem alcool|nao bebem|ninguem toma|nao tem alcool)", t):
        bebem = 0

    faltando: list[str] = []
    if adultos is None and total is not None:
        adultos = max(1, total - (criancas or 0))        # as crianças contam dentro do total
        if criancas:
            faltando.append(f"se as {total} pessoas já incluem as crianças")
    elif adultos is None:
        faltando.append("quantos adultos")
    if adultos is not None and not 1 <= adultos <= MAX_PESSOAS:
        adultos = None
    return PedidoInterpretado(
        adultos=adultos, criancas=criancas, vegetarianos=vegetarianos, bebem_alcool=bebem,
        duracao_horas=_achar_duracao(t), faltando=tuple(faltando))
