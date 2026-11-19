import pytest

from churrasco_facil.catalogo_carnes import (CORTES, VEGETARIANO, Corte, cortes_de_carne,
                                             obter_corte, pesos_validos)
from churrasco_facil.produtos import ACOUGUE


def test_obter_corte_desconhecido_levanta_keyerror():
    with pytest.raises(KeyError):
        obter_corte("zebra")


def test_cortes_de_carne_excluem_os_vegetarianos():
    assert all(c.categoria != VEGETARIANO for c in cortes_de_carne())


def test_pesos_validos_descarta_ids_desconhecidos_e_pesos_nao_positivos():
    pesos = {"picanha": 3, "zebra": 5, "alcatra": 0, "maminha": -1}
    assert pesos_validos(pesos) == {"picanha": 3}


def test_corte_com_preco_continua_um_corte_com_os_mesmos_dados():
    picanha = CORTES["picanha"]
    barata = picanha.com_preco({"picanha": 1})
    assert isinstance(barata, Corte)
    assert (barata.nome, barata.peca_g, barata.preco) == (picanha.nome, picanha.peca_g, 1)


def test_todo_corte_diz_quanto_pesa_a_peca_que_se_compra():
    with pytest.raises(ValueError):
        Corte(id="x", nome="X", secao="Açougue", unidade="g", preco=1, por_quantidade=1000,
              peca_g=0)


def test_vazio_e_uma_carne_vendida_em_peca_inteira():
    vazio = obter_corte("vazio")
    assert (vazio.nome, vazio.embalagem, vazio.peca_g) == ("Vazio", "peça", 2000)
    assert vazio in cortes_de_carne()


@pytest.mark.parametrize("corte", CORTES.values(), ids=list(CORTES))
def test_todo_corte_tem_dica_de_escolha_e_de_preparo(corte):
    assert corte.combina_com and corte.como_escolher        # aba Carnes
    assert corte.ponto and corte.preparo                    # aba Horários


@pytest.mark.parametrize("corte", CORTES.values(), ids=list(CORTES))
def test_so_o_que_vem_do_acougue_diz_como_pedir_ao_acougueiro(corte):
    assert bool(corte.como_pedir) == (corte.secao == ACOUGUE)
