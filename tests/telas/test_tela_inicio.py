import pytest

from tela import achar, campos, clicar, textos, tocar_icone


@pytest.fixture
def plano_salvo(app, pedido):
    return app.banco.salvar(pedido)


def test_inicio_mostra_o_nome_do_app(app, pagina):
    app.ir_inicio()
    assert "Churrasco Fácil" in textos(pagina)


def test_configuracoes_ficam_no_icone_de_cima(app, pagina):
    app.ir_inicio()
    tocar_icone(pagina, "Configurações")
    assert "Chave do Groq" in campos(pagina)


def test_inicio_nao_tem_botao_de_configuracoes(app, pagina):
    app.ir_inicio()
    assert "Configurações" not in textos(pagina)


def test_planejar_comeca_pelos_precos(app, pagina):
    app.ir_inicio()
    clicar(achar(pagina, "Planejar um churrasco"))
    assert textos(pagina)[0] == "Preços"


def test_sem_planos_salvos_nao_mostra_a_secao(app, pagina):
    app.ir_inicio()
    assert "Meus churrascos" not in textos(pagina)


def test_plano_salvo_aparece_no_inicio(app, pagina, plano_salvo):
    app.ir_inicio()
    assert "Meus churrascos" in textos(pagina) and "Teste" in textos(pagina)


def test_abrir_plano_salvo_carrega_o_pedido(app, pagina, pedido, plano_salvo):
    app.ir_inicio()
    clicar(achar(pagina, "Abrir"))
    assert app.plano.pedido == pedido and app.plano_id == plano_salvo


@pytest.mark.usefixtures("plano_salvo")
def test_abrir_plano_salvo_usa_os_precos_atuais(app, pagina):
    app.config.precos = {"pao_alho": 1}
    app.ir_inicio()
    clicar(achar(pagina, "Abrir"))
    pao = next(i for i in app.plano.compras.itens if i.produto.id == "pao_alho")
    assert pao.produto.preco == 1


def test_excluir_plano_salvo_tira_do_banco_e_da_tela(app, pagina, plano_salvo):
    app.ir_inicio()
    tocar_icone(pagina, "Excluir")
    assert app.banco.listar() == []
    assert "Meus churrascos" not in textos(pagina)
