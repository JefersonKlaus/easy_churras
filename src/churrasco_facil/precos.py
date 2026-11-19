"""Os preços que a pessoa confere e muda: quais aparecem, em que grupos, e como o que ela
digita vira preço salvo (em centavos, por id do produto)."""
from __future__ import annotations

from typing import Mapping

from .catalogo_carnes import CORTES, MISTURA_VEGETARIANA, Corte, cortes_de_carne
from .catalogo_itens import ITENS
from .dinheiro import reais_para_centavos
from .opcoes import OPCOES
from .produtos import SECOES, SECOES_LEMBRETE, Produto

PRECO_MAXIMO = 10_000_00   # R$ 10.000,00 por unidade base: acima disso é erro de digitação


def precos_validos(bruto: object) -> dict[str, int]:
    if not isinstance(bruto, dict):
        return {}
    validos = set(CORTES) | set(ITENS)
    return {k: v for k, v in bruto.items()
            if k in validos and isinstance(v, int) and not isinstance(v, bool)
            and 0 <= v <= PRECO_MAXIMO}


def juntar_precos(atuais: Mapping[str, int], digitados: Mapping[str, str]) -> dict[str, int]:
    """Junta aos preços salvos os que o usuário digitou (em reais), por id do produto.

    Preço igual ao do catálogo não é guardado. Levanta ValueError citando o produto.
    """
    novos = dict(atuais)
    for id, texto in digitados.items():
        produto = CORTES.get(id) or ITENS[id]
        try:
            centavos = reais_para_centavos(texto)
        except ValueError as erro:
            raise ValueError(f"{produto.nome}: {erro}") from None
        if centavos > PRECO_MAXIMO:
            raise ValueError(f"{produto.nome}: preço alto demais")
        if centavos == produto.preco:
            novos.pop(id, None)
        else:
            novos[id] = centavos
    return novos


def carnes_com_preco() -> list[Corte]:
    """Todas as carnes, porque a pessoa pode marcar qualquer uma: primeiro as das opções
    (da mais importante para a menos), depois as outras."""
    ids = dict.fromkeys([c.id for o in OPCOES for c in o.cortes]
                        + [c.id for c in cortes_de_carne()])
    return [CORTES[i] for i in ids]


def grupos_de_precos() -> list[tuple[str, list[Produto]]]:
    """Tudo cujo preço pode entrar na conta, em grupos: carnes, vegetariano e os outros
    itens por seção do mercado. As seções de lembrete ficam de fora: não entram na conta."""
    grupos = [("Carnes", carnes_com_preco()),
              ("Vegetariano", [CORTES[i] for i in MISTURA_VEGETARIANA])]
    for secao in SECOES:
        itens = [p for p in ITENS.values() if p.secao == secao]
        if itens and secao not in SECOES_LEMBRETE:
            grupos.append((secao, itens))
    return grupos
