from types import SimpleNamespace

import pytest

from tela import clicar, textos, tocar_icone, todos


@pytest.fixture
def contador(modulo_app):
    """Contador de 0 a 2 começando em 1, que anota as mudanças e as atualizações."""
    from churrasco_facil.telas.widgets import Contador
    anotado = SimpleNamespace(mudancas=[], atualizacoes=0)

    def atualizar():
        anotado.atualizacoes += 1

    anotado.widget = Contador("Adultos", 1, 0, 2, anotado.mudancas.append, atualizar)
    return anotado


def apertar(contador, botao, vezes=1):
    dica = {"+": "Mais", "-": "Menos"}[botao]
    for _ in range(vezes):
        tocar_icone(contador.widget.controle, dica)


def test_mais_aumenta_avisa_e_atualiza(contador):
    apertar(contador, "+")
    assert (contador.widget.valor, contador.mudancas, contador.atualizacoes) == (2, [2], 1)


def test_mais_no_maximo_nao_muda(contador):
    apertar(contador, "+", vezes=2)
    assert (contador.widget.valor, contador.mudancas) == (2, [2])


def test_menos_no_minimo_nao_muda(contador):
    apertar(contador, "-", vezes=2)
    assert (contador.widget.valor, contador.mudancas) == (0, [0])


def test_definir_respeita_os_limites_sem_avisar(contador):
    contador.widget.definir(50)
    assert contador.widget.valor == 2 and contador.mudancas == []


def test_definir_mostra_o_numero_novo(contador):
    contador.widget.definir(0)
    assert "0" in textos(contador.widget.controle)


# ---------------------------------------------------------------- botões

@pytest.fixture
def w(modulo_app):
    from churrasco_facil.telas import widgets
    return widgets


@pytest.mark.parametrize("fabrica", ["botao_principal", "botao_secundario"])
def test_botoes_de_acao_sao_grandes_e_ocupam_a_largura(w, fabrica):
    botao = getattr(w, fabrica)("Ok", lambda _e: None)
    assert (botao.height, botao.expand) == (56, True)


def test_botao_de_icone_tem_alvo_de_toque_de_48(w):
    botao = w.botao_icone("HOME", "Início", lambda _e: None)
    assert (botao.width, botao.height) == (48, 48)


def test_botao_de_icone_tem_dica_para_quem_nao_ve_o_icone(w):
    assert w.botao_icone("HOME", "Início", lambda _e: None).tooltip == "Início"


def test_contador_mostra_o_nome_em_cima_e_os_botoes_embaixo(contador):
    assert textos(contador.widget.controle) == ["Adultos", "1"]


@pytest.mark.parametrize("fabrica", ["titulo", "subtitulo", "secao", "dica", "erro"])
def test_textos_ficam_centralizados(w, fabrica):
    assert getattr(w, fabrica)("x").text_align == "CENTER"


def test_cartao_com_acao_e_um_botao(w):
    acoes = []
    cartao = w.cartao([w.secao("Opção")], on_click=acoes.append)
    clicar(cartao)
    assert acoes == [None] and cartao.ink is True


def test_cartao_sem_acao_nao_e_clicavel(w):
    assert w.cartao([w.secao("Info")]).on_click is None


@pytest.mark.parametrize("lados, quantos", [({"esquerda": "E"}, 3), ({"direita": "D"}, 3),
                                            ({}, 1)])
def test_cabecalho_equilibra_o_icone_para_o_titulo_ficar_no_meio(w, lados, quantos):
    assert len(w.cabecalho("Título", **lados).controls) == quantos


def test_botoes_do_contador_tem_alvo_de_toque_grande(contador):
    botoes = [c for c in todos(contador.widget.controle) if getattr(c, "tooltip", None)]
    assert [(b.tooltip, b.width >= 48, b.height >= 48) for b in botoes] == \
        [("Menos", True, True), ("Mais", True, True)]


# ---------------------------------------------------------------- expansivel

@pytest.fixture
def cartao(modulo_app):
    """Cartão expansível com um título e um detalhe, que anota as atualizações."""
    from churrasco_facil.telas import widgets as w
    anotado = SimpleNamespace(atualizacoes=0)

    def atualizar():
        anotado.atualizacoes += 1

    anotado.widget = w.expansivel([w.secao("Título")], [w.subtitulo("O detalhe")], atualizar,
                                  "dicas")
    return anotado


def test_expansivel_comeca_fechado(cartao):
    assert textos(cartao.widget) == ["Título", "Ver dicas ▾"]


def test_tocar_abre_e_atualiza_a_tela(cartao):
    clicar(cartao.widget)
    assert textos(cartao.widget) == ["Título", "Esconder dicas ▴", "O detalhe"]
    assert cartao.atualizacoes == 1


def test_tocar_de_novo_fecha(cartao):
    clicar(cartao.widget)
    clicar(cartao.widget)
    assert textos(cartao.widget) == ["Título", "Ver dicas ▾"]
