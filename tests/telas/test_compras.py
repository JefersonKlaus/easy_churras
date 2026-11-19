"""Aba Compras: o que comprar, por seção do mercado."""
import pytest
from tela import achar, clicar, textos, todos

from churrasco_facil.catalogo_carnes import DICA_DO_ACOUGUE
from churrasco_facil.compartilhar import texto_compras
from churrasco_facil.dinheiro import formatar_reais
from churrasco_facil.lista_compras import formatar_quantidade

pytestmark = pytest.mark.usefixtures("lista_aberta")


@pytest.fixture
def lista_aberta(app, plano_aberto):
    app.ir_compras()


def cartao_com(pagina, titulo):
    """O menor bloco da tela que tem o título e mais alguma coisa."""
    return [c for c in todos(pagina) if titulo in textos(c) and len(textos(c)) > 1][-1]


@pytest.fixture
def agua(plano):
    return next(i for i in plano.compras.itens if i.produto.id == "agua_1_5l")


def test_lista_agrupa_por_secao(pagina):
    assert {"Açougue", "Hortifruti", "Bebidas", "Carvão e acessórios"} <= set(textos(pagina))


# ---------------------------------------------------------------- salvar sozinho


def test_item_aparece_com_a_quantidade(pagina, agua):
    assert "Água (garrafa 1,5 L)" in textos(pagina)
    assert formatar_quantidade(agua) in textos(pagina)


def test_item_nao_mostra_o_preco(pagina, agua):
    assert formatar_reais(agua.custo) not in textos(pagina)


def test_total_diz_que_inclui_carnes_bebidas_e_carvao(pagina, plano):
    quanto = textos(cartao_com(pagina, "Quanto custa"))
    assert ["Total estimado", formatar_reais(plano.custo_total)] == \
        quanto[quanto.index("Total estimado"):quanto.index("Total estimado") + 2]
    assert {"Carnes e grelha vegetariana", "Bebidas", "Carvão e acessórios"} <= set(quanto)
    assert "Com carnes, bebidas e carvão. O \"Não esqueça\" fica fora da conta." in quanto


def test_descartaveis_aparecem_so_para_lembrar(pagina):
    assert {"Não esqueça", "Fora da conta: só para lembrar."} <= set(textos(pagina))


def test_cada_lembrete_aparece_no_nao_esqueca(pagina, plano):
    nao_esqueca = set(textos(cartao_com(pagina, "Não esqueça")))
    assert {i.produto.nome for i in plano.lembretes} <= nao_esqueca


def test_compartilhar_manda_a_lista_de_compras(app, pagina):
    # o Flet de mentira não tem compartilhar: a lista é copiada
    pagina.liberar_area_de_transferencia()
    clicar(achar(pagina, "Compartilhar lista"))
    assert pagina.copiado == [texto_compras(app.plano)]
    assert "Lista copiada! Cole no WhatsApp." in textos(pagina)


def test_sem_compartilhar_nem_copiar_mostra_a_lista_para_copiar(app, pagina):
    clicar(achar(pagina, "Compartilhar lista"))
    assert "Selecione o texto abaixo e copie." in textos(pagina)
    assert texto_compras(app.plano) in textos(pagina)


def test_cada_bebida_diz_quanto_e_indicado_por_pessoa(pagina, plano):
    bebidas = next(textos(c) for c in todos(pagina) if textos(c)[:1] == ["Bebidas"]
                   and len(textos(c)) > 2)
    indicados = [i.observacao for i in plano.compras.itens if i.produto.secao == "Bebidas"]
    assert "Cerveja (lata 350 ml)" in bebidas and len(indicados) == 4
    assert all(o.startswith("Indicado: ") and o in bebidas for o in indicados)


# ---------------------------------------------------------------- como pedir no açougue

def test_acougue_tem_a_dica_de_como_comprar_carne(pagina):
    assert DICA_DO_ACOUGUE in textos(cartao_com(pagina, "Açougue"))


def test_cada_carne_do_acougue_diz_como_pedir(pagina, plano):
    acougue = textos(cartao_com(pagina, "Açougue"))
    assert plano.compras.carnes
    for item in plano.compras.carnes:
        nome = acougue.index(item.produto.nome)
        assert acougue[nome + 1] == item.produto.como_pedir     # logo embaixo do nome


def test_dica_do_acougue_fica_so_no_cartao_do_acougue(pagina):
    assert textos(pagina).count(DICA_DO_ACOUGUE) == 1
