import pytest

from churrasco_facil.calculadora import Convidados
from churrasco_facil.orcamento import (ajustar_ao_orcamento, custo_por_pessoa, custo_total,
                                       maiores_gastos, planejar_compras)

QUATRO_ADULTOS = Convidados(adultos=4, duracao_horas=3)


# ---------------------------------------------------------------- escolha da mistura

@pytest.mark.parametrize("limite", [None, 0])
def test_sem_limite_usa_a_mistura_tradicional(convidados, limite):
    assert planejar_compras(convidados, limite).mistura == "tradicional"


@pytest.mark.parametrize("limite", [None, 0])
def test_sem_limite_nunca_estoura(convidados, limite):
    resultado = planejar_compras(convidados, limite)
    assert resultado.orcamento is None
    assert (resultado.estourou, resultado.excedente) == (False, 0)


def test_orcamento_alto_escolhe_a_mistura_premium(convidados):
    resultado = planejar_compras(convidados, 10 ** 9)
    assert resultado.mistura == "premium" and not resultado.estourou


def test_orcamento_um_pouco_menor_que_o_premium_escolhe_outra_que_cabe(convidados):
    limite = planejar_compras(convidados, 10 ** 9).custo_total - 1
    resultado = planejar_compras(convidados, limite)
    assert resultado.mistura != "premium"
    assert resultado.custo_total <= limite


def test_precos_do_usuario_mudam_a_escolha(convidados):
    barato = {i: 100 for i in ("picanha", "fraldinha", "contrafile", "linguica_toscana",
                               "coxa_sobrecoxa", "costelinha_suina")}
    limite = planejar_compras(convidados, None).custo_total   # custo da tradicional
    assert planejar_compras(convidados, limite, precos=barato).mistura == "premium"


# ---------------------------------------------------------------- cortes preferidos

def test_cortes_preferidos_sao_usados_quando_cabem(convidados):
    resultado = planejar_compras(convidados, None,
                                 pesos_preferidos={"alcatra": 2, "bisteca_suina": 1})
    assert resultado.mistura == "personalizada"
    assert set(resultado.pesos) == {"alcatra", "bisteca_suina"}


def test_ids_inventados_sao_ignorados_e_cai_na_mistura_padrao(convidados):
    resultado = planejar_compras(convidados, None, pesos_preferidos={"zebra": 5})
    assert resultado.mistura == "tradicional"


# ---------------------------------------------------------------- ajuste ao orçamento

def test_orcamento_impossivel_marca_quanto_estourou(convidados):
    resultado = planejar_compras(convidados, 1000)
    assert resultado.estourou
    assert resultado.excedente == resultado.custo_total - 1000


def test_custo_total_e_a_soma_dos_itens(convidados):
    resultado = planejar_compras(convidados, 1000)
    assert resultado.custo_total == custo_total(resultado.itens)


def test_troca_cortes_caros_pelos_substitutos_ate_acabarem_as_opcoes():
    resultado = planejar_compras(QUATRO_ADULTOS, 1, pesos_preferidos={"picanha": 1})
    assert resultado.trocas == [("picanha", "maminha"), ("maminha", "alcatra")]
    assert set(resultado.pesos) == {"alcatra"}


def test_troca_para_assim_que_o_plano_cabe():
    caro = planejar_compras(QUATRO_ADULTOS, None, pesos_preferidos={"picanha": 1})
    meio = planejar_compras(QUATRO_ADULTOS, caro.custo_total - 1,
                            pesos_preferidos={"picanha": 1})
    assert meio.trocas == [("picanha", "maminha")] and not meio.estourou


def test_ajustar_nao_mexe_em_plano_que_ja_cabe(convidados):
    assert ajustar_ao_orcamento(convidados, {"picanha": 1}, 10 ** 9) == ({"picanha": 1}, [])


def test_secoes_fora_barateiam_a_conta(convidados):
    com_tudo = planejar_compras(convidados, None).custo_total
    sem_hortifruti = planejar_compras(convidados, None, secoes_fora={"Hortifruti"}).custo_total
    assert sem_hortifruti < com_tudo


# ---------------------------------------------------------------- números para a tela

def test_maiores_gastos_vem_do_mais_caro_para_o_mais_barato(convidados):
    itens = planejar_compras(convidados, None).itens
    top = maiores_gastos(itens, 3)
    assert [i.custo for i in top] == sorted((i.custo for i in itens), reverse=True)[:3]


@pytest.mark.parametrize("total, pessoas, esperado", [(1001, 10, 101), (1000, 10, 100)])
def test_custo_por_pessoa_arredonda_para_cima(total, pessoas, esperado):
    assert custo_por_pessoa(total, pessoas) == esperado


def test_custo_por_pessoa_sem_pessoas_nao_divide_por_zero():
    assert custo_por_pessoa(5, 0) == 5
