"""Validação do que o Groq devolve. Nada que venha da IA entra no app sem passar por aqui."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Optional

from .calculadora import MAX_PESSOAS
from .catalogo_carnes import CORTES, VEGETARIANO


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
    orcamento_centavos: Optional[int] = None
    observacoes: str = ""
    faltando: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class Sugestao:
    id: str
    motivo: str


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
    reais = _numero(dados, "orcamento_reais")
    orcamento = int(round(reais * 100)) if reais is not None and 0 < reais <= 1_000_000 else None
    faltando = dados.get("faltando")
    faltando_ok = tuple(str(f)[:40] for f in faltando[:6]) if isinstance(faltando, list) else ()
    observacoes = dados.get("observacoes")
    return PedidoInterpretado(
        adultos=_inteiro(dados, "adultos"),
        criancas=_inteiro(dados, "criancas"),
        vegetarianos=_inteiro(dados, "vegetarianos"),
        bebem_alcool=_inteiro(dados, "bebem_alcool"),
        duracao_horas=horas if horas is not None and 1 <= horas <= 12 else None,
        orcamento_centavos=orcamento,
        observacoes=observacoes.strip()[:300] if isinstance(observacoes, str) else "",
        faltando=faltando_ok,
    )


def interpretar_sugestoes(texto: str, maximo: int = 6) -> list[Sugestao]:
    """Lê as sugestões de cortes. Descarta ids que não existem, repetidos e vegetarianos."""
    dados = extrair_json(texto)
    lista = dados.get("cortes") if isinstance(dados, dict) else None
    if not isinstance(lista, list):
        raise ErroEsquema("faltou a lista 'cortes'")
    vistos: set[str] = set()
    sugestoes: list[Sugestao] = []
    for entrada in lista:
        if not isinstance(entrada, dict):
            continue
        id = entrada.get("id")
        if not isinstance(id, str) or id not in CORTES or id in vistos:
            continue
        if CORTES[id].categoria == VEGETARIANO:
            continue
        vistos.add(id)
        motivo = entrada.get("motivo")
        sugestoes.append(Sugestao(id, motivo.strip()[:200] if isinstance(motivo, str) else ""))
        if len(sugestoes) >= maximo:
            break
    if not sugestoes:
        raise ErroEsquema("nenhum corte válido na resposta")
    return sugestoes


def limpar_texto_livre(texto: str, maximo: int = 800) -> str:
    """Texto da IA para mostrar na tela: tira cercas de código e limita o tamanho."""
    limpo = re.sub(r"```.*?```", "", texto or "", flags=re.S).strip()
    return limpo[:maximo]
