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


def seta(cartao):
    """O ícone de seta do cartão: para baixo (fechado) ou para cima (aberto)."""
    return next(c.icon for c in todos(cartao.widget)
                if str(getattr(c, "icon", "") or "").startswith("EXPAND"))


def test_expansivel_comeca_fechado(cartao):
    assert textos(cartao.widget) == ["Título"] and seta(cartao) == "EXPAND_MORE"


def test_tocar_abre_vira_a_seta_e_atualiza_a_tela(cartao):
    clicar(cartao.widget)
    assert textos(cartao.widget) == ["Título", "O detalhe"] and seta(cartao) == "EXPAND_LESS"
    assert cartao.atualizacoes == 1


def test_tocar_de_novo_fecha(cartao):
    clicar(cartao.widget)
    clicar(cartao.widget)
    assert textos(cartao.widget) == ["Título"] and seta(cartao) == "EXPAND_MORE"
