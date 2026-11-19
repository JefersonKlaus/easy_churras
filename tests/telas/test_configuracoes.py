"""Configurações: só a chave do Groq."""
from dubles import resposta_ok
from tela import achar, campos, clicar, digitar, tem_texto, textos, tocar_icone


def salvar_chave(app, pagina, chave):
    app.ir_configuracoes()
    digitar(campos(pagina)["Chave do Groq"], chave)
    clicar(achar(pagina, "Salvar"))


def test_sem_chave_diz_que_a_chave_e_opcional(app, pagina):
    app.ir_configuracoes()
    assert tem_texto(pagina, "A chave é opcional")


def test_com_chave_diz_que_a_ia_esta_ligada(app, pagina, ligar_groq):
    ligar_groq(resposta_ok("não usada"))
    app.ir_configuracoes()
    assert tem_texto(pagina, "IA ligada")


def test_salvar_grava_a_chave_sem_espacos(app, pagina):
    salvar_chave(app, pagina, " minha-chave ")
    assert app.config.chave_groq == "minha-chave"


def test_salvar_confirma_na_tela(app, pagina):
    salvar_chave(app, pagina, "minha-chave")
    assert "Configurações salvas." in textos(pagina)


def test_salvar_grava_o_arquivo(app, pagina, pasta_de_dados):
    salvar_chave(app, pagina, "minha-chave")
    assert (pasta_de_dados / "configuracao.json").exists()


def test_salvar_a_chave_nao_mexe_nos_precos(app, pagina):
    app.config.precos = {"picanha": 9500}
    salvar_chave(app, pagina, "minha-chave")
    assert app.config.precos == {"picanha": 9500}


def test_testar_conexao_sem_chave_pede_a_chave(app, pagina):
    app.ir_configuracoes()
    clicar(achar(pagina, "Testar conexão"))
    assert "Escreva a chave primeiro." in textos(pagina)


def test_voltar_leva_ao_inicio(app, pagina):
    app.ir_configuracoes()
    tocar_icone(pagina, "Voltar")
    assert "Planejar um churrasco" in textos(pagina)
