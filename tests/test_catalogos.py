from churrasco_facil.catalogo_carnes import (CORTES, MISTURA_VEGETARIANA, MISTURAS,
                                             ORDEM_MISTURAS, VEGETARIANO, cortes_de_carne,
                                             cortes_para_iniciante, obter_corte, pesos_validos,
                                             resumo_para_prompt)
from churrasco_facil.catalogo_itens import ITENS, obter_item
from churrasco_facil.produtos import SECOES, ItemPlano

import pytest


def test_toda_mistura_soma_100_e_usa_cortes_que_existem():
    for nome, pesos in MISTURAS.items():
        assert sum(pesos.values()) == 100, nome
        assert set(pesos) <= set(CORTES), nome
    assert set(MISTURA_VEGETARIANA) <= set(CORTES)
    assert set(ORDEM_MISTURAS) == set(MISTURAS)


def test_substitutos_existem_e_sao_mais_baratos_ou_iguais_na_categoria():
    for corte in CORTES.values():
        assert set(corte.substitutos) <= set(CORTES), corte.id
        assert corte.id not in corte.substitutos


def test_misturas_ficam_mais_baratas_da_premium_para_a_economica():
    def preco_medio(nome):
        pesos = MISTURAS[nome]
        return sum(CORTES[i].preco * p for i, p in pesos.items()) / sum(pesos.values())
    assert preco_medio("premium") > preco_medio("tradicional") > preco_medio("economica")


def test_secoes_dos_produtos_estao_na_lista_de_secoes():
    for produto in list(CORTES.values()) + list(ITENS.values()):
        assert produto.secao in SECOES, produto.id


def test_ids_unicos_entre_cortes_e_itens():
    assert not set(CORTES) & set(ITENS)


def test_obter_corte_e_item_desconhecidos():
    with pytest.raises(KeyError):
        obter_corte("zebra")
    with pytest.raises(KeyError):
        obter_item("zebra")


def test_filtros_do_catalogo():
    assert all(c.categoria != VEGETARIANO for c in cortes_de_carne())
    assert all(c.dificuldade <= 2 for c in cortes_para_iniciante())
    assert "costela_bovina" not in {c.id for c in cortes_para_iniciante()}
    assert pesos_validos({"picanha": 3, "zebra": 5, "alcatra": 0, "maminha": -1}) == {"picanha": 3}


def test_resumo_para_prompt_lista_todos_os_cortes_de_carne_e_nenhum_vegetariano():
    texto = resumo_para_prompt()
    for corte in cortes_de_carne():
        assert corte.id in texto
    assert "queijo_coalho" not in texto


def test_com_preco_troca_so_o_que_o_usuario_configurou():
    picanha = CORTES["picanha"]
    assert picanha.com_preco({"picanha": 1}).preco == 1
    assert picanha.com_preco({"maminha": 1}) is picanha
    assert picanha.com_preco(None) is picanha
    assert picanha.com_preco({"picanha": 1}).nome == "Picanha"
    assert obter_item("pao_alho").com_preco({"pao_alho": 999}).preco == 999


def test_item_plano_calcula_custo_pela_quantidade():
    item = ItemPlano(CORTES["picanha"], 250)
    assert item.custo == 2250
    assert ItemPlano(obter_item("pao_alho"), 3).custo == 1200
