"""Fixtures do domínio usadas por vários módulos de teste."""
import pytest

from churrasco_facil.calculadora import Convidados
from churrasco_facil.planejador import Pedido, montar_plano
from dados import SERVIR


@pytest.fixture
def convidados():
    return Convidados(adultos=10, criancas=3, vegetarianos=1, bebem_alcool=6, duracao_horas=5)


@pytest.fixture
def pedido(convidados):
    """Pedido com orçamento de R$ 600,00."""
    return Pedido(convidados, SERVIR, 60000, nome="Teste")


@pytest.fixture
def plano(pedido):
    return montar_plano(pedido)
