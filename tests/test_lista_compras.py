import pytest

from churrasco_facil.catalogo_carnes import CORTES
from churrasco_facil.lista_compras import agrupar_por_secao, formatar_quantidade, linha_do_item
from churrasco_facil.produtos import ItemPlano, Produto

PAO_DE_ALHO = ItemPlano(Produto("p", "Pão de alho", "Padaria", "un", 400, 1), 3, "para todos")


def item(unidade="un", quantidade=1, nome="X", secao="Mercearia"):
    return ItemPlano(Produto("x", nome, secao, unidade, 100, 1), quantidade)


@pytest.mark.parametrize("unidade, quantidade, texto", [
    ("g", 950, "950 g"), ("g", 1000, "1 kg"), ("g", 1200, "1,2 kg"), ("g", 1450, "1,45 kg"),
    ("ml", 500, "500 ml"), ("ml", 1500, "1,5 L"), ("un", 3, "3 un"),
])
def test_formatar_quantidade(unidade, quantidade, texto):
    assert formatar_quantidade(item(unidade, quantidade)) == texto


@pytest.mark.parametrize("id, gramas, texto", [
    ("picanha", 2400, "2 peças · 2,4 kg"), ("linguica_toscana", 1000, "1 pacote · 1 kg"),
    ("contrafile", 800, "2 bifes · 800 g"),
])
def test_corte_e_contado_em_pecas_com_o_peso_total(id, gramas, texto):
    assert formatar_quantidade(ItemPlano(CORTES[id], gramas)) == texto


def test_agrupar_segue_a_ordem_do_mercado_e_deixa_secoes_novas_no_fim():
    itens = [item(secao="Seção nova"), item(secao="Bebidas"), item(secao="Açougue")]
    assert list(agrupar_por_secao(itens)) == ["Açougue", "Bebidas", "Seção nova"]


def test_agrupar_ordena_os_itens_por_nome():
    itens = [item(nome="Bife", secao="Açougue"), item(nome="Alcatra", secao="Açougue")]
    grupo = agrupar_por_secao(itens)["Açougue"]
    assert [i.produto.nome for i in grupo] == ["Alcatra", "Bife"]


def test_linha_do_item_com_preco():
    assert linha_do_item(PAO_DE_ALHO) == "Pão de alho: 3 un (para todos) - R$ 12,00"
