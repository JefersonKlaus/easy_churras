"""Do pedido ao plano: compras, horários e avisos, e se a carne está certa."""
import pytest
from dados import SERVIR

from churrasco_facil.catalogo_carnes import MISTURAS, VEGETARIANO
from churrasco_facil.convidados import Convidados
from churrasco_facil.planejador import FALTA, SOBRA, Pedido, montar_plano, trocar_carnes


def ids_dos_cortes(plano):
    return [c.id for c in plano.cortes]


def test_mesmo_pedido_gera_sempre_o_mesmo_plano(pedido):
    a, b = montar_plano(pedido), montar_plano(pedido)
    assert (a.compras, a.cronograma, a.avisos) == (b.compras, b.cronograma, b.avisos)


def test_gramas_de_carne_do_plano_nao_contam_a_grelha_vegetariana():
    plano = montar_plano(Pedido(Convidados(adultos=2, vegetarianos=2), SERVIR))
    assert plano.compras.itens and plano.gramas_de_carne == 0


def test_horarios_e_avisos_seguem_o_que_foi_comprado():
    # 4 adultos levam só picanha e linguiça da mistura tradicional (peças inteiras)
    plano = montar_plano(Pedido(Convidados(adultos=4, duracao_horas=3), SERVIR,
                                pesos_preferidos=MISTURAS["tradicional"]))
    assert ids_dos_cortes(plano) == ["picanha", "linguica_toscana"]
    assert not any("Maminha" in e.titulo for e in plano.cronograma)
    assert "frango" not in {a.id for a in plano.avisos}


@pytest.fixture
def plano_de_4():
    """4 adultos, tradicional: a melhor compra é só picanha e linguiça."""
    return montar_plano(Pedido(Convidados(adultos=4, duracao_horas=3), SERVIR,
                               pesos_preferidos=MISTURAS["tradicional"]))


def test_trocar_sem_mudar_nada_da_o_mesmo_plano(plano_de_4):
    mesmo = montar_plano(trocar_carnes(plano_de_4, ids_dos_cortes(plano_de_4)))
    assert mesmo.compras.itens == plano_de_4.compras.itens


def test_carne_marcada_e_comprada_mesmo_fora_da_opcao(plano_de_4):
    plano = montar_plano(trocar_carnes(plano_de_4, ["picanha", "linguica_toscana",
                                                    "coracao_frango"]))
    assert ids_dos_cortes(plano) == ["picanha", "linguica_toscana", "coracao_frango"]


def test_melhor_escolha_da_opcao_esta_na_medida(plano_de_4):
    assert plano_de_4.situacao_da_carne() == ""


def test_desmarcar_carne_deixa_faltar(plano_de_4):
    menos = montar_plano(trocar_carnes(plano_de_4, ["picanha"]))
    assert menos.situacao_da_carne() == FALTA


def test_marcar_carne_demais_faz_sobrar(plano_de_4):
    mais = montar_plano(trocar_carnes(plano_de_4, [*ids_dos_cortes(plano_de_4), "coracao_frango",
                                                   "alcatra"]))
    assert mais.situacao_da_carne() == SOBRA


def test_passar_um_pouco_por_causa_das_pecas_nao_e_sobra():
    # 1 adulto: 500 g indicados, 2 bifes (800 g) é o mínimo de peças inteiras
    plano = montar_plano(Pedido(Convidados(adultos=1), SERVIR,
                                pesos_preferidos=MISTURAS["premium"]))
    assert plano.gramas_de_carne > plano.carne_indicada_g and plano.situacao_da_carne() == ""


def test_cortes_preferidos_viram_os_cortes_do_plano():
    plano = montar_plano(Pedido(Convidados(adultos=4), SERVIR, pesos_preferidos={"alcatra": 1}))
    assert ids_dos_cortes(plano) == ["alcatra"]


def test_sem_vegetarianos_nao_ha_opcao_vegetariana():
    plano = montar_plano(Pedido(Convidados(adultos=4), SERVIR))
    assert "queijo_coalho" not in ids_dos_cortes(plano)


def test_com_vegetarianos_ha_opcao_vegetariana():
    plano = montar_plano(Pedido(Convidados(adultos=4, vegetarianos=1), SERVIR))
    assert any(c.categoria == VEGETARIANO for c in plano.cortes)
