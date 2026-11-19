"""As compras: os itens do plano e quanto custam."""
import pytest

from churrasco_facil.catalogo_carnes import MISTURAS
from churrasco_facil.compras import (custo_por_pessoa, custo_total, custos_por_tipo,
                                     planejar_compras)


def ids_das_carnes(compras):
    return [i.produto.id for i in compras.carnes]


def test_sem_mistura_usa_a_tradicional(convidados):
    assert planejar_compras(convidados).pesos == MISTURAS["tradicional"]


def test_cortes_preferidos_viram_a_mistura(convidados):
    compras = planejar_compras(convidados, pesos_preferidos={"alcatra": 2, "bisteca_suina": 1})
    assert set(compras.pesos) == {"alcatra", "bisteca_suina"}
    assert set(ids_das_carnes(compras)) == {"alcatra", "bisteca_suina"}


def test_ids_inventados_sao_ignorados_e_cai_na_tradicional(convidados):
    assert planejar_compras(convidados, pesos_preferidos={"zebra": 5}).pesos == \
        MISTURAS["tradicional"]


def test_pecas_escolhidas_sao_compradas_exatamente(convidados):
    compras = planejar_compras(convidados, pesos_preferidos=MISTURAS["premium"],
                               pecas_escolhidas={"picanha": 3, "coracao_frango": 1})
    assert {i.produto.id: i.quantidade for i in compras.carnes} == \
        {"picanha": 3 * 1200, "coracao_frango": 500}


def test_custo_total_e_a_soma_dos_itens(convidados):
    compras = planejar_compras(convidados)
    assert compras.custo_total == custo_total(compras.itens)


def test_custos_por_tipo_somam_o_total(convidados):
    compras = planejar_compras(convidados)
    assert sum(v for _, v in custos_por_tipo(compras.itens)) == compras.custo_total


@pytest.mark.parametrize("total, pessoas, esperado", [(1001, 10, 101), (1000, 10, 100)])
def test_custo_por_pessoa_arredonda_para_cima(total, pessoas, esperado):
    assert custo_por_pessoa(total, pessoas) == esperado


def test_custo_por_pessoa_sem_pessoas_nao_divide_por_zero():
    assert custo_por_pessoa(5, 0) == 5
