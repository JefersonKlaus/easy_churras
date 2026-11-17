"""Chat de dúvidas: o "Mestre do Churrasco"."""
from __future__ import annotations

from .cliente_groq import ClienteGroq
from .esquemas import limpar_texto_livre
from .prompts import mensagens_conversa

MAX_TURNOS = 6          # quantas trocas de mensagem lembrar
MAX_PERGUNTA = 500


class Conversa:
    """Guarda um histórico curto e responde dúvidas com o plano como contexto."""

    def __init__(self, cliente: ClienteGroq, resumo_plano: str) -> None:
        self.cliente = cliente
        self.resumo_plano = resumo_plano
        self.historico: list[dict[str, str]] = []

    async def perguntar(self, pergunta: str) -> str:
        pergunta = pergunta.strip()[:MAX_PERGUNTA]
        if not pergunta:
            raise ValueError("escreva a sua dúvida")
        mensagens = mensagens_conversa(self.resumo_plano, self.historico, pergunta)
        resposta = limpar_texto_livre(
            await self.cliente.conversar(mensagens, temperatura=0.5, max_tokens=350))
        self.historico.append({"role": "user", "content": pergunta})
        self.historico.append({"role": "assistant", "content": resposta})
        del self.historico[:-2 * MAX_TURNOS]
        return resposta

    def limpar(self) -> None:
        self.historico.clear()
