"""Aba Compras: o que comprar, por seção do mercado."""
import pytest

from churrasco_facil.dinheiro import formatar_reais
from churrasco_facil.lista_compras import formatar_quantidade
from tela import achar, clicar, textos, todos

pytestmark = pytest.mark.usefixtures("lista_aberta")


@pytest.fixture
def lista_aberta(app, plano_aberto):
    app.ir_lista()


def cartao_com(pagina, titulo):
    """O menor bloco da tela que tem o título e mais alguma coisa."""
    return [c for c in todos(pagina) if titulo in textos(c) and len(textos(c)) > 1][-1]


@pytest.fixture
def pao_de_alho(plano):
    return next(i for i in plano.compras.itens if i.produto.id == "pao_alho")


@pytest.mark.parametrize("secao", ["Açougue", "Hortifruti", "Bebidas", "Carvão e acessórios"])
def test_lista_agrupa_por_secao(pagina, secao):
    assert secao in textos(pagina)


def test_mercearia_nao_e_uma_secao_da_conta(pagina):
    assert "Mercearia" not in textos(pagina)


# ---------------------------------------------------------------- salvar sozinho

def test_abrir_as_compras_salva_o_plano(app):
    assert len(app.banco.listar()) == 1 and app.plano_id is not None


def test_abrir_as_compras_avisa_que_salvou(pagina):
    assert "Plano salvo em Meus churrascos." in textos(pagina)


def test_voltar_as_compras_nao_salva_de_novo_nem_avisa(app, pagina):
    app.ir_lista()
    assert len(app.banco.listar()) == 1
    assert "Plano salvo em Meus churrascos." not in textos(pagina)


def test_item_aparece_com_a_quantidade(pagina, pao_de_alho):
    assert "Pão de alho" in textos(pagina) and formatar_quantidade(pao_de_alho) in textos(pagina)


def test_item_nao_mostra_o_preco(pagina, pao_de_alho):
    assert formatar_reais(pao_de_alho.custo) not in textos(pagina)


def test_lista_mostra_o_total(pagina, plano):
    assert f"Total estimado: {formatar_reais(plano.custo_total)}" in textos(pagina)


def test_descartaveis_aparecem_so_para_lembrar(pagina):
    assert "Não esqueça" in textos(pagina) and "Fora da conta: só para lembrar." in textos(pagina)


@pytest.mark.parametrize("nome", ["Arroz (pacote 1 kg)", "Sal grosso (pacote 1 kg)",
                                  "Copos descartáveis (pacote 50)", "Guardanapos (pacote 50)",
                                  "Pratos descartáveis (pacote 10)"])
def test_cada_descartavel_aparece_no_lembrete(pagina, nome):
    assert nome in textos(cartao_com(pagina, "Não esqueça"))


def test_copiar_lista_quando_da(pagina):
    pagina.liberar_area_de_transferencia()
    clicar(achar(pagina, "Copiar lista"))
    assert "Lista copiada!" in textos(pagina)


def test_lista_copiada_lembra_da_mercearia_e_dos_descartaveis(pagina):
    pagina.liberar_area_de_transferencia()
    clicar(achar(pagina, "Copiar lista"))
    lembrete = pagina.copiado[0].split("NÃO ESQUEÇA (fora da conta)")[1]
    assert "- Sal grosso" in lembrete and "- Copos descartáveis" in lembrete


def test_copiar_lista_sem_area_de_transferencia_avisa(pagina):
    clicar(achar(pagina, "Copiar lista"))
    assert "Não consegui copiar neste aparelho." in textos(pagina)
