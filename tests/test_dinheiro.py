import pytest

from churrasco_facil.dinheiro import (custo_proporcional, formatar_reais, reais_para_centavos,
                                      valor_para_campo)


@pytest.mark.parametrize("texto, centavos", [
    ("12,50", 1250), ("R$ 1.234,56", 123456), ("12.5", 1250), ("1.234.567", 123456700),
    ("  7 ", 700), ("0,05", 5), ("0", 0),
])
def test_reais_para_centavos(texto, centavos):
    assert reais_para_centavos(texto) == centavos


@pytest.mark.parametrize("texto", ["", "   ", "abc", "-5", "1,2,3", "nan", "inf"])
def test_reais_para_centavos_recusa_valor_invalido(texto):
    with pytest.raises(ValueError):
        reais_para_centavos(texto)


@pytest.mark.parametrize("centavos, texto", [
    (123456, "R$ 1.234,56"), (5, "R$ 0,05"), (0, "R$ 0,00"), (-250, "-R$ 2,50"),
    (100000000, "R$ 1.000.000,00"),
])
def test_formatar_reais(centavos, texto):
    assert formatar_reais(centavos) == texto


@pytest.mark.parametrize("centavos, texto", [(9500, "95,00"), (5, "0,05"), (123456, "1234,56")])
def test_valor_para_campo(centavos, texto):
    assert valor_para_campo(centavos) == texto


@pytest.mark.parametrize("centavos", [0, 5, 9500, 123456])
def test_valor_para_campo_volta_igual_pela_leitura(centavos):
    assert reais_para_centavos(valor_para_campo(centavos)) == centavos


@pytest.mark.parametrize("preco, por, quantidade, custo", [
    (9000, 1000, 250, 2250),
    (1, 2, 1, 1),            # 0,5 sobe
    (1, 3, 1, 0),            # 0,33 desce
    (400, 1, 3, 1200),
])
def test_custo_proporcional_arredonda_a_metade_para_cima(preco, por, quantidade, custo):
    assert custo_proporcional(preco, por, quantidade) == custo


def test_custo_proporcional_exige_quantidade_de_referencia_positiva():
    with pytest.raises(ValueError):
        custo_proporcional(1, 0, 1)
