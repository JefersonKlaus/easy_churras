"""Peças inteiras: repartir a carne em peças e ajustar quando a pessoa troca as carnes."""
import pytest

from churrasco_facil.catalogo_carnes import CORTES, MISTURAS
from churrasco_facil.pecas import ajustar_pecas, distribuir_em_pecas

TRADICIONAL = MISTURAS["tradicional"]


PECAS = {i: c.peca_g for i, c in CORTES.items()}


MAIOR_PECA = max(PECAS.values())


def test_pecas_seguem_a_proporcao():
    assert distribuir_em_pecas(6000, {"a": 2, "b": 1}, {"a": 1000, "b": 1000}) == {"a": 4, "b": 2}


def test_pecas_ignoram_pesos_zerados():
    assert distribuir_em_pecas(2000, {"a": 1, "b": 0}, {"a": 1000, "b": 1000}) == {"a": 2}


@pytest.mark.parametrize("total, pesos", [(0, {"a": 1}), (1000, {})])
def test_pecas_sem_nada_para_repartir(total, pesos):
    assert distribuir_em_pecas(total, pesos, {"a": 1000}) == {}


@pytest.mark.parametrize("total", [350, 1600, 2850, 4600, 20700])
def test_pecas_chegam_ao_total_sem_passar_uma_peca(total):
    # pode ficar até 5% abaixo (folga) e nunca passa mais que uma peça do total
    pecas = distribuir_em_pecas(total, TRADICIONAL, PECAS)
    comprado = sum(n * PECAS[i] for i, n in pecas.items())
    assert total * 0.95 <= comprado < total + MAIOR_PECA


def test_grupo_pequeno_leva_primeiro_os_cortes_mais_importantes():
    # 1,6 kg não dá para uma peça de cada um dos 5 cortes da mistura tradicional
    assert distribuir_em_pecas(1600, TRADICIONAL, PECAS) == {"picanha": 1, "linguica_toscana": 1}


def test_o_fim_fica_com_quem_passa_menos_do_total():
    # faltam 500 g: dois bifes de contrafilé (800 g) passam menos que uma peça de 1 kg
    assert distribuir_em_pecas(500, MISTURAS["premium"], PECAS) == {"contrafile": 2}


DOIS = {"a": 1000, "b": 1000}


def test_carne_marcada_entra_com_uma_peca_sem_mexer_no_resto():
    assert ajustar_pecas({"a": 3}, ["a", "b"], 3000, DOIS) == {"a": 3, "b": 1}


def test_carne_desmarcada_sai_e_as_outras_nao_mudam():
    # faltar carne é problema da tela avisar, não de mexer escondido nas outras
    assert ajustar_pecas({"a": 2, "b": 2}, ["a"], 4000, DOIS) == {"a": 2}


def test_carne_marcada_quando_falta_cobre_a_falta():
    # trocar uma carne por outra: desmarca a (sobra b com 1 kg), marca c para 4 kg
    assert ajustar_pecas({"b": 1}, ["b", "c"], 4000, DOIS | {"c": 1000}) == {"b": 1, "c": 3}


def test_ordem_e_a_da_lista():
    assert list(ajustar_pecas({"a": 1, "b": 1}, ["b", "a"], 2000, DOIS)) == ["b", "a"]


def test_falta_pequena_nao_compra_peca_a_mais():
    # 4150 g com peças de 1 kg: 4 peças (4 kg) ficam dentro da folga de 5%
    assert distribuir_em_pecas(4150, {"a": 1}, {"a": 1000}) == {"a": 4}
