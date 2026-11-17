import pytest

from churrasco_facil.dinheiro import (custo_proporcional, dividir_centavos, formatar_reais,
                                      reais_para_centavos)


@pytest.mark.parametrize("texto, centavos", [
    ("12,50", 1250), ("R$ 1.234,56", 123456), ("12.5", 1250), ("1.234.567", 123456700),
    ("  7 ", 700), ("0,05", 5), ("0", 0),
])
def test_reais_para_centavos(texto, centavos):
    assert reais_para_centavos(texto) == centavos


@pytest.mark.parametrize("texto", ["", "   ", "abc", "-5", "1,2,3", "nan", "inf"])
def test_valores_invalidos(texto):
    with pytest.raises(ValueError):
        reais_para_centavos(texto)


def test_formatar_reais():
    assert formatar_reais(123456) == "R$ 1.234,56"
    assert formatar_reais(5) == "R$ 0,05"
    assert formatar_reais(0) == "R$ 0,00"
    assert formatar_reais(-250) == "-R$ 2,50"
    assert formatar_reais(100000000) == "R$ 1.000.000,00"


def test_dividir_centavos_nao_perde_nem_cria_centavo():
    assert dividir_centavos(100, 3) == [34, 33, 33]
    assert dividir_centavos(0, 4) == [0, 0, 0, 0]
    for total in (1, 99, 10001):
        for partes in (1, 2, 7):
            assert sum(dividir_centavos(total, partes)) == total
    with pytest.raises(ValueError):
        dividir_centavos(100, 0)


def test_custo_proporcional_arredonda_a_metade_para_cima():
    assert custo_proporcional(9000, 1000, 250) == 2250
    assert custo_proporcional(1, 2, 1) == 1        # 0,5 sobe
    assert custo_proporcional(1, 3, 1) == 0        # 0,33 desce
    assert custo_proporcional(400, 1, 3) == 1200
    with pytest.raises(ValueError):
        custo_proporcional(1, 0, 1)
