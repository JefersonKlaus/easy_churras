import json
from datetime import datetime

import pytest

from churrasco_facil.calculadora import Convidados
from churrasco_facil.planejador import Pedido

SERVIR = datetime(2026, 11, 21, 14, 0)


@pytest.fixture
def convidados():
    return Convidados(adultos=10, criancas=3, vegetarianos=1, bebem_alcool=6, duracao_horas=5)


@pytest.fixture
def pedido(convidados):
    return Pedido(convidados, SERVIR, 60000, nome="Teste")


def resposta_groq(texto: str) -> str:
    """Corpo de uma resposta 200 do Groq com o texto indicado."""
    return json.dumps({"choices": [{"message": {"content": texto}}]})


class TransporteFalso:
    """Transporte que devolve respostas pré-definidas, na ordem, e guarda o que recebeu."""

    def __init__(self, *respostas):
        self.respostas = list(respostas)
        self.chamadas = []

    def __call__(self, url, cabecalhos, corpo, timeout):
        self.chamadas.append({"url": url, "cabecalhos": dict(cabecalhos),
                              "corpo": json.loads(corpo), "timeout": timeout})
        indice = min(len(self.chamadas) - 1, len(self.respostas) - 1)
        resposta = self.respostas[indice]
        if isinstance(resposta, Exception):
            raise resposta
        return resposta


async def sem_espera(_segundos):
    return None
