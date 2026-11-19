"""O assistente local: o mesmo método do `Assistente` com IA, sem rede."""
from __future__ import annotations

from ..esquemas import PedidoInterpretado
from .pedido import interpretar_pedido_local


class AssistenteLocal:
    """Entende o pedido escrito livremente, como o `Assistente`, mas sem rede."""

    aviso = ""

    async def interpretar_pedido(self, texto: str) -> PedidoInterpretado:
        if not texto.strip():
            raise ValueError("escreva alguma coisa para eu entender")
        return interpretar_pedido_local(texto)
