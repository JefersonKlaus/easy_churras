"""As opções de churrasco (Caprichado, Tradicional, Simples) e o custo de cada uma."""
from churrasco_facil.compras import planejar_compras
from churrasco_facil.convidados import Convidados
from churrasco_facil.opcoes import calcular_opcoes

GRUPO = Convidados(adultos=8, criancas=2, bebem_alcool=4)


def test_custo_da_opcao_e_o_da_lista_de_compras():
    caprichado = calcular_opcoes(GRUPO)[0]
    assert caprichado.custo_total == \
        planejar_compras(GRUPO, pesos_preferidos=caprichado.opcao.pesos).custo_total


def test_com_precos_padrao_o_caprichado_custa_mais_e_o_simples_menos():
    custos = [c.custo_total for c in calcular_opcoes(GRUPO)]
    assert custos == sorted(custos, reverse=True)


def test_custo_por_pessoa_divide_pelo_grupo_todo():
    opcao = calcular_opcoes(GRUPO)[0]
    assert opcao.custo_por_pessoa == -(-opcao.custo_total // GRUPO.pessoas)


def test_precos_do_usuario_mudam_o_custo():
    padrao = calcular_opcoes(GRUPO)[0].custo_total
    assert calcular_opcoes(GRUPO, precos={"picanha": 20000})[0].custo_total > padrao
