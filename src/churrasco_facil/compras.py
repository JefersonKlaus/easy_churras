"""As compras do churrasco: os itens (carnes, bebidas, carvão) e quanto custam."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional

from .calculadora import montar_itens
from .catalogo_carnes import MISTURAS, VEGETARIANO, Corte, pesos_validos
from .convidados import Convidados
from .parametros import Parametros
from .produtos import ItemPlano


@dataclass(frozen=True)
class Compras:
    """O que comprar. `pesos` é a mistura de carnes de que as peças saíram."""

    pesos: dict[str, int]                # id do corte -> importância na mistura
    itens: list[ItemPlano]

    @property
    def custo_total(self) -> int:
        """Em centavos: carnes, bebidas e carvão (os lembretes ficam fora)."""
        return custo_total(self.itens)

    @property
    def carnes(self) -> list[ItemPlano]:
        """Os itens de carne comprados (sem a grelha vegetariana)."""
        return [i for i in self.itens
                if isinstance(i.produto, Corte) and i.produto.categoria != VEGETARIANO]

    @property
    def gramas_de_carne(self) -> int:
        """Quanto de carne as peças compradas somam."""
        return sum(i.quantidade for i in self.carnes)


def planejar_compras(conv: Convidados, par: Optional[Parametros] = None,
                     precos: Optional[Mapping[str, int]] = None,
                     pesos_preferidos: Optional[Mapping[str, int]] = None,
                     pecas_escolhidas: Optional[Mapping[str, int]] = None) -> Compras:
    """Monta as compras. A carne sai da mistura `pesos_preferidos` (a da opção escolhida; sem
    ela, a tradicional) ou, se a pessoa trocou as carnes, exatamente das `pecas_escolhidas`."""
    pesos = pesos_validos(pesos_preferidos or {}) or dict(MISTURAS["tradicional"])
    return Compras(pesos, montar_itens(conv, pesos, par, precos, pecas_escolhidas))


def custo_total(itens: list[ItemPlano]) -> int:
    return sum(i.custo for i in itens)


def custos_por_tipo(itens: list[ItemPlano]) -> list[tuple[str, int]]:
    """O total separado em carnes (com a grelha vegetariana, se houver), bebidas e o resto
    (carvão e acessórios), para deixar claro o que o total inclui."""
    grelha = [i for i in itens if isinstance(i.produto, Corte)]
    veg = any(i.produto.categoria == VEGETARIANO for i in grelha)
    partes = {("Carnes e grelha vegetariana" if veg else "Carnes"): custo_total(grelha)}
    for item in itens:
        if not isinstance(item.produto, Corte):
            partes[item.produto.secao] = partes.get(item.produto.secao, 0) + item.custo
    return [(nome, valor) for nome, valor in partes.items() if valor]


def custo_por_pessoa(total: int, pessoas: int) -> int:
    """Centavos por pessoa, arredondando para cima para a conta não ficar curta."""
    return -(-total // max(1, pessoas))
