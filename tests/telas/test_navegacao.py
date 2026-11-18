"""Navegação sem barra de cima: ícones no cabeçalho de cada tela e abas do plano no rodapé."""
import pytest

from tela import aba_selecionada, abas, icones, ir_para_aba, parte_que_rola, textos, tocar_icone

ABAS = ["Carnes", "Compras", "Horários", "Mestre"]
IR = {"Carnes": "ir_plano", "Compras": "ir_lista", "Horários": "ir_cronograma",
      "Mestre": "ir_conversa"}


def cabecalho_fixo(pagina):
    """Tudo o que fica fixo em cima do conteúdo que rola."""
    rola = parte_que_rola(pagina)
    return pagina.adicionados[:pagina.adicionados.index(rola)]


# ---------------------------------------------------------------- sem barra de cima

@pytest.mark.parametrize("abrir", [lambda app: app.ir_inicio(), lambda app: app.ir_assistente(1),
                                   lambda app: app.ir_plano(), lambda app: app.ir_configuracoes()],
                         ids=["inicio", "assistente", "plano", "configuracoes"])
@pytest.mark.usefixtures("plano_aberto")
def test_nenhuma_tela_tem_barra_de_cima(app, pagina, abrir):
    abrir(app)
    assert getattr(pagina, "appbar", None) is None


# ---------------------------------------------------------------- ícones no cabeçalho

def test_inicio_tem_o_icone_de_configuracoes(app, pagina):
    app.ir_inicio()
    tocar_icone(pagina, "Configurações")
    assert textos(pagina)[0] == "Configurações"


def test_configuracoes_tem_o_icone_de_voltar_ao_inicio(app, pagina):
    app.ir_configuracoes()
    tocar_icone(pagina, "Voltar")
    assert textos(pagina)[0] == "Churrasco Fácil"


@pytest.mark.parametrize("passo", range(4))
@pytest.mark.usefixtures("rascunho_pronto")
def test_assistente_tem_o_x_para_sair_fixo_em_cima(app, pagina, passo):
    app.ir_assistente(passo)
    assert "Início" in [d for raiz in cabecalho_fixo(pagina) for d in icones(raiz)]


@pytest.mark.usefixtures("rascunho_pronto")
def test_x_do_assistente_leva_ao_inicio(app, pagina):
    app.ir_assistente(2)
    tocar_icone(pagina, "Início")
    assert textos(pagina)[0] == "Churrasco Fácil"


@pytest.mark.parametrize("aba", ABAS)
@pytest.mark.usefixtures("plano_aberto")
def test_aba_do_plano_tem_o_icone_de_inicio_fixo_em_cima(app, pagina, aba):
    getattr(app, IR[aba])()
    assert "Início" in [d for raiz in cabecalho_fixo(pagina) for d in icones(raiz)]


@pytest.mark.parametrize("aba", ABAS)
@pytest.mark.usefixtures("plano_aberto")
def test_icone_de_inicio_do_plano_leva_ao_inicio(app, pagina, aba):
    getattr(app, IR[aba])()
    tocar_icone(pagina, "Início")
    assert textos(pagina)[0] == "Churrasco Fácil"


# ---------------------------------------------------------------- abas do plano

@pytest.mark.usefixtures("plano_aberto")
def test_plano_aberto_mostra_as_abas(pagina):
    assert abas(pagina) == ABAS


@pytest.mark.usefixtures("plano_aberto")
def test_plano_abre_na_aba_carnes(pagina):
    assert aba_selecionada(pagina) == "Carnes"


@pytest.mark.parametrize("aba", ABAS)
@pytest.mark.usefixtures("plano_aberto")
def test_tocar_na_aba_abre_a_tela_dela(pagina, aba):
    ir_para_aba(pagina, aba)
    assert textos(pagina)[0] == aba and aba_selecionada(pagina) == aba


@pytest.mark.parametrize("aba", ABAS)
@pytest.mark.usefixtures("plano_aberto")
def test_cabecalho_diz_de_qual_churrasco_e(app, pagina, aba):
    getattr(app, IR[aba])()
    assert "Teste · sábado, 21/11 às 14:00" in textos(pagina)


@pytest.mark.parametrize("abrir", [lambda app: app.ir_inicio(),
                                   lambda app: app.ir_configuracoes(),
                                   lambda app: app.ir_assistente(0)],
                         ids=["inicio", "configuracoes", "assistente"])
@pytest.mark.usefixtures("plano_aberto")
def test_fora_do_plano_nao_ha_abas(app, pagina, abrir):
    abrir(app)
    assert abas(pagina) == []


def test_sem_plano_nao_ha_abas(app, pagina):
    app.ir_plano()
    assert abas(pagina) == []
