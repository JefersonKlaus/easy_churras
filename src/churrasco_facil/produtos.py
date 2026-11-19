"""Estruturas comuns a tudo o que se compra: produto, corte de carne e item do plano."""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Mapping, Optional

from .dinheiro import custo_proporcional

# Ordem em que as seções aparecem na lista de compras (a ordem do corredor do mercado).
# Hortifruti só aparece com vegetarianos: é onde se compram os legumes e cogumelos da grelha.
ACOUGUE = "Açougue"
SECOES = (ACOUGUE, "Hortifruti", "Padaria", "Frios e laticínios", "Mercearia",
          "Bebidas", "Carvão e acessórios", "Descartáveis")
# Seções que são só um lembrete ("não esqueça"): aparecem na lista, mas ficam fora da conta.
SECOES_LEMBRETE = ("Padaria", "Mercearia", "Descartáveis")


@dataclass(frozen=True)
class Produto:
    """Algo que se compra. O preço vale para `por_quantidade` da unidade base.

    Exemplo: picanha a R$ 90,00 o kg -> preco=9000, por_quantidade=1000, unidade="g".
    Um pacote de pão de alho a R$ 4,00 a unidade -> preco=400, por_quantidade=1, unidade="un".
    """

    id: str
    nome: str
    secao: str
    unidade: str            # "g", "ml" ou "un"
    preco: int              # centavos
    por_quantidade: int

    def com_preco(self, precos: Optional[Mapping[str, int]]) -> "Produto":
        """Devolve o produto com o preço trocado pelo que o usuário configurou."""
        if precos and self.id in precos:
            return replace(self, preco=precos[self.id])
        return self


@dataclass(frozen=True)
class ItemPlano:
    """Uma linha do plano: um produto, quanto comprar e uma observação curta."""

    produto: Produto
    quantidade: int
    observacao: str = ""

    @property
    def custo(self) -> int:
        return custo_proporcional(self.produto.preco, self.produto.por_quantidade,
                                  self.quantidade)
