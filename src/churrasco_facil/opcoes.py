"""Opções de churrasco para o usuário escolher: do mais caprichado ao mais simples.

Cada opção é uma das misturas do catálogo. O custo é calculado para o grupo, com os preços
do usuário, e inclui carne, bebidas e carvão (o que é só lembrete fica fora).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional

from .catalogo_carnes import CORTES, MISTURAS, Corte
from .compras import Compras, custo_por_pessoa, planejar_compras
from .convidados import Convidados
from .parametros import Parametros


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
    compras: Compras
    pessoas: int

    @property
    def custo_total(self) -> int:
        return self.compras.custo_total

    @property
    def custo_por_pessoa(self) -> int:
        return custo_por_pessoa(self.compras.custo_total, self.pessoas)


def calcular_opcoes(conv: Convidados, par: Optional[Parametros] = None,
                    precos: Optional[Mapping[str, int]] = None) -> list[OpcaoCalculada]:
    """O custo de cada opção para o grupo, na ordem de OPCOES."""
    return [OpcaoCalculada(o, planejar_compras(conv, par, precos, o.pesos),
                           conv.pessoas)
            for o in OPCOES]
