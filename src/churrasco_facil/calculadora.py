"""Quantidades: quanto de cada coisa comprar para um grupo.

Tudo aqui é conta feita pelo código. A IA nunca decide quantidades.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, fields, replace
from typing import Any, Collection, Mapping, Optional

from .catalogo_carnes import CORTES, MISTURA_VEGETARIANA, obter_corte
from .catalogo_itens import obter_item
from .produtos import SECOES_LEMBRETE, ItemPlano

MAX_PESSOAS = 200


@dataclass(frozen=True)
class Convidados:
    """Quem vem ao churrasco."""

    adultos: int
    criancas: int = 0
    vegetarianos: int = 0       # fazem parte dos adultos
    bebem_alcool: int = 0       # fazem parte dos adultos
    duracao_horas: float = 4.0

    def __post_init__(self) -> None:
        if self.adultos < 0 or self.criancas < 0:
            raise ValueError("o número de pessoas não pode ser negativo")
        if self.pessoas < 1:
            raise ValueError("precisa vir pelo menos uma pessoa")
        if self.pessoas > MAX_PESSOAS:
            raise ValueError(f"o máximo é {MAX_PESSOAS} pessoas")
        if not 0 <= self.vegetarianos <= self.adultos:
            raise ValueError("vegetarianos precisam estar entre os adultos")
        if not 0 <= self.bebem_alcool <= self.adultos:
            raise ValueError("quem bebe álcool precisa estar entre os adultos")
        if not 1 <= self.duracao_horas <= 12:
            raise ValueError("a duração deve ficar entre 1 e 12 horas")

    @property
    def pessoas(self) -> int:
        return self.adultos + self.criancas

    @property
    def comem_carne(self) -> int:
        return self.adultos - self.vegetarianos


@dataclass(frozen=True)
class Parametros:
    """Tabela de quantidades por pessoa. O usuário pode editar tudo nas configurações."""

    carne_adulto_g: int = 400
    carne_crianca_g: int = 200
    vegetariano_g: int = 350
    alcool_ml_por_bebedor: int = 1500
    refri_ml_por_pessoa_sem_alcool: int = 800
    agua_ml_por_pessoa: int = 500
    gelo_g_por_pessoa: int = 400
    pao_alho_por_pessoa: float = 1.0
    farofa_g_por_pessoa: int = 40
    arroz_g_por_pessoa: int = 70
    vinagrete_g_por_pessoa: int = 80
    salada_g_por_pessoa: int = 80
    carvao_kg_por_kg_de_carne: float = 1.0
    copos_por_pessoa: int = 3
    guardanapos_por_pessoa: int = 4
    pratos_por_pessoa: int = 2

    def fator_duracao(self, horas: float) -> float:
        """Quanto mais longo o churrasco, mais se come e se bebe."""
        if horas <= 3:
            return 1.0
        if horas <= 5:
            return 1.15
        return 1.3

    @classmethod
    def de_dicionario(cls, dados: Optional[Mapping[str, Any]]) -> "Parametros":
        """Cria a tabela a partir de um dicionário salvo, ignorando o que não for válido."""
        padrao = cls()
        if not dados:
            return padrao
        valores = {}
        for campo in fields(cls):
            if campo.name in dados:
                novo = dados[campo.name]
                antigo = getattr(padrao, campo.name)
                ok = isinstance(novo, (int, float)) and not isinstance(novo, bool) and novo >= 0
                if ok:
                    valores[campo.name] = type(antigo)(novo)
        return replace(padrao, **valores)


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


def distribuir(total_g: int, pesos: Mapping[str, int], multiplo: int = 50) -> dict[str, int]:
    """Reparte `total_g` entre os itens conforme o peso de cada um (maior resto primeiro).

    O resultado soma exatamente `total_g` quando ele é múltiplo de `multiplo`.
    """
    positivos = {i: p for i, p in pesos.items() if p > 0}
    if not positivos or total_g <= 0:
        return {}
    soma = sum(positivos.values())
    blocos = total_g // multiplo
    base = {i: blocos * p // soma for i, p in positivos.items()}
    restos = sorted(positivos, key=lambda i: (-(blocos * positivos[i] % soma), i))
    sobra = blocos - sum(base.values())
    for i in restos[:sobra]:
        base[i] += 1
    return {i: q * multiplo for i, q in base.items() if q > 0}


def itens_de_carne(conv: Convidados, pesos: Mapping[str, int], par: Parametros,
                   precos: Optional[Mapping[str, int]] = None) -> list[ItemPlano]:
    itens = []
    for id, gramas in distribuir(gramas_de_carne(conv, par), pesos).items():
        corte = obter_corte(id).com_preco(precos)
        itens.append(ItemPlano(corte, gramas))
    return itens


def itens_vegetarianos(conv: Convidados, par: Parametros,
                       precos: Optional[Mapping[str, int]] = None) -> list[ItemPlano]:
    itens = []
    for id, gramas in distribuir(gramas_vegetarianas(conv, par), MISTURA_VEGETARIANA).items():
        itens.append(ItemPlano(obter_corte(id).com_preco(precos), gramas,
                               "para quem não come carne"))
    return itens


def _item(id: str, quantidade: int, obs: str, precos: Optional[Mapping[str, int]]
          ) -> Optional[ItemPlano]:
    if quantidade <= 0:
        return None
    return ItemPlano(obter_item(id).com_preco(precos), quantidade, obs)


def itens_acompanhamentos(conv: Convidados, par: Parametros,
                          precos: Optional[Mapping[str, int]] = None) -> list[ItemPlano]:
    n = conv.pessoas
    vinagrete = arredondar_para_cima(n * par.vinagrete_g_por_pessoa, 50)
    candidatos = [
        _item("pao_alho", teto_divisao(n * par.pao_alho_por_pessoa, 1), "", precos),
        _item("farinha_mandioca", teto_divisao(n * par.farofa_g_por_pessoa, 500),
              "para a farofa", precos),
        _item("arroz", teto_divisao(n * par.arroz_g_por_pessoa, 1000), "", precos),
        _item("tomate", arredondar_para_cima(vinagrete * 0.5, 50), "vinagrete", precos),
        _item("cebola", arredondar_para_cima(vinagrete * 0.25, 50), "vinagrete", precos),
        _item("pimentao", arredondar_para_cima(vinagrete * 0.25, 50), "vinagrete", precos),
        _item("vinagre_azeite", 1, "tempero do vinagrete", precos),
        _item("salada_folhas", arredondar_para_cima(n * par.salada_g_por_pessoa, 100),
              "", precos),
    ]
    return [i for i in candidatos if i is not None]


def itens_bebidas(conv: Convidados, par: Parametros,
                  precos: Optional[Mapping[str, int]] = None) -> list[ItemPlano]:
    fator = par.fator_duracao(conv.duracao_horas)
    n = conv.pessoas
    sem_alcool = n - conv.bebem_alcool
    candidatos = [
        _item("cerveja_lata", teto_divisao(conv.bebem_alcool * par.alcool_ml_por_bebedor
                                           * fator, 350), "", precos),
        _item("refrigerante_2l", teto_divisao(sem_alcool * par.refri_ml_por_pessoa_sem_alcool
                                              * fator, 2000), "", precos),
        _item("agua_1_5l", teto_divisao(n * par.agua_ml_por_pessoa * fator, 1500), "", precos),
        _item("gelo_5kg", teto_divisao(n * par.gelo_g_por_pessoa * fator, 5000),
              "para as bebidas", precos),
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
        _item("papel_aluminio", 1, "para embrulhar e proteger", precos),
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
                 secoes_fora: Collection[str] = ()) -> list[ItemPlano]:
    """Os itens que entram na conta. A grelha vai sempre; dos outros itens, ficam de fora
    os das `secoes_fora` (escolha da pessoa) e os que são só lembrete (SECOES_LEMBRETE)."""
    par = par or Parametros()
    pesos = {i: p for i, p in pesos_carne.items() if i in CORTES}
    carnes = itens_de_carne(conv, pesos, par, precos)
    vegetarianos = itens_vegetarianos(conv, par, precos)
    grelha_g = sum(i.quantidade for i in carnes + vegetarianos)
    fora = set(secoes_fora) | set(SECOES_LEMBRETE)
    return carnes + vegetarianos + [i for i in _fora_da_grelha(conv, grelha_g, par, precos)
                                    if i.produto.secao not in fora]


def itens_para_lembrar(conv: Convidados, par: Optional[Parametros] = None) -> list[ItemPlano]:
    """Mercearia e descartáveis: vão para o "não esqueça", sem entrar na conta."""
    par = par or Parametros()
    return [i for i in _fora_da_grelha(conv, 0, par, None)
            if i.produto.secao in SECOES_LEMBRETE]
