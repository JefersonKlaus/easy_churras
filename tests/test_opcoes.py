import pytest

from churrasco_facil.calculadora import Convidados
from churrasco_facil.catalogo_carnes import MISTURAS
from churrasco_facil.catalogo_carnes import MISTURA_VEGETARIANA
from churrasco_facil.catalogo_itens import ITENS
from churrasco_facil.opcoes import OPCOES, calcular_opcoes, cortes_das_opcoes, grupos_de_precos
from churrasco_facil.orcamento import planejar_compras

GRUPO = Convidados(adultos=8, criancas=2, bebem_alcool=4)


@pytest.mark.parametrize("opcao", OPCOES, ids=lambda o: o.id)
def test_cada_opcao_e_uma_mistura_do_catalogo(opcao):
    assert opcao.pesos == MISTURAS[opcao.id]


def test_opcoes_vao_do_caprichado_ao_simples():
    assert [o.titulo for o in OPCOES] == ["Caprichado", "Tradicional", "Simples"]


def test_cortes_da_opcao_vem_do_mais_importante_ao_menos():
    tradicional = next(o for o in OPCOES if o.id == "tradicional")
    pesos = [tradicional.pesos[c.id] for c in tradicional.cortes]
    assert pesos == sorted(pesos, reverse=True)


def test_cortes_das_opcoes_juntam_todas_as_opcoes_sem_repetir():
    ids = [c.id for c in cortes_das_opcoes()]
    assert sorted(ids) == sorted({i for o in OPCOES for i in o.pesos})


def test_calcular_opcoes_devolve_uma_por_opcao_na_mesma_ordem():
    assert [c.opcao for c in calcular_opcoes(GRUPO)] == list(OPCOES)


def test_custo_da_opcao_e_o_da_lista_de_compras():
    caprichado = calcular_opcoes(GRUPO)[0]
    assert caprichado.custo_total == planejar_compras(GRUPO, None, None, None,
                                                      caprichado.opcao.pesos).custo_total


def test_com_precos_padrao_o_caprichado_custa_mais_e_o_simples_menos():
    custos = [c.custo_total for c in calcular_opcoes(GRUPO)]
    assert custos == sorted(custos, reverse=True)


def test_custo_por_pessoa_divide_pelo_grupo_todo():
    opcao = calcular_opcoes(GRUPO)[0]
    assert opcao.custo_por_pessoa == -(-opcao.custo_total // GRUPO.pessoas)


def test_precos_do_usuario_mudam_o_custo():
    padrao = calcular_opcoes(GRUPO)[0].custo_total
    assert calcular_opcoes(GRUPO, precos={"picanha": 20000})[0].custo_total > padrao


def test_secoes_fora_barateiam_todas_as_opcoes():
    com_tudo = calcular_opcoes(GRUPO)
    sem_hortifruti = calcular_opcoes(GRUPO, secoes_fora={"Hortifruti"})
    assert all(s.custo_total < c.custo_total for s, c in zip(sem_hortifruti, com_tudo, strict=True))


def ids_do_grupo(nome):
    return [p.id for p in dict(grupos_de_precos())[nome]]


def test_grupos_de_precos_comecam_pelas_carnes_e_pelo_vegetariano():
    assert [nome for nome, _ in grupos_de_precos()][:2] == ["Carnes", "Vegetariano"]


def test_grupo_carnes_sao_os_cortes_das_opcoes():
    assert ids_do_grupo("Carnes") == [c.id for c in cortes_das_opcoes()]


def test_grupo_vegetariano_e_a_grelha_vegetariana():
    assert ids_do_grupo("Vegetariano") == list(MISTURA_VEGETARIANA)


def test_hortifruti_dos_precos_so_tem_acompanhamentos():
    assert ids_do_grupo("Hortifruti") == ["tomate", "cebola", "pimentao", "salada_folhas"]


def test_descartaveis_nao_tem_preco_para_conferir():
    assert "Descartáveis" not in dict(grupos_de_precos())


def test_todo_item_com_preco_aparece_uma_vez():
    ids = [p.id for _, produtos in grupos_de_precos()[2:] for p in produtos]
    assert sorted(ids) == sorted(i for i, p in ITENS.items()
                                 if p.secao not in ("Mercearia", "Descartáveis"))


def test_mercearia_nao_tem_preco_para_conferir():
    assert "Mercearia" not in dict(grupos_de_precos())


def test_opcoes_nao_tem_orcamento_para_estourar():
    assert not any(c.compras.estourou for c in calcular_opcoes(GRUPO))
