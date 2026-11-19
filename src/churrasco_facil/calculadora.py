"""Quantidades: quanto de cada coisa comprar para um grupo, item por item.

Tudo aqui é conta feita pelo código. A IA nunca decide quantidades. O que vai para a grelha
é comprado em peças inteiras (veja `pecas`).
"""
from __future__ import annotations

import math
from typing import Iterable, Mapping, Optional

from .catalogo_carnes import CORTES, MISTURA_VEGETARIANA, obter_corte
from .catalogo_itens import obter_item
from .convidados import Convidados
from .parametros import Parametros
from .pecas import distribuir_em_pecas
from .produtos import SECOES_LEMBRETE, ItemPlano


def teto_divisao(a: float, b: float) -> int:
    """Divisão que arredonda para cima (precisa comprar pacote inteiro)."""
    return math.ceil(round(a / b, 9))


def arredondar_para_cima(valor: float, multiplo: int) -> int:
    return teto_divisao(valor, multiplo) * multiplo


def gramas_de_carne(conv: Convidados, par: Parametros) -> int:
    """Total de carne crua (em gramas, múltiplo de 50) para quem come carne."""
    base = conv.comem_carne * par.carne_adulto_g + conv.criancas * par.carne_crianca_g
    return arredondar_para_cima(base * par.fator_duracao(conv.duracao_horas), 50) if base else 0


def gramas_vegetarianas(conv: Convidados, par: Parametros) -> int:
    base = conv.vegetarianos * par.vegetariano_g
    return arredondar_para_cima(base, 50) if base else 0


def _itens_da_grelha(pecas: Mapping[str, int], obs: str,
                     precos: Optional[Mapping[str, int]]) -> list[ItemPlano]:
    """Peças inteiras dos cortes. A quantidade do item é o peso das peças, em gramas."""
    itens = []
    for id, n in pecas.items():
        corte = obter_corte(id).com_preco(precos)
        itens.append(ItemPlano(corte, n * corte.peca_g, obs))
    return itens


def _pecas_dos_cortes(ids: Iterable[str]) -> dict[str, int]:
    return {i: obter_corte(i).peca_g for i in ids}


def itens_de_carne(conv: Convidados, pesos: Mapping[str, int], par: Parametros,
                   precos: Optional[Mapping[str, int]] = None) -> list[ItemPlano]:
    pecas = distribuir_em_pecas(gramas_de_carne(conv, par), pesos, _pecas_dos_cortes(pesos))
    return _itens_da_grelha(pecas, "", precos)


def itens_vegetarianos(conv: Convidados, par: Parametros,
                       precos: Optional[Mapping[str, int]] = None) -> list[ItemPlano]:
    pecas = distribuir_em_pecas(gramas_vegetarianas(conv, par), MISTURA_VEGETARIANA,
                                _pecas_dos_cortes(MISTURA_VEGETARIANA))
    return _itens_da_grelha(pecas, "para quem não come carne", precos)


def _item(id: str, quantidade: int, obs: str, precos: Optional[Mapping[str, int]]
          ) -> Optional[ItemPlano]:
    if quantidade <= 0:
        return None
    return ItemPlano(obter_item(id).com_preco(precos), quantidade, obs)


def itens_acompanhamentos(conv: Convidados, par: Parametros,
                          precos: Optional[Mapping[str, int]] = None) -> list[ItemPlano]:
    n = conv.pessoas
    candidatos = [
        _item("pao_alho", teto_divisao(n * par.pao_alho_por_pessoa, 1), "", precos),
        _item("farinha_mandioca", teto_divisao(n * par.farofa_g_por_pessoa, 500),
              "para a farofa", precos),
    ]
    return [i for i in candidatos if i is not None]


def _indicado(por_pessoa: float, unidade: str, quem: str) -> str:
    """Quanto cada um deve tomar, para a lista: 'Indicado: 1,7 L por pessoa que bebe'.
    `por_pessoa` vem em ml (ou g) e aparece em L (ou kg), com uma casa decimal."""
    return f"Indicado: {por_pessoa / 1000:.1f}".replace(".", ",") + f" {unidade} por {quem}"


def itens_bebidas(conv: Convidados, par: Parametros,
                  precos: Optional[Mapping[str, int]] = None) -> list[ItemPlano]:
    """Todas as bebidas seguem a mesma regra: uma quantidade por pessoa, que cresce com a
    duração da festa, arredondada para latas ou garrafas inteiras. Cada item diz quanto é
    indicado por pessoa."""
    fator = par.fator_duracao(conv.duracao_horas)
    n = conv.pessoas
    sem_alcool = n - conv.bebem_alcool
    cerveja = par.cerveja_ml_por_bebedor * fator
    refri = par.refri_ml_por_pessoa_sem_alcool * fator
    agua = par.agua_ml_por_pessoa * fator
    gelo = par.gelo_g_por_pessoa * fator
    candidatos = [
        _item("cerveja_lata", teto_divisao(conv.bebem_alcool * cerveja, 350),
              _indicado(cerveja, "L", "pessoa que bebe"), precos),
        _item("refrigerante_2l", teto_divisao(sem_alcool * refri, 2000),
              _indicado(refri, "L", "pessoa que não bebe álcool"), precos),
        _item("agua_1_5l", teto_divisao(n * agua, 1500), _indicado(agua, "L", "pessoa"), precos),
        _item("gelo_5kg", teto_divisao(n * gelo, 5000), _indicado(gelo, "kg", "pessoa"),
              precos),
    ]
    return [i for i in candidatos if i is not None]


def itens_carvao_e_extras(conv: Convidados, total_grelha_g: int, par: Parametros,
                          precos: Optional[Mapping[str, int]] = None) -> list[ItemPlano]:
    kg_carvao = max(1.0, total_grelha_g / 1000 * par.carvao_kg_por_kg_de_carne)
    candidatos = [
        _item("carvao_3kg", teto_divisao(kg_carvao, 3), "cerca de 1 kg por kg de carne",
              precos),
        _item("acendedor", 1, "nunca use álcool ou gasolina", precos),
        _item("sal_grosso", 1, "uns 10 g por kg de carne", precos),
    ]
    return [i for i in candidatos if i is not None]


def itens_descartaveis(conv: Convidados, par: Optional[Parametros] = None) -> list[ItemPlano]:
    """Copos, guardanapos e pratos. São só um lembrete: não entram na conta."""
    par = par or Parametros()
    n = conv.pessoas
    candidatos = [
        _item("copos", teto_divisao(n * par.copos_por_pessoa, 50), "", None),
        _item("guardanapos", teto_divisao(n * par.guardanapos_por_pessoa, 50), "", None),
        _item("pratos", teto_divisao(n * par.pratos_por_pessoa, 10), "", None),
    ]
    return [i for i in candidatos if i is not None]


def _fora_da_grelha(conv: Convidados, grelha_g: int, par: Parametros,
                    precos: Optional[Mapping[str, int]]) -> list[ItemPlano]:
    """Tudo o que não vai para a grelha: acompanhamentos, bebidas, carvão e descartáveis."""
    return (itens_acompanhamentos(conv, par, precos) + itens_bebidas(conv, par, precos)
            + itens_carvao_e_extras(conv, grelha_g, par, precos)
            + itens_descartaveis(conv, par))


def montar_itens(conv: Convidados, pesos_carne: Mapping[str, int],
                 par: Optional[Parametros] = None,
                 precos: Optional[Mapping[str, int]] = None,
                 pecas_escolhidas: Optional[Mapping[str, int]] = None) -> list[ItemPlano]:
    """Os itens que entram na conta: tudo, menos o que é só lembrete (SECOES_LEMBRETE).
    Com `pecas_escolhidas` (a pessoa trocou as carnes), a carne é exatamente essa; sem elas,
    as peças saem da mistura `pesos_carne`."""
    par = par or Parametros()
    if pecas_escolhidas:
        carnes = _itens_da_grelha({i: n for i, n in pecas_escolhidas.items()
                                   if i in CORTES and n > 0}, "", precos)
    else:
        carnes = itens_de_carne(conv, {i: p for i, p in pesos_carne.items() if i in CORTES},
                                par, precos)
    vegetarianos = itens_vegetarianos(conv, par, precos)
    grelha_g = sum(i.quantidade for i in carnes + vegetarianos)
    return carnes + vegetarianos + [i for i in _fora_da_grelha(conv, grelha_g, par, precos)
                                    if i.produto.secao not in SECOES_LEMBRETE]


def itens_para_lembrar(conv: Convidados, par: Optional[Parametros] = None) -> list[ItemPlano]:
    """Pão de alho, mercearia e descartáveis: vão para o "não esqueça", fora da conta."""
    par = par or Parametros()
    return [i for i in _fora_da_grelha(conv, 0, par, None)
            if i.produto.secao in SECOES_LEMBRETE]
