"""Modo offline: entende o pedido escrito livremente sem internet e sem chave do Groq.

Serve de reserva quando a internet cai ou a chave falha. Cada módulo cuida de uma coisa só:

- `texto`: deixar o texto digitado pronto para comparar.
- `pedido`: ler um pedido escrito livremente ("12 pessoas, 3 crianças...").
- `assistente_local`: o assistente sem rede, com o mesmo método do `Assistente`.
- `reserva`: usar o assistente local quando o Groq falha.
"""
from .assistente_local import AssistenteLocal
from .pedido import interpretar_pedido_local
from .reserva import AssistenteComReserva
from .texto import normalizar

__all__ = ["AssistenteComReserva", "AssistenteLocal", "interpretar_pedido_local", "normalizar"]
