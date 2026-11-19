"""Dublês do Groq: respondem sem rede e guardam o que receberam."""
import json
from typing import Optional

from churrasco_facil.cliente_groq import ClienteGroq

CHAVE = "chave-secreta"


def resposta_groq(texto: str) -> str:
    """Corpo de uma resposta do Groq com o texto indicado."""
    return json.dumps({"choices": [{"message": {"content": texto}}]})


def resposta_ok(texto: str) -> tuple[int, dict, str]:
    """Resposta HTTP 200 do Groq com o texto indicado."""
    return 200, {}, resposta_groq(texto)


class TransporteFalso:
    """Devolve as respostas na ordem (repete a última) e guarda cada chamada."""

    def __init__(self, *respostas):
        self.respostas = list(respostas)
        self.chamadas = []

    def __call__(self, url, cabecalhos, corpo, timeout):
        self.chamadas.append({"url": url, "cabecalhos": dict(cabecalhos),
                              "corpo": json.loads(corpo), "timeout": timeout})
        resposta = self.respostas[min(len(self.chamadas), len(self.respostas)) - 1]
        if isinstance(resposta, Exception):
            raise resposta
        return resposta

    @property
    def mensagens(self) -> list[dict[str, str]]:
        """Mensagens enviadas na primeira chamada."""
        return self.chamadas[0]["corpo"]["messages"]


class DormirFalso:
    """Não espera de verdade: só anota quantos segundos o cliente pediu."""

    def __init__(self):
        self.esperas = []

    async def __call__(self, segundos):
        self.esperas.append(segundos)


def cliente_falso(*respostas, tentativas: int = 3, dormir: Optional[DormirFalso] = None
                  ) -> tuple[ClienteGroq, TransporteFalso]:
    """Cliente do Groq ligado a um transporte falso. Devolve os dois."""
    transporte = TransporteFalso(*respostas)
    cliente = ClienteGroq(CHAVE, transporte=transporte, tentativas=tentativas,
                          dormir=dormir or DormirFalso())
    return cliente, transporte
