"""Passo 3: quando é e quanto dura."""
import pytest
from tela import achar, campos, clicar, digitar, textos

PRECOS, QUEM_VEM, QUANDO, ESCOLHA = range(4)


def proximo(app, pagina, passo):
    app.ir_assistente(passo)
    clicar(achar(pagina, "Próximo"))


def test_quando_nao_pede_orcamento_nem_nome(app, pagina):
    app.ir_assistente(QUANDO)
    assert list(campos(pagina)) == ["Data", "Hora de servir"]


def test_digitar_a_data_atualiza_o_rascunho(app, pagina):
    app.ir_assistente(QUANDO)
    digitar(campos(pagina)["Data"], "25/12/2099")
    assert app.rascunho.data_texto == "25/12/2099"


@pytest.mark.parametrize("data, erro", [("31/02/2099", "essa data não existe"),
                                        ("01/01/2020", "essa data e hora já passaram")])
def test_quando_com_data_ruim_mostra_erro_e_nao_avanca(app, pagina, rascunho_pronto, data, erro):
    rascunho_pronto.data_texto = data
    proximo(app, pagina, QUANDO)
    assert erro in textos(pagina) and textos(pagina)[0] == "Quando"
