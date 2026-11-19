"""O que os passos têm em comum: ícones e título em cima, Voltar e Próximo embaixo, o X."""
import pytest
from tela import achar, clicar, estados_dos_passos, fixos, parte_que_rola, textos, tocar_icone

PRECOS, QUEM_VEM, QUANDO, ESCOLHA = range(4)


def proximo(app, pagina, passo):
    app.ir_assistente(passo)
    clicar(achar(pagina, "Próximo"))


@pytest.mark.parametrize("passo, estados", [
    (PRECOS, ["atual", "depois", "depois", "depois"]),
    (QUEM_VEM, ["feito", "atual", "depois", "depois"]),
    (QUANDO, ["feito", "feito", "atual", "depois"]),
    (ESCOLHA, ["feito", "feito", "feito", "atual"]),
])
@pytest.mark.usefixtures("rascunho_pronto")
def test_icones_mostram_em_que_passo_a_pessoa_esta(app, pagina, passo, estados):
    app.ir_assistente(passo)
    assert estados_dos_passos(pagina) == estados


@pytest.mark.parametrize("passo, botoes", [
    (PRECOS, ["Voltar", "Próximo"]), (QUEM_VEM, ["Voltar", "Próximo"]),
    (QUANDO, ["Voltar", "Próximo"]), (ESCOLHA, ["Voltar"]),
])
@pytest.mark.usefixtures("rascunho_pronto")
def test_botoes_de_navegacao_ficam_fixos_embaixo(app, pagina, passo, botoes):
    app.ir_assistente(passo)
    assert fixos(pagina)[-len(botoes):] == botoes
    assert not set(botoes) & set(textos(parte_que_rola(pagina)))


@pytest.mark.parametrize("passo, titulo", [(-5, "Preços"), (99, "Escolha o churrasco")])
def test_passo_fora_do_intervalo_cai_nos_limites(app, pagina, passo, titulo):
    app.ir_assistente(passo)
    assert textos(pagina)[0] == titulo


@pytest.mark.parametrize("passo, proxima_tela", [
    (PRECOS, "Quem vem"), (QUEM_VEM, "Quando"), (QUANDO, "Escolha o churrasco"),
])
@pytest.mark.usefixtures("rascunho_pronto")
def test_proximo_leva_a_tela_seguinte(app, pagina, passo, proxima_tela):
    proximo(app, pagina, passo)
    assert textos(pagina)[0] == proxima_tela


@pytest.mark.parametrize("passo, tela_anterior", [
    (PRECOS, "Planejar um churrasco"), (QUEM_VEM, "Preços"), (QUANDO, "Quem vem"),
    (ESCOLHA, "Quando"),
])
@pytest.mark.usefixtures("rascunho_pronto")
def test_voltar_leva_a_tela_anterior(app, pagina, passo, tela_anterior):
    app.ir_assistente(passo)
    clicar(achar(pagina, "Voltar"))
    assert tela_anterior in textos(pagina)


@pytest.mark.usefixtures("rascunho_pronto")
def test_x_do_assistente_leva_ao_inicio(app, pagina):
    app.ir_assistente(2)
    tocar_icone(pagina, "Sair do planejamento")
    assert textos(pagina)[0] == "Churrasco Fácil"
