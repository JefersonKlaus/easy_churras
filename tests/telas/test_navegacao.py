"""Navegação do plano: abas no rodapé, cabeçalho e o botão Salvar/Início."""
import pytest
from tela import (aba_selecionada, abas, achar, clicar, digitar, fixos, ir_para_aba,
                  parte_que_rola, pelo_rotulo_de_acessibilidade, tem_texto, textos)

ABAS = ["Carnes", "Compras", "Horários"]


IR = {"Carnes": "ir_carnes", "Compras": "ir_compras", "Horários": "ir_horarios"}


# algo que só aparece no conteúdo de cada aba
MARCA = {"Carnes": "No seu churrasco", "Compras": "Não esqueça", "Horários": "Servir!"}


@pytest.mark.parametrize("aba", ABAS)
@pytest.mark.usefixtures("plano_aberto")
def test_salvar_fica_fixo_embaixo_em_todas_as_abas(app, pagina, aba):
    getattr(app, IR[aba])()
    assert "Salvar" in fixos(pagina) and "Salvar" not in textos(parte_que_rola(pagina))


@pytest.mark.usefixtures("plano_aberto")
def test_abrir_e_trocar_de_aba_nao_salva_sozinho(app):
    app.ir_compras()
    app.ir_horarios()
    assert app.banco.listar() == []


@pytest.mark.usefixtures("plano_aberto")
def test_salvar_guarda_e_o_botao_vira_inicio(app, pagina):
    clicar(achar(pagina, "Salvar"))
    assert len(app.banco.listar()) == 1
    assert fixos(pagina)[-2:] == ["Salvo em Meus churrascos.", "Início"]


@pytest.mark.usefixtures("plano_aberto")
def test_inicio_depois_de_salvar_volta_a_tela_inicial(app, pagina):
    clicar(achar(pagina, "Salvar"))
    clicar(achar(pagina, "Início"))
    assert textos(pagina)[0] == "Churrasco Fácil"


@pytest.mark.usefixtures("plano_aberto")
def test_mudar_depois_de_salvar_volta_a_pedir_para_salvar(app, pagina):
    clicar(achar(pagina, "Salvar"))
    digitar(pelo_rotulo_de_acessibilidade(pagina, "Levar Coração de frango"), True)
    assert "Salvar" in fixos(pagina) and "Início" not in fixos(pagina)


@pytest.mark.usefixtures("plano_aberto")
def test_salvar_de_novo_depois_de_trocar_as_carnes_grava_por_cima(app, pagina):
    clicar(achar(pagina, "Salvar"))
    app.trocar_cortes(["picanha"])
    app.ir_carnes()
    clicar(achar(pagina, "Salvar"))
    assert len(app.banco.listar()) == 1
    assert app.banco.carregar(app.plano_id).pecas_escolhidas == app.plano.pedido.pecas_escolhidas


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
    assert tem_texto(pagina, MARCA[aba]) and aba_selecionada(pagina) == aba


@pytest.mark.parametrize("aba", ABAS)
@pytest.mark.usefixtures("plano_aberto")
def test_cabecalho_diz_de_qual_churrasco_e(app, pagina, aba):
    getattr(app, IR[aba])()
    assert fixos(pagina)[:2] == ["Teste", "sábado, 21/11 às 14:00 · 13 pessoas"]


@pytest.mark.usefixtures("plano_aberto")
def test_fora_do_plano_nao_ha_abas(app, pagina):
    app.ir_inicio()
    assert abas(pagina) == []


def test_sem_plano_nao_ha_abas(app, pagina):
    app.ir_carnes()
    assert abas(pagina) == []
