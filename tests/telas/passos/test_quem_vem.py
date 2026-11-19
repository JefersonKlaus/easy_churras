"""Passo 2: quem vem, com os contadores ou contando em palavras."""
from dubles import resposta_ok
from tela import achar, campos, clicar, tem_texto, textos

PRECOS, QUEM_VEM, QUANDO, ESCOLHA = range(4)

TEXTO_LIVRE = "Ou conte em poucas palavras"


PEDIDO_DA_IA = '{"adultos": 12, "criancas": 3, "vegetarianos": 1, "duracao_horas": 6}'


def proximo(app, pagina, passo):
    app.ir_assistente(passo)
    clicar(achar(pagina, "Próximo"))


def entender(app, pagina, texto):
    app.rascunho.texto_livre = texto
    app.ir_assistente(QUEM_VEM)
    clicar(achar(pagina, "Entender o texto"))


def test_quem_vem_mostra_os_contadores(app, pagina):
    app.ir_assistente(QUEM_VEM)
    assert {"Adultos", "Crianças", "Vegetarianos (entre os adultos)",
            "Adultos que bebem álcool"} <= set(textos(pagina))


def test_quem_vem_sem_ninguem_mostra_erro_e_nao_avanca(app, pagina, rascunho_pronto):
    rascunho_pronto.adultos = rascunho_pronto.criancas = 0
    proximo(app, pagina, QUEM_VEM)
    assert "precisa vir pelo menos uma pessoa" in textos(pagina)
    assert textos(pagina)[0] == "Quem vem"


def test_sem_chave_nao_mostra_o_texto_livre(app, pagina):
    app.ir_assistente(QUEM_VEM)
    assert TEXTO_LIVRE not in campos(pagina) and "Entender o texto" not in textos(pagina)


def test_com_chave_mostra_o_texto_livre(app, pagina, ligar_groq):
    ligar_groq(resposta_ok("não usada"))
    app.ir_assistente(QUEM_VEM)
    assert TEXTO_LIVRE in campos(pagina)


def test_entender_com_ia_preenche_o_rascunho(app, pagina, ligar_groq):
    ligar_groq(resposta_ok(PEDIDO_DA_IA))
    entender(app, pagina, "churrasco para 12 adultos e 3 crianças")
    r = app.rascunho
    assert (r.adultos, r.criancas, r.vegetarianos, r.duracao_horas) == (12, 3, 1, 6)


def test_entender_mostra_o_que_foi_entendido(app, pagina, ligar_groq):
    ligar_groq(resposta_ok(PEDIDO_DA_IA))
    entender(app, pagina, "churrasco para 12 adultos e 3 crianças")
    assert tem_texto(pagina, "Entendi: 12 adultos")


def test_entender_com_a_chave_recusada_usa_o_modo_offline(app, pagina, ligar_groq):
    ligar_groq((401, {}, ""))
    entender(app, pagina, "12 adultos")
    assert app.rascunho.adultos == 12 and app.ocupado is False


def test_entender_com_a_chave_recusada_avisa(app, pagina, ligar_groq):
    ligar_groq((401, {}, ""))
    entender(app, pagina, "12 adultos")
    assert tem_texto(pagina, "recusou a chave") and tem_texto(pagina, "modo offline")
