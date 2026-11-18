"""Aba Carnes: o que vai na grelha, o total, salvar e compartilhar."""
import pytest

from churrasco_facil.catalogo_carnes import Corte
from churrasco_facil.dinheiro import formatar_reais
from churrasco_facil.lista_compras import formatar_quantidade
from tela import achar, clicar, tem_texto, textos, tocar

pytestmark = pytest.mark.usefixtures("plano_aberto")


@pytest.fixture
def carne(plano):
    """O primeiro item que vai para a grelha."""
    return next(i for i in plano.compras.itens if isinstance(i.produto, Corte))


# ---------------------------------------------------------------- carnes e dicas

def test_carne_aparece_com_a_quantidade(pagina, carne):
    assert carne.produto.nome in textos(pagina)
    assert formatar_quantidade(carne) in textos(pagina)


def test_diz_que_da_para_tocar_para_ver_as_dicas(pagina):
    assert "Toque em uma carne para ver as dicas." in textos(pagina)


def test_dicas_ficam_escondidas_ate_tocar(pagina, carne):
    assert carne.produto.dica not in textos(pagina)


def test_tocar_na_carne_mostra_as_dicas(pagina, carne):
    tocar(pagina, carne.produto.nome)
    assert carne.produto.dica in textos(pagina)


def test_tocar_de_novo_esconde_as_dicas(pagina, carne):
    tocar(pagina, carne.produto.nome)
    tocar(pagina, carne.produto.nome)
    assert carne.produto.dica not in textos(pagina)


def test_mostra_o_total_e_o_valor_por_pessoa(pagina, plano):
    assert tem_texto(pagina, f"Total do churrasco: {formatar_reais(plano.custo_total)} "
                             f"({formatar_reais(plano.custo_por_pessoa)} por pessoa)")


# ---------------------------------------------------------------- um assunto só

@pytest.mark.parametrize("de_outra_aba", ["Nunca use a churrasqueira em lugar fechado",
                                          "Explicar o meu plano", "Acender o carvão",
                                          "Copiar lista", "Não esqueça"])
def test_nao_mostra_o_que_e_de_outra_aba(pagina, de_outra_aba):
    assert de_outra_aba not in textos(pagina)


# ---------------------------------------------------------------- compartilhar

def test_compartilhar_e_um_botao_grande(pagina):
    assert achar(pagina, "Compartilhar").height == 56


def test_nao_tem_botao_salvar(pagina):
    assert "Salvar" not in textos(pagina)


def test_abrir_as_carnes_nao_salva_o_plano(app):
    assert app.banco.listar() == []


def test_compartilhar_copia_o_texto_quando_da(pagina):
    pagina.liberar_area_de_transferencia()
    clicar(achar(pagina, "Compartilhar"))
    assert pagina.copiado[0].startswith("*Teste*")
    assert "Texto copiado! Cole no WhatsApp." in textos(pagina)


def test_compartilhar_sem_area_de_transferencia_pede_copia_manual(pagina):
    clicar(achar(pagina, "Compartilhar"))
    assert "Selecione o texto abaixo e copie." in textos(pagina)
