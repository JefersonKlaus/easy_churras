"""Custo do churrasco e ajuste ao dinheiro disponível.

Se o plano não cabe no orçamento, o código troca os cortes mais caros por substitutos
mais baratos do catálogo (picanha -> maminha -> alcatra...) até caber ou acabarem as opções.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Collection, Mapping, Optional

from .calculadora import Convidados, Parametros, montar_itens
from .catalogo_carnes import CORTES, MISTURAS, ORDEM_MISTURAS, pesos_validos
from .produtos import ItemPlano


@dataclass(frozen=True)
class ResultadoOrcamento:
    """O plano de compras escolhido e como ele se compara ao orçamento."""

    mistura: str                         # nome da mistura ou "personalizada"
    pesos: dict[str, int]                # id do corte -> peso
    itens: list[ItemPlano]
    custo_total: int                     # centavos
    orcamento: Optional[int]             # centavos, None = sem limite
    estourou: bool
    excedente: int                       # centavos acima do orçamento (0 se coube)
    trocas: list[tuple[str, str]] = field(default_factory=list)  # (saiu, entrou)


def custo_total(itens: list[ItemPlano]) -> int:
    return sum(i.custo for i in itens)


def _custo_com_pesos(conv: Convidados, pesos: Mapping[str, int], par: Parametros,
                     precos: Optional[Mapping[str, int]], secoes_fora: Collection[str] = ()
                     ) -> tuple[list[ItemPlano], int]:
    itens = montar_itens(conv, pesos, par, precos, secoes_fora)
    return itens, custo_total(itens)


def _preco_kg(id: str, precos: Optional[Mapping[str, int]]) -> int:
    return CORTES[id].com_preco(precos).preco


def _proxima_troca(pesos: Mapping[str, int], precos: Optional[Mapping[str, int]]
                   ) -> Optional[tuple[str, str]]:
    """Acha o corte mais caro que tem um substituto mais barato fora da mistura."""
    for id in sorted(pesos, key=lambda i: -_preco_kg(i, precos)):
        for sub in CORTES[id].substitutos:
            if sub in CORTES and sub not in pesos \
                    and _preco_kg(sub, precos) < _preco_kg(id, precos):
                return id, sub
    return None


def _trocar(pesos: Mapping[str, int], saiu: str, entrou: str) -> dict[str, int]:
    novos = {i: p for i, p in pesos.items() if i != saiu}
    novos[entrou] = pesos[saiu]
    return novos


def ajustar_ao_orcamento(conv: Convidados, pesos: Mapping[str, int], orcamento: int,
                         par: Optional[Parametros] = None,
                         precos: Optional[Mapping[str, int]] = None,
                         secoes_fora: Collection[str] = ()
                         ) -> tuple[dict[str, int], list[tuple[str, str]]]:
    """Troca cortes caros por mais baratos até o plano caber. Devolve (pesos, trocas)."""
    par = par or Parametros()
    atuais = dict(pesos)
    trocas: list[tuple[str, str]] = []
    while True:
        _, custo = _custo_com_pesos(conv, atuais, par, precos, secoes_fora)
        if custo <= orcamento:
            break
        troca = _proxima_troca(atuais, precos)
        if troca is None:
            break
        atuais = _trocar(atuais, *troca)
        trocas.append(troca)
    return atuais, trocas


def planejar_compras(conv: Convidados, orcamento: Optional[int] = None,
                     par: Optional[Parametros] = None,
                     precos: Optional[Mapping[str, int]] = None,
                     pesos_preferidos: Optional[Mapping[str, int]] = None,
                     secoes_fora: Collection[str] = ()
                     ) -> ResultadoOrcamento:
    """Escolhe os cortes e monta os itens.

    - Com `pesos_preferidos` (por exemplo, sugeridos pelo Groq) parte deles.
    - Sem eles, usa a mistura mais rica que couber no orçamento.
    - Sem orçamento (None ou 0), usa a mistura tradicional.
    - Os itens das `secoes_fora` não entram na conta.
    """
    par = par or Parametros()
    limite = orcamento if orcamento else None
    pesos_ini = pesos_validos(pesos_preferidos or {})
    # Sem nenhum corte de carne válido (ex.: todos vegetarianos) ainda assim há mistura.
    if pesos_ini:
        nome, pesos = "personalizada", pesos_ini
    elif limite is None:
        nome, pesos = "tradicional", dict(MISTURAS["tradicional"])
    else:
        nome, pesos = ORDEM_MISTURAS[-1], dict(MISTURAS[ORDEM_MISTURAS[-1]])
        for candidata in ORDEM_MISTURAS:
            _, custo = _custo_com_pesos(conv, MISTURAS[candidata], par, precos, secoes_fora)
            if custo <= limite:
                nome, pesos = candidata, dict(MISTURAS[candidata])
                break
    trocas: list[tuple[str, str]] = []
    if limite is not None:
        pesos, trocas = ajustar_ao_orcamento(conv, pesos, limite, par, precos, secoes_fora)
    itens, total = _custo_com_pesos(conv, pesos, par, precos, secoes_fora)
    excedente = max(0, total - limite) if limite is not None else 0
    return ResultadoOrcamento(nome, pesos, itens, total, limite, excedente > 0, excedente,
                              trocas)


def custo_por_pessoa(total: int, pessoas: int) -> int:
    """Centavos por pessoa, arredondando para cima para a conta não ficar curta."""
    return -(-total // max(1, pessoas))


def maiores_gastos(itens: list[ItemPlano], quantidade: int = 3) -> list[ItemPlano]:
    """Os itens que mais pesam no custo (para sugerir onde economizar)."""
    return sorted(itens, key=lambda i: -i.custo)[:quantidade]
