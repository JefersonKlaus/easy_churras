"""Assistente em 4 passos, um assunto por tela: preços, quem vem, quando e a escolha."""
import pytest

from churrasco_facil.configuracao import Configuracao
from churrasco_facil.dinheiro import formatar_reais
from churrasco_facil.opcoes import OPCOES, calcular_opcoes, grupos_de_precos
from dubles import resposta_ok
from tela import (achar, campos, cartao_de, clicar, digitar, estados_dos_passos, fixos,
                  parte_que_rola, tem_texto, textos, tocar)

PRECOS, QUEM_VEM, QUANDO, ESCOLHA = range(4)
TITULOS = ["Preços", "Quem vem", "Quando", "Escolha o churrasco"]
TEXTO_LIVRE = "Ou conte em poucas palavras"
PEDIDO_DA_IA = '{"adultos": 12, "criancas": 3, "vegetarianos": 1, "duracao_horas": 6}'


def proximo(app, pagina, passo):
    app.ir_assistente(passo)
    clicar(achar(pagina, "Próximo"))


def confirmar_precos(app, pagina, **digitados):
    app.ir_assistente(PRECOS)
    for rotulo, valor in digitados.items():
        digitar(campos(pagina)[rotulo], valor)
    clicar(achar(pagina, "Próximo"))


def entender(app, pagina, texto):
    app.rascunho.texto_livre = texto
    app.ir_assistente(QUEM_VEM)
    clicar(achar(pagina, "Entender o texto"))


def escolher(app, pagina, titulo):
    """Abre a escolha e toca no cartão da opção."""
    app.ir_assistente(ESCOLHA)
    tocar(pagina, titulo)


# ---------------------------------------------------------------- caminho

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


@pytest.mark.parametrize("passo", range(4))
@pytest.mark.usefixtures("rascunho_pronto")
def test_passo_nao_usa_texto_para_dizer_o_numero(app, pagina, passo):
    app.ir_assistente(passo)
    assert not tem_texto(pagina, "Passo ")


@pytest.mark.parametrize("passo", range(4))
@pytest.mark.usefixtures("rascunho_pronto")
def test_titulo_do_passo_fica_fixo_em_cima(app, pagina, passo):
    app.ir_assistente(passo)
    assert fixos(pagina)[0] == TITULOS[passo]


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


@pytest.mark.parametrize("passo", range(4))
@pytest.mark.usefixtures("rascunho_pronto")
def test_botoes_de_navegacao_sao_grandes(app, pagina, passo):
    app.ir_assistente(passo)
    voltar = achar(pagina, "Voltar")
    assert (voltar.height, voltar.expand) == (56, True)


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


# ---------------------------------------------------------------- 1. preços

@pytest.mark.parametrize("produto", [p for _, ps in grupos_de_precos() for p in ps],
                         ids=lambda p: p.id)
def test_precos_tem_um_campo_para_cada_preco_que_entra_na_conta(app, pagina, produto):
    app.ir_assistente(PRECOS)
    assert produto.nome in campos(pagina)


@pytest.mark.parametrize("campo", ["Picanha", "Data"])
@pytest.mark.usefixtures("rascunho_pronto")
def test_valor_dos_campos_fica_centralizado(app, pagina, campo):
    app.ir_assistente(PRECOS if campo == "Picanha" else QUANDO)
    assert campos(pagina)[campo].text_align == "CENTER"


@pytest.mark.parametrize("descartavel", ["Copos descartáveis (pacote 50)",
                                         "Guardanapos (pacote 50)"])
def test_descartaveis_nao_tem_preco_para_conferir(app, pagina, descartavel):
    app.ir_assistente(PRECOS)
    assert descartavel not in campos(pagina)


@pytest.mark.parametrize("nome, por", [("Picanha", "/kg"), ("Pão de alho", "/un")])
def test_campo_de_preco_diz_a_unidade(app, pagina, nome, por):
    app.ir_assistente(PRECOS)
    assert (campos(pagina)[nome].prefix, campos(pagina)[nome].suffix) == ("R$ ", por)


@pytest.mark.parametrize("secao", ["Carnes", "Vegetariano", "Hortifruti", "Bebidas",
                                   "Carvão e acessórios"])
def test_precos_sao_agrupados(app, pagina, secao):
    app.ir_assistente(PRECOS)
    assert secao in textos(pagina)


def test_precos_perguntam_se_o_hortifruti_entra_na_conta(app, pagina):
    app.ir_assistente(PRECOS)
    assert campos(pagina)["Incluir hortifruti na conta"].value is True


def test_so_o_hortifruti_e_perguntado(app, pagina):
    app.ir_assistente(PRECOS)
    assert [r for r in campos(pagina) if r.startswith("Incluir")] == \
        ["Incluir hortifruti na conta"]


@pytest.mark.parametrize("da_mercearia", ["Arroz (pacote 1 kg)", "Sal grosso (pacote 1 kg)"])
def test_mercearia_nao_tem_preco_para_conferir(app, pagina, da_mercearia):
    app.ir_assistente(PRECOS)
    assert da_mercearia not in campos(pagina)


def test_tirar_a_secao_da_conta_esconde_os_precos_dela(app, pagina):
    app.ir_assistente(PRECOS)
    digitar(campos(pagina)["Incluir hortifruti na conta"], False)
    assert "Tomate" not in campos(pagina) and "Picanha" in campos(pagina)


def test_tirar_a_secao_da_conta_fica_no_rascunho(app, pagina):
    app.ir_assistente(PRECOS)
    digitar(campos(pagina)["Incluir hortifruti na conta"], False)
    assert app.rascunho.secoes_fora == {"Hortifruti"}


def test_pôr_a_secao_de_volta_mostra_os_precos(app, pagina):
    app.ir_assistente(PRECOS)
    digitar(campos(pagina)["Incluir hortifruti na conta"], False)
    digitar(campos(pagina)["Incluir hortifruti na conta"], True)
    assert "Tomate" in campos(pagina) and app.rascunho.secoes_fora == set()


def test_secao_fora_continua_fora_ao_voltar_para_os_precos(app, pagina):
    app.rascunho.secoes_fora.add("Hortifruti")
    app.ir_assistente(PRECOS)
    assert campos(pagina)["Incluir hortifruti na conta"].value is False
    assert "Tomate" not in campos(pagina)


def test_preco_errado_de_secao_fora_nao_trava(app, pagina):
    app.ir_assistente(PRECOS)
    digitar(campos(pagina)["Tomate"], "caro")
    digitar(campos(pagina)["Incluir hortifruti na conta"], False)
    clicar(achar(pagina, "Próximo"))
    assert textos(pagina)[0] == "Quem vem" and "tomate" not in app.config.precos


def test_precos_comecam_com_o_preco_salvo(app, pagina):
    app.config.precos = {"picanha": 9500}
    app.ir_assistente(PRECOS)
    assert campos(pagina)["Picanha"].value == "95,00"


@pytest.mark.parametrize("nome, valor, id, centavos", [
    ("Picanha", "95,00", "picanha", 9500), ("Cerveja (lata 350 ml)", "4,50", "cerveja_lata", 450),
])
def test_proximo_guarda_os_precos_digitados(app, pagina, nome, valor, id, centavos):
    confirmar_precos(app, pagina, **{nome: valor})
    assert app.config.precos == {id: centavos}


def test_proximo_salva_os_precos_no_aparelho(app, pagina, pasta_de_dados):
    confirmar_precos(app, pagina, Picanha="95,00")
    assert (pasta_de_dados / "configuracao.json").exists()


@pytest.mark.parametrize("valor", ["caro", "-3", "99999999"])
def test_preco_invalido_mostra_erro_e_nao_avanca(app, pagina, valor):
    confirmar_precos(app, pagina, Picanha=valor)
    assert tem_texto(pagina, "Confira o preço. Picanha") and textos(pagina)[0] == "Preços"


def test_erro_aparece_no_rodape_a_vista(app, pagina):
    confirmar_precos(app, pagina, Picanha="caro")
    assert any(t.startswith("Confira o preço") for t in fixos(pagina))


def test_preco_invalido_nao_muda_a_configuracao(app, pagina):
    confirmar_precos(app, pagina, Picanha="caro")
    assert app.config == Configuracao()


# ---------------------------------------------------------------- 2. quem vem

@pytest.mark.parametrize("rotulo", ["Adultos", "Crianças", "Vegetarianos (entre os adultos)",
                                    "Adultos que bebem álcool"])
def test_quem_vem_mostra_os_contadores(app, pagina, rotulo):
    app.ir_assistente(QUEM_VEM)
    assert rotulo in textos(pagina)


@pytest.mark.parametrize("de_outro_passo", ["Data", "Hora de servir", "Duração da festa (horas)"])
def test_quem_vem_nao_pergunta_quando(app, pagina, de_outro_passo):
    app.ir_assistente(QUEM_VEM)
    assert de_outro_passo not in textos(pagina) and de_outro_passo not in campos(pagina)


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


# ---------------------------------------------------------------- 3. quando

@pytest.mark.parametrize("rotulo", ["Data", "Hora de servir"])
def test_quando_tem_os_campos(app, pagina, rotulo):
    app.ir_assistente(QUANDO)
    assert rotulo in campos(pagina)


def test_quando_tem_a_duracao_da_festa_explicada(app, pagina):
    app.ir_assistente(QUANDO)
    assert "Duração da festa (horas)" in textos(pagina)
    assert tem_texto(pagina, "Quanto tempo os convidados vão ficar")


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


# ---------------------------------------------------------------- 4. escolha

@pytest.mark.parametrize("opcao", OPCOES, ids=lambda o: o.id)
@pytest.mark.usefixtures("rascunho_pronto")
def test_escolha_mostra_cada_opcao(app, pagina, opcao):
    app.ir_assistente(ESCOLHA)
    assert opcao.titulo in textos(pagina) and opcao.descricao in textos(pagina)


@pytest.mark.parametrize("indice", range(len(OPCOES)), ids=[o.id for o in OPCOES])
@pytest.mark.usefixtures("rascunho_pronto")
def test_escolha_mostra_o_custo_da_opcao_com_os_precos_salvos(app, pagina, indice):
    app.config.precos = {"picanha": 20000}
    app.ir_assistente(ESCOLHA)
    calculada = calcular_opcoes(app.rascunho.para_convidados(), precos=app.config.precos)[indice]
    assert tem_texto(pagina, f"{formatar_reais(calculada.custo_total)} no total")


@pytest.mark.parametrize("opcao", OPCOES, ids=lambda o: o.id)
@pytest.mark.usefixtures("rascunho_pronto")
def test_o_cartao_da_opcao_e_o_botao(app, pagina, opcao):
    app.ir_assistente(ESCOLHA)
    assert cartao_de(pagina, opcao.titulo).on_click is not None


@pytest.mark.usefixtures("rascunho_pronto")
def test_escolha_nao_tem_botao_escolher_este(app, pagina):
    app.ir_assistente(ESCOLHA)
    assert "Escolher este" not in textos(pagina)


@pytest.mark.usefixtures("rascunho_pronto")
def test_escolha_diz_que_e_so_tocar_na_opcao(app, pagina):
    app.ir_assistente(ESCOLHA)
    assert "Toque na opção que você quer." in textos(pagina)


@pytest.mark.parametrize("opcao", OPCOES, ids=lambda o: o.id)
@pytest.mark.usefixtures("rascunho_pronto")
def test_escolher_abre_o_plano_com_as_carnes_da_opcao(app, pagina, opcao):
    escolher(app, pagina, opcao.titulo)
    assert set(app.plano.compras.pesos) == set(opcao.pesos)


@pytest.mark.usefixtures("rascunho_pronto")
def test_escolher_abre_a_aba_carnes(app, pagina):
    escolher(app, pagina, "Simples")
    assert textos(pagina)[0] == "Carnes"


@pytest.mark.usefixtures("rascunho_pronto")
def test_plano_escolhido_custa_o_que_a_opcao_mostrou(app, pagina):
    escolher(app, pagina, "Tradicional")
    tradicional = calcular_opcoes(app.rascunho.para_convidados())[1]
    assert app.plano.custo_total == tradicional.custo_total


@pytest.mark.usefixtures("rascunho_pronto")
def test_plano_escolhido_leva_o_nome_da_opcao_e_nao_tem_orcamento(app, pagina):
    escolher(app, pagina, "Simples")
    assert (app.plano.pedido.nome, app.plano.pedido.orcamento) == ("Churrasco Simples", None)


def test_escolha_diz_o_que_ficou_fora_da_conta(app, pagina, rascunho_pronto):
    rascunho_pronto.secoes_fora.add("Hortifruti")
    app.ir_assistente(ESCOLHA)
    assert tem_texto(pagina, "Sem hortifruti.")


def test_escolha_com_secao_fora_custa_menos(app, pagina, rascunho_pronto):
    rascunho_pronto.secoes_fora.add("Hortifruti")
    app.ir_assistente(ESCOLHA)
    sem = calcular_opcoes(rascunho_pronto.para_convidados(), secoes_fora={"Hortifruti"})[0]
    assert tem_texto(pagina, f"{formatar_reais(sem.custo_total)} no total")


def test_plano_escolhido_deixa_a_secao_fora(app, pagina, rascunho_pronto):
    rascunho_pronto.secoes_fora.add("Hortifruti")
    escolher(app, pagina, "Simples")
    assert app.plano.pedido.secoes_fora == ("Hortifruti",)
    assert "tomate" not in {i.produto.id for i in app.plano.compras.itens}


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
