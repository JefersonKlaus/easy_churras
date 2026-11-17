"""Chat de dúvidas: o "Mestre do Churrasco"."""
from __future__ import annotations

from typing import Optional

from .cliente_groq import ClienteGroq, ErroGroq
from .esquemas import limpar_texto_livre
from .modo_offline import ConversaLocal
from .prompts import mensagens_conversa

MAX_TURNOS = 6          # quantas trocas de mensagem lembrar
MAX_PERGUNTA = 500


class Conversa:
    """Guarda um histórico curto e responde dúvidas com o plano como contexto."""

    def __init__(self, cliente: ClienteGroq, resumo_plano: str,
                 reserva: Optional[ConversaLocal] = None) -> None:
        self.cliente = cliente
        self.resumo_plano = resumo_plano
        self.reserva = reserva          # usada quando o Groq não responde
        self.offline = False            # a última resposta veio da reserva?
        self.historico: list[dict[str, str]] = []

    async def perguntar(self, pergunta: str) -> str:
        pergunta = pergunta.strip()[:MAX_PERGUNTA]
        if not pergunta:
            raise ValueError("escreva a sua dúvida")
        mensagens = mensagens_conversa(self.resumo_plano, self.historico, pergunta)
        self.offline = False
        try:
            resposta = limpar_texto_livre(
                await self.cliente.conversar(mensagens, temperatura=0.5, max_tokens=350))
        except ErroGroq:
            if self.reserva is None:
                raise
            self.offline = True
            resposta = await self.reserva.perguntar(pergunta)
        self.historico.append({"role": "user", "content": pergunta})
        self.historico.append({"role": "assistant", "content": resposta})
        del self.historico[:-2 * MAX_TURNOS]
        return resposta

    def limpar(self) -> None:
        self.historico.clear()
