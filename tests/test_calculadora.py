import pytest

from churrasco_facil.calculadora import (Convidados, Parametros, arredondar_para_cima,
                                         distribuir, gramas_de_carne, gramas_vegetarianas,
                                         itens_bebidas, itens_carvao_e_extras, montar_itens,
                                         teto_divisao)
from churrasco_facil.catalogo_carnes import MISTURAS


def por_id(itens):
    return {i.produto.id: i for i in itens}


def test_validacoes_de_convidados():
    for erro in (dict(adultos=0), dict(adultos=-1), dict(adultos=2, criancas=-1),
                 dict(adultos=2, vegetarianos=3), dict(adultos=2, bebem_alcool=3),
                 dict(adultos=2, duracao_horas=0.5), dict(adultos=2, duracao_horas=13),
                 dict(adultos=150, criancas=51)):
        with pytest.raises(ValueError):
            Convidados(**erro)
    assert Convidados(adultos=0, criancas=2).pessoas == 2   # só crianças é permitido
    assert Convidados(adultos=5, vegetarianos=2).comem_carne == 3


def test_helpers_de_arredondamento():
    assert teto_divisao(7, 2) == 4 and teto_divisao(6, 2) == 3 and teto_divisao(0.1, 1) == 1
    assert arredondar_para_cima(4601, 50) == 4650 and arredondar_para_cima(4600, 50) == 4600


def test_gramas_de_carne_por_duracao():
    assert gramas_de_carne(Convidados(adultos=10, duracao_horas=3), Parametros()) == 4000
    assert gramas_de_carne(Convidados(adultos=10, duracao_horas=4), Parametros()) == 4600
    assert gramas_de_carne(Convidados(adultos=10, duracao_horas=6), Parametros()) == 5200


def test_criancas_e_vegetarianos_entram_na_conta():
    conv = Convidados(adultos=2, criancas=2, duracao_horas=3)
    assert gramas_de_carne(conv, Parametros()) == 1200
    conv = Convidados(adultos=2, vegetarianos=1, duracao_horas=3)
    assert gramas_de_carne(conv, Parametros()) == 400
    assert gramas_vegetarianas(conv, Parametros()) == 350
    assert gramas_vegetarianas(Convidados(adultos=3), Parametros()) == 0


def test_so_vegetarianos_nao_gera_carne():
    conv = Convidados(adultos=2, vegetarianos=2)
    assert gramas_de_carne(conv, Parametros()) == 0
    itens = montar_itens(conv, MISTURAS["tradicional"])
    assert all(i.produto.categoria == "vegetariano" for i in itens
               if hasattr(i.produto, "categoria"))


def test_distribuir_reparte_exatamente_o_total():
    assert distribuir(1000, {"a": 1, "b": 1, "c": 1}) == {"a": 350, "b": 350, "c": 300}
    assert distribuir(0, {"a": 1}) == {}
    assert distribuir(1000, {}) == {}
    assert distribuir(1000, {"a": 1, "b": 0}) == {"a": 1000}
    for total in (50, 350, 2850, 4600):
        resultado = distribuir(total, MISTURAS["tradicional"])
        assert sum(resultado.values()) == total
        assert all(g % 50 == 0 for g in resultado.values())


def test_distribuir_respeita_a_proporcao():
    resultado = distribuir(2000, {"picanha": 3, "alcatra": 1})
    assert resultado == {"picanha": 1500, "alcatra": 500}


def test_bebidas_por_pessoa():
    conv = Convidados(adultos=4, bebem_alcool=2, duracao_horas=3)
    itens = por_id(itens_bebidas(conv, Parametros()))
    assert itens["cerveja_lata"].quantidade == 9      # 2 x 1500 ml / 350 ml, para cima
    assert itens["refrigerante_2l"].quantidade == 1   # 2 pessoas x 800 ml
    assert itens["agua_1_5l"].quantidade == 2         # 4 x 500 ml
    assert itens["gelo_5kg"].quantidade == 1


def test_ninguem_bebe_alcool_nao_compra_cerveja():
    conv = Convidados(adultos=3, bebem_alcool=0)
    assert "cerveja_lata" not in por_id(itens_bebidas(conv, Parametros()))


def test_carvao_acompanha_a_quantidade_de_carne():
    conv = Convidados(adultos=10, duracao_horas=3)
    assert por_id(itens_carvao_e_extras(conv, 4000, Parametros()))["carvao_3kg"].quantidade == 2
    assert por_id(itens_carvao_e_extras(conv, 500, Parametros()))["carvao_3kg"].quantidade == 1


def test_itens_completos_para_um_grupo(convidados):
    itens = por_id(montar_itens(convidados, MISTURAS["tradicional"]))
    for id in ("picanha", "linguica_toscana", "queijo_coalho", "pao_alho", "arroz",
               "cerveja_lata", "carvao_3kg", "sal_grosso", "copos"):
        assert id in itens
    assert itens["picanha"].produto.unidade == "g"
    assert all(i.quantidade > 0 for i in itens.values())
    gramas_carne = sum(i.quantidade for i in itens.values()
                       if getattr(i.produto, "categoria", "") not in ("", "vegetariano"))
    assert gramas_carne == gramas_de_carne(convidados, Parametros())


def test_precos_do_usuario_mudam_o_custo(convidados):
    padrao = por_id(montar_itens(convidados, MISTURAS["tradicional"]))
    barato = por_id(montar_itens(convidados, MISTURAS["tradicional"],
                                 precos={"picanha": 1000}))
    assert barato["picanha"].custo < padrao["picanha"].custo
    assert barato["alcatra"].custo == padrao["alcatra"].custo


def test_ids_desconhecidos_sao_ignorados(convidados):
    itens = por_id(montar_itens(convidados, {"zebra": 10, "picanha": 10}))
    assert "zebra" not in itens and "picanha" in itens


def test_parametros_de_dicionario_ignora_lixo():
    par = Parametros.de_dicionario({"carne_adulto_g": 500, "carne_crianca_g": "x",
                                    "desconhecido": 1, "arroz_g_por_pessoa": -5,
                                    "pao_alho_por_pessoa": 2})
    assert par.carne_adulto_g == 500
    assert par.carne_crianca_g == Parametros().carne_crianca_g
    assert par.arroz_g_por_pessoa == Parametros().arroz_g_por_pessoa
    assert par.pao_alho_por_pessoa == 2.0
    assert Parametros.de_dicionario(None) == Parametros()
