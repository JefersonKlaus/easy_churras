"""A parte do app que usa o Groq: entender o pedido escrito livremente. Todo resultado é
validado antes de ser usado."""
from __future__ import annotations

from .cliente_groq import ClienteGroq, ErroResposta
from .esquemas import ErroEsquema, PedidoInterpretado, interpretar_pedido
from .prompts import mensagens_pedido

TENTATIVAS_DE_FORMATO = 2   # se o JSON vier inválido, tenta uma segunda vez


class Assistente:
    """Usa o Groq para entender quem vem ao churrasco a partir de um texto livre."""

    def __init__(self, cliente: ClienteGroq) -> None:
        self.cliente = cliente

    async def interpretar_pedido(self, texto: str) -> PedidoInterpretado:
        """Entende um pedido em texto livre ("churrasco pra 12, 3 crianças..."). Se o JSON
        vier com a forma errada, pede de novo uma vez."""
        if not texto.strip():
            raise ValueError("escreva alguma coisa para eu entender")
        mensagens = mensagens_pedido(texto)
        for _tentativa in range(TENTATIVAS_DE_FORMATO):
            resposta = await self.cliente.conversar(mensagens, json_obrigatorio=True,
                                                    temperatura=0.1, max_tokens=400)
            try:
                return interpretar_pedido(resposta)
            except ErroEsquema:
                pass
        raise ErroResposta("formato inválido depois de duas tentativas")
