from churrasco_facil.calculadora import Convidados
from churrasco_facil.orcamento import (ajustar_ao_orcamento, custo_por_pessoa, custo_total,
                                       maiores_gastos, planejar_compras)


def test_sem_limite_usa_a_mistura_tradicional(convidados):
    for limite in (None, 0):
        resultado = planejar_compras(convidados, limite)
        assert resultado.mistura == "tradicional" and not resultado.estourou
        assert resultado.excedente == 0 and resultado.orcamento is None


def test_orcamento_alto_escolhe_a_mistura_premium(convidados):
    resultado = planejar_compras(convidados, 10 ** 9)
    assert resultado.mistura == "premium" and not resultado.estourou


def test_orcamento_um_pouco_menor_que_o_premium_escolhe_outra(convidados):
    premium = planejar_compras(convidados, 10 ** 9)
    limite = premium.custo_total - 1
    resultado = planejar_compras(convidados, limite)
    assert resultado.mistura != "premium"
    assert resultado.custo_total <= limite and not resultado.estourou


def test_orcamento_impossivel_marca_que_estourou(convidados):
    resultado = planejar_compras(convidados, 1000)
    assert resultado.estourou
    assert resultado.excedente == resultado.custo_total - 1000
    assert resultado.custo_total == custo_total(resultado.itens)


def test_cortes_sugeridos_sao_usados_quando_cabem(convidados):
    resultado = planejar_compras(convidados, None, pesos_preferidos={"alcatra": 2, "bisteca_suina": 1})
    assert resultado.mistura == "personalizada"
    assert set(resultado.pesos) == {"alcatra", "bisteca_suina"}
    assert resultado.trocas == []


def test_ids_inventados_sao_ignorados_e_cai_na_mistura_padrao(convidados):
    resultado = planejar_compras(convidados, None, pesos_preferidos={"zebra": 5})
    assert resultado.mistura == "tradicional"


def test_troca_corte_caro_por_substituto_mais_barato():
    conv = Convidados(adultos=4, duracao_horas=3)
    resultado = planejar_compras(conv, 1, pesos_preferidos={"picanha": 1})
    assert resultado.trocas == [("picanha", "maminha"), ("maminha", "alcatra")]
    assert set(resultado.pesos) == {"alcatra"} and resultado.estourou


def test_troca_para_assim_que_o_plano_cabe():
    conv = Convidados(adultos=4, duracao_horas=3)
    caro = planejar_compras(conv, None, pesos_preferidos={"picanha": 1})
    meio = planejar_compras(conv, caro.custo_total - 1, pesos_preferidos={"picanha": 1})
    assert meio.trocas == [("picanha", "maminha")] and not meio.estourou


def test_ajustar_nao_mexe_em_plano_que_ja_cabe(convidados):
    pesos, trocas = ajustar_ao_orcamento(convidados, {"picanha": 1}, 10 ** 9)
    assert pesos == {"picanha": 1} and trocas == []


def test_precos_do_usuario_mudam_a_escolha(convidados):
    barato = {i: 100 for i in ("picanha", "fraldinha", "contrafile", "linguica_toscana",
                               "coxa_sobrecoxa", "costelinha_suina")}
    limite = planejar_compras(convidados, None).custo_total   # custo da tradicional
    assert planejar_compras(convidados, limite, precos=barato).mistura == "premium"


def test_maiores_gastos_e_custo_por_pessoa(convidados):
    itens = planejar_compras(convidados, None).itens
    top = maiores_gastos(itens, 3)
    assert len(top) == 3 and top[0].custo >= top[1].custo >= top[2].custo
    assert top[0].custo == max(i.custo for i in itens)
    assert custo_por_pessoa(1001, 10) == 101 and custo_por_pessoa(1000, 10) == 100
    assert custo_por_pessoa(5, 0) == 5
