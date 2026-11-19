"""Passo 1: conferir os preços."""
import pytest
from tela import achar, campos, clicar, digitar, fixos, tem_texto, textos

from churrasco_facil.configuracao import Configuracao
from churrasco_facil.precos import grupos_de_precos

PRECOS, QUEM_VEM, QUANDO, ESCOLHA = range(4)


def confirmar_precos(app, pagina, **digitados):
    app.ir_assistente(PRECOS)
    for rotulo, valor in digitados.items():
        digitar(campos(pagina)[rotulo], valor)
    clicar(achar(pagina, "Próximo"))


def test_precos_tem_um_campo_para_cada_preco_que_entra_na_conta(app, pagina):
    # exatamente esses: mercearia e descartáveis (só lembrete) ficam sem campo
    app.ir_assistente(PRECOS)
    precos = {r for r in campos(pagina) if not r.startswith("Incluir")}
    assert precos == {p.nome for _, ps in grupos_de_precos() for p in ps}


@pytest.mark.parametrize("nome, por", [("Picanha", "/kg"), ("Água (garrafa 1,5 L)", "/un")])
def test_campo_de_preco_diz_a_unidade(app, pagina, nome, por):
    app.ir_assistente(PRECOS)
    assert (campos(pagina)[nome].prefix, campos(pagina)[nome].suffix) == ("R$ ", por)


def test_precos_sao_agrupados(app, pagina):
    app.ir_assistente(PRECOS)
    assert {nome for nome, _ in grupos_de_precos()} <= set(textos(pagina))


def test_precos_comecam_com_o_preco_salvo(app, pagina):
    app.config.precos = {"picanha": 9500}
    app.ir_assistente(PRECOS)
    assert campos(pagina)["Picanha"].value == "95,00"


@pytest.mark.parametrize("nome, valor, id, centavos", [
    ("Picanha", "95,00", "picanha", 9500),
    ("Refrigerante (garrafa 2 L)", "10,00", "refrigerante_2l", 1000),
])
def test_proximo_guarda_os_precos_digitados(app, pagina, nome, valor, id, centavos):
    confirmar_precos(app, pagina, **{nome: valor})
    assert app.config.precos == {id: centavos}


def test_proximo_salva_os_precos_no_aparelho(app, pagina, pasta_de_dados):
    confirmar_precos(app, pagina, Picanha="95,00")
    assert (pasta_de_dados / "configuracao.json").exists()


def test_preco_invalido_mostra_erro_e_nao_avanca(app, pagina):
    confirmar_precos(app, pagina, Picanha="caro")
    assert tem_texto(pagina, "Confira o preço. Picanha") and textos(pagina)[0] == "Preços"


def test_erro_aparece_no_rodape_a_vista(app, pagina):
    confirmar_precos(app, pagina, Picanha="caro")
    assert any(t.startswith("Confira o preço") for t in fixos(pagina))


def test_preco_invalido_nao_muda_a_configuracao(app, pagina):
    confirmar_precos(app, pagina, Picanha="caro")
    assert app.config == Configuracao()
