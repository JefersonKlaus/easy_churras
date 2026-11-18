import pytest

from churrasco_facil.calculadora import (Convidados, Parametros, arredondar_para_cima,
                                         distribuir, gramas_de_carne, gramas_vegetarianas,
                                         itens_bebidas, itens_carvao_e_extras,
                                         itens_descartaveis, itens_para_lembrar, montar_itens,
                                         teto_divisao)
from churrasco_facil.catalogo_carnes import CORTES, MISTURAS, VEGETARIANO

TRADICIONAL = MISTURAS["tradicional"]


def por_id(itens):
    return {i.produto.id: i for i in itens}


def gramas_de_carne_nos_itens(itens):
    return sum(i.quantidade for i in itens
               if i.produto.id in CORTES and CORTES[i.produto.id].categoria != VEGETARIANO)


# ---------------------------------------------------------------- Convidados

@pytest.mark.parametrize("dados", [
    dict(adultos=0), dict(adultos=-1), dict(adultos=2, criancas=-1),
    dict(adultos=2, vegetarianos=3), dict(adultos=2, bebem_alcool=3),
    dict(adultos=2, duracao_horas=0.5), dict(adultos=2, duracao_horas=13),
    dict(adultos=150, criancas=51),
])
def test_convidados_invalidos_levantam_valueerror(dados):
    with pytest.raises(ValueError):
        Convidados(**dados)


def test_grupo_so_de_criancas_e_permitido():
    assert Convidados(adultos=0, criancas=2).pessoas == 2


def test_comem_carne_exclui_os_vegetarianos():
    assert Convidados(adultos=5, vegetarianos=2).comem_carne == 3


# ---------------------------------------------------------------- Parametros

def test_parametros_de_dicionario_aceita_valor_valido():
    assert Parametros.de_dicionario({"carne_adulto_g": 500}).carne_adulto_g == 500


@pytest.mark.parametrize("campo, valor", [
    ("carne_crianca_g", "x"), ("arroz_g_por_pessoa", -5), ("carne_adulto_g", True),
])
def test_parametros_de_dicionario_ignora_valor_invalido(campo, valor):
    assert Parametros.de_dicionario({campo: valor}) == Parametros()


def test_parametros_de_dicionario_ignora_campo_desconhecido():
    assert Parametros.de_dicionario({"desconhecido": 1}) == Parametros()


def test_parametros_de_dicionario_converte_para_o_tipo_do_campo():
    assert Parametros.de_dicionario({"pao_alho_por_pessoa": 2}).pao_alho_por_pessoa == 2.0


def test_parametros_de_dicionario_sem_dados_usa_o_padrao():
    assert Parametros.de_dicionario(None) == Parametros()


# ---------------------------------------------------------------- arredondamento

@pytest.mark.parametrize("a, b, esperado", [(7, 2, 4), (6, 2, 3), (0.1, 1, 1)])
def test_teto_divisao(a, b, esperado):
    assert teto_divisao(a, b) == esperado


@pytest.mark.parametrize("valor, esperado", [(4601, 4650), (4600, 4600)])
def test_arredondar_para_cima(valor, esperado):
    assert arredondar_para_cima(valor, 50) == esperado


# ---------------------------------------------------------------- gramas

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


def test_sem_vegetarianos_nao_ha_gramas_vegetarianas():
    assert gramas_vegetarianas(Convidados(adultos=3), Parametros()) == 0


def test_so_vegetarianos_nao_precisa_de_carne():
    assert gramas_de_carne(Convidados(adultos=2, vegetarianos=2), Parametros()) == 0


# ---------------------------------------------------------------- distribuir

def test_distribuir_da_o_resto_aos_maiores_restos():
    assert distribuir(1000, {"a": 1, "b": 1, "c": 1}) == {"a": 350, "b": 350, "c": 300}


def test_distribuir_respeita_a_proporcao():
    assert distribuir(2000, {"picanha": 3, "alcatra": 1}) == {"picanha": 1500, "alcatra": 500}


def test_distribuir_ignora_pesos_zerados():
    assert distribuir(1000, {"a": 1, "b": 0}) == {"a": 1000}


@pytest.mark.parametrize("total, pesos", [(0, {"a": 1}), (1000, {})])
def test_distribuir_sem_nada_para_repartir(total, pesos):
    assert distribuir(total, pesos) == {}


@pytest.mark.parametrize("total", [50, 350, 2850, 4600])
def test_distribuir_soma_exatamente_o_total(total):
    assert sum(distribuir(total, TRADICIONAL).values()) == total


@pytest.mark.parametrize("total", [50, 350, 2850, 4600])
def test_distribuir_usa_multiplos_de_50_gramas(total):
    assert all(g % 50 == 0 for g in distribuir(total, TRADICIONAL).values())


# ---------------------------------------------------------------- itens

@pytest.mark.parametrize("id, quantidade", [
    ("cerveja_lata", 9),        # 2 x 1500 ml / 350 ml, para cima
    ("refrigerante_2l", 1),     # 2 pessoas x 800 ml
    ("agua_1_5l", 2),           # 4 x 500 ml
    ("gelo_5kg", 1),
])
def test_bebidas_por_pessoa(id, quantidade):
    conv = Convidados(adultos=4, bebem_alcool=2, duracao_horas=3)
    assert por_id(itens_bebidas(conv, Parametros()))[id].quantidade == quantidade


def test_ninguem_bebe_alcool_nao_compra_cerveja():
    conv = Convidados(adultos=3, bebem_alcool=0)
    assert "cerveja_lata" not in por_id(itens_bebidas(conv, Parametros()))


@pytest.mark.parametrize("gramas_na_grelha, sacos", [(4000, 2), (500, 1)])
def test_carvao_acompanha_a_quantidade_de_carne(gramas_na_grelha, sacos):
    itens = itens_carvao_e_extras(Convidados(adultos=10), gramas_na_grelha, Parametros())
    assert por_id(itens)["carvao_3kg"].quantidade == sacos


@pytest.mark.parametrize("id", ["picanha", "linguica_toscana", "queijo_coalho", "pao_alho",
                                "tomate", "cerveja_lata", "carvao_3kg", "acendedor"])
def test_montar_itens_compra_de_tudo_para_um_grupo_comum(convidados, id):
    assert id in por_id(montar_itens(convidados, TRADICIONAL))


@pytest.mark.parametrize("id", ["farinha_mandioca", "arroz", "vinagre_azeite", "sal_grosso",
                                "copos", "guardanapos", "pratos"])
def test_mercearia_e_descartaveis_nao_entram_na_conta(convidados, id):
    assert id not in por_id(montar_itens(convidados, TRADICIONAL))


def test_para_lembrar_vem_mercearia_e_depois_descartaveis(convidados):
    assert [i.produto.id for i in itens_para_lembrar(convidados)] == [
        "farinha_mandioca", "arroz", "vinagre_azeite", "sal_grosso", "copos", "guardanapos",
        "pratos"]


def test_para_lembrar_nao_tem_nada_da_conta(convidados):
    lembrar = {i.produto.id for i in itens_para_lembrar(convidados)}
    assert not lembrar & set(por_id(montar_itens(convidados, TRADICIONAL)))


@pytest.mark.parametrize("id, quantidade", [("copos", 1), ("guardanapos", 2), ("pratos", 3)])
def test_descartaveis_para_lembrar(id, quantidade):
    conv = Convidados(adultos=10, criancas=3)      # 13 pessoas: 39 copos, 52 guardanapos...
    assert por_id(itens_descartaveis(conv))[id].quantidade == quantidade


def test_hortifruti_fora_tira_o_vinagrete_e_a_salada_da_conta(convidados):
    itens = por_id(montar_itens(convidados, TRADICIONAL, secoes_fora={"Hortifruti"}))
    assert not {"tomate", "cebola", "pimentao", "salada_folhas"} & set(itens)


def test_hortifruti_fora_nao_tira_a_grelha_vegetariana(convidados):
    # espetinho de legumes e cogumelo são da seção Hortifruti, mas vão para a grelha
    itens = por_id(montar_itens(convidados, TRADICIONAL, secoes_fora={"Hortifruti"}))
    assert {"espetinho_legumes", "cogumelo"} <= set(itens)


def test_secao_fora_nao_mexe_nas_outras(convidados):
    itens = por_id(montar_itens(convidados, TRADICIONAL, secoes_fora={"Hortifruti"}))
    assert {"pao_alho", "cerveja_lata", "carvao_3kg", "acendedor"} <= set(itens)


def test_montar_itens_so_tem_quantidades_positivas(convidados):
    assert all(i.quantidade > 0 for i in montar_itens(convidados, TRADICIONAL))


def test_carne_comprada_e_a_carne_calculada(convidados):
    itens = montar_itens(convidados, TRADICIONAL)
    assert gramas_de_carne_nos_itens(itens) == gramas_de_carne(convidados, Parametros())


def test_so_vegetarianos_nao_compra_carne():
    itens = montar_itens(Convidados(adultos=2, vegetarianos=2), TRADICIONAL)
    assert gramas_de_carne_nos_itens(itens) == 0


def test_preco_do_usuario_muda_o_custo_do_corte(convidados):
    padrao = por_id(montar_itens(convidados, TRADICIONAL))
    barato = por_id(montar_itens(convidados, TRADICIONAL, precos={"picanha": 1000}))
    assert barato["picanha"].custo < padrao["picanha"].custo


def test_preco_do_usuario_nao_muda_os_outros_cortes(convidados):
    padrao = por_id(montar_itens(convidados, TRADICIONAL))
    barato = por_id(montar_itens(convidados, TRADICIONAL, precos={"picanha": 1000}))
    assert barato["alcatra"].custo == padrao["alcatra"].custo


def test_ids_desconhecidos_sao_ignorados(convidados):
    itens = por_id(montar_itens(convidados, {"zebra": 10, "picanha": 10}))
    assert "zebra" not in itens and "picanha" in itens
