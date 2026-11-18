"""Dados de teste reutilizáveis (sem fixtures: estas ficam no conftest)."""
from datetime import datetime
from typing import Optional

from churrasco_facil.calculadora import Convidados
from churrasco_facil.planejador import Pedido, Plano, montar_plano

SERVIR = datetime(2026, 11, 21, 14, 0)      # um sábado


def plano_para(adultos: int = 10, criancas: int = 3, orcamento: Optional[int] = None) -> Plano:
    """Plano de um grupo simples, sem vegetarianos."""
    pedido = Pedido(Convidados(adultos=adultos, criancas=criancas), SERVIR, orcamento, nome="T")
    return montar_plano(pedido)
