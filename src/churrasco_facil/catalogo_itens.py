"""Itens que não são carne: acompanhamentos, bebidas, carvão e descartáveis.

Preços são estimativas de referência (em centavos) e o usuário pode trocá-los.
"""
from __future__ import annotations

from .produtos import Produto


def _p(id: str, nome: str, secao: str, unidade: str, preco: int, por: int = 1) -> Produto:
    return Produto(id=id, nome=nome, secao=secao, unidade=unidade, preco=preco,
                   por_quantidade=por)


ITENS: dict[str, Produto] = {p.id: p for p in (
    # Padaria e mercearia
    _p("pao_alho", "Pão de alho", "Padaria", "un", 400),
    _p("farinha_mandioca", "Farinha de mandioca (pacote 500 g)", "Mercearia", "un", 700),
    _p("arroz", "Arroz (pacote 1 kg)", "Mercearia", "un", 650),
    _p("vinagre_azeite", "Vinagre e azeite (para o vinagrete)", "Mercearia", "un", 1500),
    _p("sal_grosso", "Sal grosso (pacote 1 kg)", "Mercearia", "un", 450),
    # Hortifruti (preço por kg)
    _p("tomate", "Tomate", "Hortifruti", "g", 800, 1000),
    _p("cebola", "Cebola", "Hortifruti", "g", 600, 1000),
    _p("pimentao", "Pimentão", "Hortifruti", "g", 1200, 1000),
    _p("salada_folhas", "Alface e folhas para salada", "Hortifruti", "g", 1500, 1000),
    # Bebidas
    _p("cerveja_lata", "Cerveja (lata 350 ml)", "Bebidas", "un", 550),
    _p("refrigerante_2l", "Refrigerante (garrafa 2 L)", "Bebidas", "un", 900),
    _p("agua_1_5l", "Água (garrafa 1,5 L)", "Bebidas", "un", 400),
    _p("gelo_5kg", "Gelo (saco 5 kg)", "Bebidas", "un", 1200),
    # Carvão e acessórios
    _p("carvao_3kg", "Carvão (saco 3 kg)", "Carvão e acessórios", "un", 2400),
    _p("acendedor", "Acendedor sólido (caixa)", "Carvão e acessórios", "un", 600),
    _p("papel_aluminio", "Papel-alumínio (rolo)", "Carvão e acessórios", "un", 1100),
    # Descartáveis
    _p("copos", "Copos descartáveis (pacote 50)", "Descartáveis", "un", 900),
    _p("guardanapos", "Guardanapos (pacote 50)", "Descartáveis", "un", 500),
    _p("pratos", "Pratos descartáveis (pacote 10)", "Descartáveis", "un", 600),
)}


def obter_item(id: str) -> Produto:
    try:
        return ITENS[id]
    except KeyError:
        raise KeyError(f"item desconhecido: {id!r}") from None
