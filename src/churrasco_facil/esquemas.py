"""Validação do que o Groq devolve. Nada que venha da IA entra no app sem passar por aqui."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Optional

from .convidados import MAX_PESSOAS


class ErroEsquema(ValueError):
    """A resposta do Groq não tem o formato esperado."""


@dataclass(frozen=True)
class PedidoInterpretado:
    """O que o Groq entendeu de um pedido em texto livre."""

    adultos: Optional[int] = None
    criancas: Optional[int] = None
    vegetarianos: Optional[int] = None
    bebem_alcool: Optional[int] = None
    duracao_horas: Optional[float] = None
    faltando: tuple[str, ...] = field(default_factory=tuple)   # o que não deu para saber


def extrair_json(texto: str) -> Any:
    """Acha e lê o objeto JSON dentro da resposta, mesmo com texto ou cercas ```json em volta."""
    limpo = re.sub(r"```(?:json)?", "", texto or "").strip()
    inicio, fim = limpo.find("{"), limpo.rfind("}")
    if inicio < 0 or fim <= inicio:
        raise ErroEsquema("a resposta não contém um objeto JSON")
    try:
        return json.loads(limpo[inicio:fim + 1])
    except json.JSONDecodeError as erro:
        raise ErroEsquema(f"JSON inválido: {erro.msg}") from None


def _inteiro(dados: dict[str, Any], chave: str, maximo: int = MAX_PESSOAS) -> Optional[int]:
    valor = dados.get(chave)
    if valor is None or isinstance(valor, bool):
        return None
    if isinstance(valor, str):
        valor = valor.strip()
        if not valor.lstrip("-").isdigit():
            return None
    try:
        numero = int(float(valor))
    except (TypeError, ValueError):
        return None
    return numero if 0 <= numero <= maximo else None


def _numero(dados: dict[str, Any], chave: str) -> Optional[float]:
    valor = dados.get(chave)
    if valor is None or isinstance(valor, bool):
        return None
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def interpretar_pedido(texto: str) -> PedidoInterpretado:
    """Converte a resposta do Groq em um `PedidoInterpretado` com valores seguros."""
    dados = extrair_json(texto)
    if not isinstance(dados, dict):
        raise ErroEsquema("esperava um objeto JSON")
    horas = _numero(dados, "duracao_horas")
    faltando = dados.get("faltando")
    faltando_ok = tuple(str(f)[:40] for f in faltando[:6]) if isinstance(faltando, list) else ()
    return PedidoInterpretado(
        adultos=_inteiro(dados, "adultos"),
        criancas=_inteiro(dados, "criancas"),
        vegetarianos=_inteiro(dados, "vegetarianos"),
        bebem_alcool=_inteiro(dados, "bebem_alcool"),
        duracao_horas=horas if horas is not None and 1 <= horas <= 12 else None,
        faltando=faltando_ok,
    )
