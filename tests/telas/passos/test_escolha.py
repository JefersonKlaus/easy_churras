"""Passo 4: escolher o churrasco."""
import pytest
from tela import aba_selecionada, tem_texto, textos, tocar

from churrasco_facil.dinheiro import formatar_reais
from churrasco_facil.opcoes import OPCOES, calcular_opcoes

PRECOS, QUEM_VEM, QUANDO, ESCOLHA = range(4)


def escolher(app, pagina, titulo):
    """Abre a escolha e toca no cartão da opção."""
    app.ir_assistente(ESCOLHA)
    tocar(pagina, titulo)


@pytest.mark.parametrize("indice", range(len(OPCOES)), ids=[o.id for o in OPCOES])
@pytest.mark.usefixtures("rascunho_pronto")
def test_escolha_mostra_o_custo_da_opcao_com_os_precos_salvos(app, pagina, indice):
    app.config.precos = {"picanha": 20000}
    app.ir_assistente(ESCOLHA)
    calculada = calcular_opcoes(app.rascunho.para_convidados(), precos=app.config.precos)[indice]
    assert tem_texto(pagina, f"{formatar_reais(calculada.custo_total)} no total")


@pytest.mark.parametrize("opcao", OPCOES, ids=lambda o: o.id)
@pytest.mark.usefixtures("rascunho_pronto")
def test_escolher_abre_o_plano_com_as_carnes_da_opcao(app, pagina, opcao):
    escolher(app, pagina, opcao.titulo)
    assert set(app.plano.compras.pesos) == set(opcao.pesos)


def test_opcao_mostra_quanto_de_carne_e_quais_cortes(app, pagina, rascunho_pronto):
    # com peças inteiras, o que cada opção compra muda com o tamanho do grupo
    rascunho_pronto.adultos, rascunho_pronto.criancas, rascunho_pronto.duracao_horas = 4, 0, 3
    rascunho_pronto.vegetarianos = rascunho_pronto.bebem_alcool = 0
    app.ir_assistente(ESCOLHA)
    assert "2,2 kg de carne: picanha e linguiça toscana." in textos(pagina)


def test_opcao_de_grupo_so_vegetariano_diz_que_nao_tem_carne(app, pagina, rascunho_pronto):
    r = rascunho_pronto
    r.adultos, r.criancas, r.vegetarianos, r.bebem_alcool = 2, 0, 2, 0
    app.ir_assistente(ESCOLHA)
    assert "Sem carne: só a grelha vegetariana." in textos(pagina)


@pytest.mark.usefixtures("rascunho_pronto")
def test_escolher_abre_a_aba_carnes(app, pagina):
    escolher(app, pagina, "Simples")
    assert aba_selecionada(pagina) == "Carnes"


@pytest.mark.usefixtures("rascunho_pronto")
def test_plano_escolhido_custa_o_que_a_opcao_mostrou(app, pagina):
    escolher(app, pagina, "Tradicional")
    tradicional = calcular_opcoes(app.rascunho.para_convidados())[1]
    assert app.plano.custo_total == tradicional.custo_total


@pytest.mark.usefixtures("rascunho_pronto")
def test_plano_escolhido_leva_o_nome_da_opcao(app, pagina):
    escolher(app, pagina, "Simples")
    assert app.plano.pedido.nome == "Churrasco Simples"


@pytest.mark.usefixtures("rascunho_pronto")
def test_plano_escolhido_usa_os_precos_da_configuracao(app, pagina):
    app.config.precos = {"picanha": 123}
    escolher(app, pagina, "Caprichado")
    picanha = next(i for i in app.plano.compras.itens if i.produto.id == "picanha")
    assert picanha.produto.preco == 123


def test_escolher_depois_que_a_hora_passou_mostra_erro(app, pagina, rascunho_pronto):
    app.ir_assistente(ESCOLHA)
    rascunho_pronto.data_texto = "01/01/2020"
    tocar(pagina, "Caprichado")
    assert app.plano is None and "essa data e hora já passaram" in textos(pagina)


def test_escolha_sem_ninguem_mostra_erro(app, pagina, rascunho_pronto):
    rascunho_pronto.adultos = rascunho_pronto.criancas = 0
    app.ir_assistente(ESCOLHA)
    assert "precisa vir pelo menos uma pessoa" in textos(pagina)
