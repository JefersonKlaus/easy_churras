"""A tabela de quantidades por pessoa, lida de um dicionário salvo."""
import pytest

from churrasco_facil.parametros import Parametros


def test_parametros_de_dicionario_aceita_valor_valido():
    assert Parametros.de_dicionario({"carne_adulto_g": 500}).carne_adulto_g == 500


@pytest.mark.parametrize("campo, valor", [
    ("carne_crianca_g", "x"), ("arroz_g_por_pessoa", -5), ("carne_adulto_g", True),
])
def test_parametros_de_dicionario_ignora_valor_invalido(campo, valor):
    assert Parametros.de_dicionario({campo: valor}) == Parametros()


def test_parametros_de_dicionario_converte_para_o_tipo_do_campo():
    assert Parametros.de_dicionario({"pao_alho_por_pessoa": 2}).pao_alho_por_pessoa == 2.0


def test_parametros_de_dicionario_sem_dados_usa_o_padrao():
    assert Parametros.de_dicionario(None) == Parametros()
