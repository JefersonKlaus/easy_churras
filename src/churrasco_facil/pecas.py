"""Peças inteiras: carne se compra em peça, pacote ou bandeja, não em gramas.

`distribuir_em_pecas` reparte o total de carne em peças, seguindo a mistura da opção;
`ajustar_pecas` muda as peças quando a pessoa marca ou desmarca uma carne.
"""
from __future__ import annotations

from typing import Mapping, Sequence

# As peças podem ficar até 5% abaixo do total pedido: as quantidades por pessoa já são
# generosas, e comprar uma peça inteira a mais para cobrir 150 g seria desperdício.
FOLGA_PERCENTUAL = 5


class _Partes:
    """A parte que cabe a cada corte no total, pela importância dele na mistura.

    A parte de um corte é total_g * peso / soma dos pesos. Para a conta ficar só com números
    inteiros, tudo o que é comparado com ela fica multiplicado pela soma dos pesos.
    """

    def __init__(self, total_g: int, pesos: Mapping[str, int], peca_g: Mapping[str, int]) -> None:
        self.total_g, self.peca_g = total_g, peca_g
        self.pesos = {i: p for i, p in pesos.items() if p > 0}
        self.soma = sum(self.pesos.values())
        self.parte = {i: total_g * p for i, p in self.pesos.items()}
        self.ordem = sorted(self.pesos, key=lambda i: (-self.pesos[i], i))   # desempate fixo
        self.folga = total_g * FOLGA_PERCENTUAL // 100

    def abaixo_da_parte(self, pecas: Mapping[str, int], i: str) -> int:
        """Positivo: falta carne deste corte para chegar à parte dele. Negativo: passou."""
        return self.parte[i] - pecas.get(i, 0) * self.peca_g[i] * self.soma

    def comprado(self, pecas: Mapping[str, int]) -> int:
        return sum(n * self.peca_g[i] for i, n in pecas.items())

    def completar(self, pecas: Mapping[str, int]) -> dict[str, int]:
        """Põe peças até chegar ao total (menos a folga). Cada peça vai para o corte que está
        mais longe da sua parte; quando ela já passaria do que falta, o fim fica com o corte
        que completa o total passando menos (mesmo que precise de duas peças pequenas)."""
        pecas = dict(pecas)
        falta = self.total_g - self.comprado(pecas)
        while falta > self.folga:
            escolhido = max(self.ordem, key=lambda i: self.abaixo_da_parte(pecas, i))
            if self.peca_g[escolhido] >= falta:

                def passa_do_total(i: str) -> int:
                    return -(-falta // self.peca_g[i]) * self.peca_g[i] - falta

                escolhido = min(self.ordem, key=lambda i: (passa_do_total(i),
                                                           -self.abaixo_da_parte(pecas, i)))
            pecas[escolhido] = pecas.get(escolhido, 0) + 1
            falta -= self.peca_g[escolhido]
        return pecas


def distribuir_em_pecas(total_g: int, pesos: Mapping[str, int],
                        peca_g: Mapping[str, int]) -> dict[str, int]:
    """Quantas peças inteiras de cada corte comprar para chegar a `total_g` (podendo ficar
    até FOLGA_PERCENTUAL abaixo), seguindo a importância (`pesos`) de cada corte. `peca_g`
    diz quanto pesa a peça de cada um.

    Cada corte leva as peças inteiras que cabem na parte dele; o resto é completado peça a
    peça (veja `_Partes.completar`). Com poucas peças, os cortes mais importantes da mistura
    vêm primeiro: um grupo pequeno não leva uma peça de cada corte e sobra pouca carne.
    Devolve só os cortes que levam pelo menos uma peça.
    """
    partes = _Partes(total_g, pesos, peca_g)
    if not partes.pesos or total_g <= 0:
        return {}
    inicial = {i: partes.parte[i] // (peca_g[i] * partes.soma) for i in partes.ordem}
    return {i: n for i, n in partes.completar(inicial).items() if n > 0}


def ajustar_pecas(atuais: Mapping[str, int], marcados: Sequence[str], total_g: int,
                  peca_g: Mapping[str, int]) -> dict[str, int]:
    """As peças depois que a pessoa marca ou desmarca carnes. Nada muda escondido:

    - carne desmarcada sai, e as outras ficam como estavam (se faltar carne, a tela avisa);
    - carne marcada entra com uma peça ou, se estiver faltando carne, com as peças que cobrem
      a falta (assim dá para trocar uma carne por outra: desmarca uma, marca a outra).

    `atuais` são as peças de antes; a ordem de `marcados` é a ordem da lista.
    """
    minimo = total_g - total_g * FOLGA_PERCENTUAL // 100
    pecas = {i: atuais[i] for i in marcados if atuais.get(i)}
    for i in marcados:
        if i not in pecas:
            falta = minimo - sum(n * peca_g[j] for j, n in pecas.items())
            pecas[i] = max(1, -(-falta // peca_g[i]))
    return {i: pecas[i] for i in dict.fromkeys(marcados)}
