"""Partes do app que usam o Groq. Todo resultado é validado antes de ser usado."""
from __future__ import annotations

from typing import Optional

from .calculadora import Convidados
from .catalogo_carnes import CORTES
from .cliente_groq import ClienteGroq, ErroResposta
from .esquemas import (ErroEsquema, PedidoInterpretado, Sugestao, interpretar_pedido,
                       interpretar_sugestoes, limpar_texto_livre)
from .planejador import Plano, resumo_pedido, resumo_plano
from .prompts import mensagens_cortes, mensagens_explicacao, mensagens_pedido

TENTATIVAS_DE_FORMATO = 2   # se o JSON vier inválido, tenta uma segunda vez


class Assistente:
    """Usa o Groq para entender pedidos, sugerir cortes e explicar o plano."""

    def __init__(self, cliente: ClienteGroq) -> None:
        self.cliente = cliente

    async def _json(self, mensagens: list[dict[str, str]], interpretar, max_tokens: int):
        """Pede JSON e valida. Se a forma estiver errada, tenta de novo uma vez."""
        for tentativa in range(TENTATIVAS_DE_FORMATO):
            texto = await self.cliente.conversar(mensagens, json_obrigatorio=True,
                                                 temperatura=0.1, max_tokens=max_tokens)
            try:
                return interpretar(texto)
            except ErroEsquema:
                if tentativa == TENTATIVAS_DE_FORMATO - 1:
                    raise ErroResposta("formato inválido depois de duas tentativas") from None
        raise ErroResposta("sem resposta")  # nunca chega aqui; deixa o tipo claro

    async def interpretar_pedido(self, texto: str) -> PedidoInterpretado:
        """Entende um pedido em texto livre ("churrasco pra 12, 3 crianças...")."""
        if not texto.strip():
            raise ValueError("escreva alguma coisa para eu entender")
        return await self._json(mensagens_pedido(texto), interpretar_pedido, 400)

    async def sugerir_cortes(self, conv: Convidados, orcamento: Optional[int]) -> list[Sugestao]:
        """Sugere cortes do catálogo para o grupo. O código descarta ids inventados."""
        return await self._json(mensagens_cortes(resumo_pedido(conv, orcamento)),
                                interpretar_sugestoes, 600)

    async def explicar(self, plano: Plano) -> str:
        """Texto curto e amigável sobre o plano."""
        texto = await self.cliente.conversar(mensagens_explicacao(resumo_plano(plano)),
                                             temperatura=0.5, max_tokens=350)
        limpo = limpar_texto_livre(texto)
        if not limpo:
            raise ErroResposta("explicação vazia")
        return limpo


def pesos_das_sugestoes(sugestoes: list[Sugestao]) -> dict[str, int]:
    """Transforma sugestões em pesos usando a importância padrão de cada corte."""
    return {s.id: CORTES[s.id].peso_padrao for s in sugestoes if s.id in CORTES}
