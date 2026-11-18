import pytest

from churrasco_facil.catalogo_carnes import (CORTES, MISTURA_VEGETARIANA, MISTURAS,
                                             ORDEM_MISTURAS, VEGETARIANO, Corte, cortes_de_carne,
                                             cortes_para_iniciante, obter_corte, pesos_validos,
                                             resumo_para_prompt)
from churrasco_facil.produtos import SECOES


@pytest.mark.parametrize("nome", MISTURAS)
def test_mistura_soma_100(nome):
    assert sum(MISTURAS[nome].values()) == 100


@pytest.mark.parametrize("pesos", [*MISTURAS.values(), MISTURA_VEGETARIANA])
def test_mistura_so_usa_cortes_do_catalogo(pesos):
    assert set(pesos) <= set(CORTES)


def test_ordem_das_misturas_tem_todas_as_misturas():
    assert set(ORDEM_MISTURAS) == set(MISTURAS)


def test_misturas_ficam_mais_baratas_da_premium_para_a_economica():
    def preco_medio(nome):
        pesos = MISTURAS[nome]
        return sum(CORTES[i].preco * p for i, p in pesos.items()) / sum(pesos.values())
    assert preco_medio("premium") > preco_medio("tradicional") > preco_medio("economica")


@pytest.mark.parametrize("corte", CORTES.values(), ids=list(CORTES))
def test_substitutos_sao_outros_cortes_do_catalogo(corte):
    assert set(corte.substitutos) <= set(CORTES) - {corte.id}


@pytest.mark.parametrize("corte", CORTES.values(), ids=list(CORTES))
def test_corte_fica_numa_secao_conhecida(corte):
    assert corte.secao in SECOES


def test_obter_corte_desconhecido_levanta_keyerror():
    with pytest.raises(KeyError):
        obter_corte("zebra")


def test_cortes_de_carne_excluem_os_vegetarianos():
    assert all(c.categoria != VEGETARIANO for c in cortes_de_carne())


def test_cortes_para_iniciante_sao_os_faceis():
    assert all(c.dificuldade <= 2 for c in cortes_para_iniciante())


def test_cortes_para_iniciante_excluem_os_dificeis():
    assert "costela_bovina" not in {c.id for c in cortes_para_iniciante()}


def test_pesos_validos_descarta_ids_desconhecidos_e_pesos_nao_positivos():
    assert pesos_validos({"picanha": 3, "zebra": 5, "alcatra": 0, "maminha": -1}) == {"picanha": 3}


def test_resumo_para_prompt_lista_todos_os_cortes_de_carne():
    texto = resumo_para_prompt()
    assert all(c.id in texto for c in cortes_de_carne())


def test_resumo_para_prompt_nao_lista_vegetarianos():
    assert "queijo_coalho" not in resumo_para_prompt()


def test_corte_com_preco_continua_um_corte_com_os_mesmos_dados():
    picanha = CORTES["picanha"]
    barata = picanha.com_preco({"picanha": 1})
    assert isinstance(barata, Corte)
    assert (barata.nome, barata.dificuldade, barata.preco) == (picanha.nome, picanha.dificuldade, 1)
