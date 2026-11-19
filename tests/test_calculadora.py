"""Quantidades: quanto comprar de cada item para o grupo."""
import pytest

from churrasco_facil.calculadora import (arredondar_para_cima, gramas_de_carne,
                                         gramas_vegetarianas, itens_bebidas,
                                         itens_carvao_e_extras, itens_descartaveis,
                                         itens_para_lembrar, montar_itens, teto_divisao)
from churrasco_facil.catalogo_carnes import CORTES, MISTURAS, VEGETARIANO, Corte
from churrasco_facil.convidados import Convidados
from churrasco_facil.parametros import Parametros

TRADICIONAL = MISTURAS["tradicional"]


PECAS = {i: c.peca_g for i, c in CORTES.items()}


MAIOR_PECA = max(PECAS.values())


def por_id(itens):
    return {i.produto.id: i for i in itens}


def gramas_de_carne_nos_itens(itens):
    return sum(i.quantidade for i in itens
               if i.produto.id in CORTES and CORTES[i.produto.id].categoria != VEGETARIANO)


@pytest.mark.parametrize("a, b, esperado", [(7, 2, 4), (6, 2, 3), (0.1, 1, 1)])
def test_teto_divisao(a, b, esperado):
    assert teto_divisao(a, b) == esperado


@pytest.mark.parametrize("valor, esperado", [(4601, 4650), (4600, 4600)])
def test_arredondar_para_cima(valor, esperado):
    assert arredondar_para_cima(valor, 50) == esperado


@pytest.mark.parametrize("horas, gramas", [(3, 4000), (4, 4600), (6, 5200)])
def test_gramas_de_carne_aumentam_com_a_duracao(horas, gramas):
    assert gramas_de_carne(Convidados(adultos=10, duracao_horas=horas), Parametros()) == gramas


def test_criancas_comem_a_porcao_de_crianca():
    conv = Convidados(adultos=2, criancas=2, duracao_horas=3)
    assert gramas_de_carne(conv, Parametros()) == 2 * 400 + 2 * 200


def test_vegetarianos_ficam_fora_da_conta_de_carne():
    conv = Convidados(adultos=2, vegetarianos=1, duracao_horas=3)
    assert gramas_de_carne(conv, Parametros()) == 400


def test_gramas_vegetarianas_sao_por_vegetariano():
    conv = Convidados(adultos=2, vegetarianos=1, duracao_horas=3)
    assert gramas_vegetarianas(conv, Parametros()) == 350


def test_so_vegetarianos_nao_precisa_de_carne():
    assert gramas_de_carne(Convidados(adultos=2, vegetarianos=2), Parametros()) == 0


@pytest.mark.parametrize("id, quantidade", [
    ("cerveja_lata", 9),        # 2 x 1500 ml / 350 ml, para cima
    ("refrigerante_2l", 1),     # 2 pessoas x 800 ml
    ("agua_1_5l", 2),           # 4 x 500 ml
    ("gelo_5kg", 1),
])
def test_bebidas_por_pessoa(id, quantidade):
    conv = Convidados(adultos=4, bebem_alcool=2, duracao_horas=3)
    assert por_id(itens_bebidas(conv, Parametros()))[id].quantidade == quantidade


@pytest.mark.parametrize("id, indicado", [
    ("cerveja_lata", "Indicado: 1,5 L por pessoa que bebe"),
    ("refrigerante_2l", "Indicado: 0,8 L por pessoa que não bebe álcool"),
    ("agua_1_5l", "Indicado: 0,5 L por pessoa"), ("gelo_5kg", "Indicado: 0,4 kg por pessoa"),
])
def test_cada_bebida_diz_quanto_e_indicado_por_pessoa(id, indicado):
    conv = Convidados(adultos=4, bebem_alcool=2, duracao_horas=3)
    assert por_id(itens_bebidas(conv, Parametros()))[id].observacao == indicado


def test_festa_longa_indica_mais_bebida_por_pessoa():
    conv = Convidados(adultos=4, bebem_alcool=2, duracao_horas=6)       # fator 1,3
    assert por_id(itens_bebidas(conv, Parametros()))["agua_1_5l"].observacao == \
        "Indicado: 0,7 L por pessoa"


def test_ninguem_bebe_alcool_nao_compra_cerveja():
    conv = Convidados(adultos=3, bebem_alcool=0)
    assert "cerveja_lata" not in por_id(itens_bebidas(conv, Parametros()))


@pytest.mark.parametrize("gramas_na_grelha, sacos", [(4000, 2), (500, 1)])
def test_carvao_acompanha_a_quantidade_de_carne(gramas_na_grelha, sacos):
    itens = itens_carvao_e_extras(Convidados(adultos=10), gramas_na_grelha, Parametros())
    assert por_id(itens)["carvao_3kg"].quantidade == sacos


def test_montar_itens_compra_de_tudo_para_um_grupo_comum(convidados):
    itens = por_id(montar_itens(convidados, TRADICIONAL))
    assert {"picanha", "linguica_toscana", "cerveja_lata", "refrigerante_2l", "carvao_3kg",
            "acendedor"} <= set(itens)
    assert any(CORTES[i].categoria == VEGETARIANO for i in itens if i in CORTES)


def test_para_lembrar_vem_pao_de_alho_mercearia_e_descartaveis(convidados):
    assert [i.produto.id for i in itens_para_lembrar(convidados)] == [
        "pao_alho", "farinha_mandioca", "sal_grosso", "copos", "guardanapos", "pratos"]


def test_para_lembrar_nao_tem_nada_da_conta(convidados):
    lembrar = {i.produto.id for i in itens_para_lembrar(convidados)}
    assert not lembrar & set(por_id(montar_itens(convidados, TRADICIONAL)))


@pytest.mark.parametrize("id, quantidade", [("copos", 1), ("guardanapos", 2), ("pratos", 3)])
def test_descartaveis_para_lembrar(id, quantidade):
    conv = Convidados(adultos=10, criancas=3)      # 13 pessoas: 39 copos, 52 guardanapos...
    assert por_id(itens_descartaveis(conv))[id].quantidade == quantidade


def test_carne_comprada_cobre_a_carne_calculada(convidados):
    comprada = gramas_de_carne_nos_itens(montar_itens(convidados, TRADICIONAL))
    precisa = gramas_de_carne(convidados, Parametros())
    assert precisa * 0.95 <= comprada < precisa + MAIOR_PECA


def test_o_que_vai_para_a_grelha_e_comprado_em_pecas_inteiras(convidados):
    grelha = [i for i in montar_itens(convidados, TRADICIONAL) if isinstance(i.produto, Corte)]
    assert grelha and all(i.quantidade % i.produto.peca_g == 0 for i in grelha)


def test_preco_do_usuario_muda_o_custo_do_corte(convidados):
    padrao = por_id(montar_itens(convidados, TRADICIONAL))
    barato = por_id(montar_itens(convidados, TRADICIONAL, precos={"picanha": 1000}))
    assert barato["picanha"].custo < padrao["picanha"].custo


def test_ids_desconhecidos_sao_ignorados(convidados):
    itens = por_id(montar_itens(convidados, {"zebra": 10, "picanha": 10}))
    assert "zebra" not in itens and "picanha" in itens
