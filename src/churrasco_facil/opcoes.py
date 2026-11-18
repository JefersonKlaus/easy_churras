"""Opções de churrasco para o usuário escolher: do mais caprichado ao mais simples.

Cada opção é uma das misturas do catálogo. O custo é calculado para o grupo, com os preços
do usuário, e inclui tudo (carne, bebida, acompanhamentos e carvão).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Collection, Mapping, Optional

from .calculadora import Convidados, Parametros
from .catalogo_carnes import CORTES, MISTURA_VEGETARIANA, MISTURAS, Corte
from .catalogo_itens import ITENS
from .orcamento import ResultadoOrcamento, custo_por_pessoa, planejar_compras
from .produtos import SECOES, SECOES_LEMBRETE, Produto


@dataclass(frozen=True)
class Opcao:
    id: str          # chave em MISTURAS
    titulo: str
    descricao: str

    @property
    def pesos(self) -> dict[str, int]:
        return dict(MISTURAS[self.id])

    @property
    def cortes(self) -> list[Corte]:
        """Os cortes da opção, do que tem mais peso para o que tem menos."""
        return [CORTES[i] for i in sorted(self.pesos, key=lambda i: -self.pesos[i])]


OPCOES: tuple[Opcao, ...] = (
    Opcao("premium", "Caprichado", "Mais picanha e cortes nobres."),
    Opcao("tradicional", "Tradicional", "Um pouco de tudo: boi, linguiça e frango."),
    Opcao("economica", "Simples", "Mais linguiça, frango e porco. Gasta menos."),
)


@dataclass(frozen=True)
class OpcaoCalculada:
    """Uma opção com as compras e o custo para um grupo."""

    opcao: Opcao
    compras: ResultadoOrcamento
    pessoas: int

    @property
    def custo_total(self) -> int:
        return self.compras.custo_total

    @property
    def custo_por_pessoa(self) -> int:
        return custo_por_pessoa(self.compras.custo_total, self.pessoas)


def cortes_das_opcoes() -> list[Corte]:
    """Todos os cortes usados em alguma opção, sem repetir (os preços que importam)."""
    ids = dict.fromkeys(c.id for o in OPCOES for c in o.cortes)
    return [CORTES[i] for i in ids]


def grupos_de_precos() -> list[tuple[str, list[Produto]]]:
    """Tudo cujo preço pode entrar na conta, em grupos: carnes, vegetariano e os outros
    itens por seção do mercado. As seções de lembrete ficam de fora: não entram na conta."""
    grupos = [("Carnes", list(cortes_das_opcoes())),
              ("Vegetariano", [CORTES[i] for i in MISTURA_VEGETARIANA])]
    for secao in SECOES:
        itens = [p for p in ITENS.values() if p.secao == secao]
        if itens and secao not in SECOES_LEMBRETE:
            grupos.append((secao, itens))
    return grupos


def calcular_opcoes(conv: Convidados, par: Optional[Parametros] = None,
                    precos: Optional[Mapping[str, int]] = None,
                    secoes_fora: Collection[str] = ()) -> list[OpcaoCalculada]:
    """O custo de cada opção para o grupo, na ordem de OPCOES."""
    return [OpcaoCalculada(o, planejar_compras(conv, None, par, precos, o.pesos, secoes_fora),
                           conv.pessoas)
            for o in OPCOES]
