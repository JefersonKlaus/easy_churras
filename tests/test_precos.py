"""Os preços que a pessoa confere: quais aparecem e como o que ela digita é guardado."""
import pytest

from churrasco_facil.catalogo_itens import ITENS
from churrasco_facil.precos import grupos_de_precos, juntar_precos
from churrasco_facil.produtos import SECOES_LEMBRETE


def test_juntar_precos_mantem_os_outros_precos_salvos():
    assert juntar_precos({"pao_alho": 450}, {"picanha": "95,00"}) == \
        {"pao_alho": 450, "picanha": 9500}


def test_preco_igual_ao_do_catalogo_nao_e_guardado():
    assert juntar_precos({}, {"picanha": "90,00"}) == {}


def test_voltar_ao_preco_do_catalogo_apaga_o_personalizado():
    assert juntar_precos({"picanha": 9500}, {"picanha": "90,00"}) == {}


@pytest.mark.parametrize("texto", ["caro", "-3", "99999999"])
def test_preco_invalido_levanta_valueerror_com_o_nome_do_produto(texto):
    with pytest.raises(ValueError, match="Picanha"):
        juntar_precos({}, {"picanha": texto})


def test_grupos_de_precos_comecam_pelas_carnes_e_pelo_vegetariano():
    assert [nome for nome, _ in grupos_de_precos()][:2] == ["Carnes", "Vegetariano"]


def test_todo_item_com_preco_aparece_uma_vez():
    # também garante que pão de alho, mercearia e descartáveis (só lembrete) não pedem preço
    ids = [p.id for _, produtos in grupos_de_precos()[2:] for p in produtos]
    assert sorted(ids) == sorted(i for i, p in ITENS.items() if p.secao not in SECOES_LEMBRETE)
