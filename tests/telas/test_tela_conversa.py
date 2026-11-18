"""Aba Mestre: a explicação do plano e as dúvidas."""
import pytest

from dubles import resposta_ok
from tela import achar, clicar, tem_texto, textos

CHUVA = "E se começar a chover?"          # uma das sugestões prontas da tela
EXPLICACAO_DA_IA = "Comece pelos cortes fáceis e relaxe."

pytestmark = pytest.mark.usefixtures("plano_aberto")


@pytest.fixture
def plano_salvo(app):
    app.plano_id = app.banco.salvar(app.plano.pedido)
    return app.plano_id


def perguntar_sobre_chuva(app, pagina):
    app.ir_conversa()
    clicar(achar(pagina, CHUVA))


def explicar(app, pagina):
    app.ir_conversa()
    clicar(achar(pagina, "Explicar o meu plano"))


# ---------------------------------------------------------------- explicação

def test_explicacao_sem_chave_usa_o_assistente_local(app, pagina):
    explicar(app, pagina)
    assert tem_texto(pagina, "Para 13 pessoas, o plano compra")


def test_explicacao_pronta_esconde_o_botao(app, pagina):
    explicar(app, pagina)
    assert "Explicar o meu plano" not in textos(pagina)


def test_explicacao_do_plano_salvo_vai_para_o_banco(app, pagina, plano_salvo):
    explicar(app, pagina)
    assert app.banco.carregar(plano_salvo)[1].startswith("Para 13 pessoas")


def test_explicacao_com_groq_aparece(app, pagina, ligar_groq):
    ligar_groq(resposta_ok(EXPLICACAO_DA_IA))
    explicar(app, pagina)
    assert EXPLICACAO_DA_IA in textos(pagina)


def test_explicacao_com_groq_vai_para_o_banco(app, pagina, plano_salvo, ligar_groq):
    ligar_groq(resposta_ok(EXPLICACAO_DA_IA))
    explicar(app, pagina)
    assert app.banco.carregar(plano_salvo)[1] == EXPLICACAO_DA_IA


def test_explicacao_com_groq_limitado_usa_o_modo_offline(app, pagina, ligar_groq):
    ligar_groq((429, {}, ""))
    explicar(app, pagina)
    assert tem_texto(pagina, "Para 13 pessoas") and app.ocupado is False


def test_explicacao_com_groq_limitado_avisa(app, pagina, ligar_groq):
    ligar_groq((429, {}, ""))
    explicar(app, pagina)
    assert any("Muitos pedidos" in t and "modo offline" in t for t in textos(pagina))


# ---------------------------------------------------------------- dúvidas

def test_conversa_com_groq_mostra_pergunta_e_resposta(app, pagina, ligar_groq):
    ligar_groq(resposta_ok("Espere a brasa ficar branca."))
    perguntar_sobre_chuva(app, pagina)
    assert CHUVA in textos(pagina) and "Espere a brasa ficar branca." in textos(pagina)
    assert app.ocupado is False


def test_conversa_sem_chave_deixa_enviar(app, pagina):
    app.ir_conversa()
    assert achar(pagina, "Enviar").disabled is False


def test_conversa_sem_chave_avisa_do_modo_offline(app, pagina):
    app.ir_conversa()
    assert tem_texto(pagina, "Modo offline")


def test_conversa_sem_chave_responde_com_dica_pronta(app, pagina):
    perguntar_sobre_chuva(app, pagina)
    assert tem_texto(pagina, "monóxido de carbono")


def test_conversa_com_a_chave_recusada_responde_offline(app, pagina, ligar_groq):
    ligar_groq((401, {}, ""))
    perguntar_sobre_chuva(app, pagina)
    assert any(t.startswith("Chuva fina") for t in textos(pagina))


def test_conversa_com_a_chave_recusada_avisa(app, pagina, ligar_groq):
    ligar_groq((401, {}, ""))
    perguntar_sobre_chuva(app, pagina)
    assert "Sem internet: respondi com dicas prontas." in textos(pagina)


def test_limpar_conversa_apaga_da_tela_e_do_historico(app, pagina, ligar_groq):
    ligar_groq(resposta_ok("resposta"))
    perguntar_sobre_chuva(app, pagina)
    clicar(achar(pagina, "Limpar conversa"))
    assert "resposta" not in textos(pagina) and app.conversa.historico == []
