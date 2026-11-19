"""Reserva automática: tenta o Groq e, se a internet ou a chave falharem, usa o local."""
from __future__ import annotations

from typing import Optional

from ..cliente_groq import ErroGroq
from ..esquemas import PedidoInterpretado
from .assistente_local import AssistenteLocal


class AssistenteComReserva:
    """Tenta o Groq; se a internet ou a chave falharem, usa o assistente local.

    Depois de cada chamada, `aviso` diz se foi preciso usar a reserva.
    """

    def __init__(self, principal, reserva: Optional[AssistenteLocal] = None) -> None:
        self.principal = principal
        self.reserva = reserva or AssistenteLocal()
        self.aviso = ""

    async def interpretar_pedido(self, texto: str) -> PedidoInterpretado:
        self.aviso = ""
        try:
            return await self.principal.interpretar_pedido(texto)
        except ErroGroq as erro:
            self.aviso = f"{erro.mensagem_usuario} Usei o modo offline."
            return await self.reserva.interpretar_pedido(texto)
