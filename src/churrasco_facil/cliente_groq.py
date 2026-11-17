"""Cliente do Groq (API compatível com a da OpenAI), com tentativas e erros claros.

Usa só a biblioteca padrão do Python (urllib), então não exige nenhum pacote extra e fica
fácil de instalar em máquina sem internet.
"""
from __future__ import annotations

import asyncio
import json
import socket
import urllib.error
import urllib.request
from typing import Any, Awaitable, Callable, Mapping, Optional

URL_PADRAO = "https://api.groq.com/openai/v1/chat/completions"
# Confira a lista atual de modelos na documentação do Groq: eles mudam com o tempo.
MODELO_PADRAO = "llama-3.3-70b-versatile"
ESPERA_MAXIMA_S = 20.0


class ErroGroq(Exception):
    """Erro base. `mensagem_usuario` é um texto simples para mostrar na tela."""

    mensagem_usuario = "Não consegui falar com a IA agora. Tente de novo mais tarde."

    def __init__(self, detalhe: str = "") -> None:
        super().__init__(detalhe or self.mensagem_usuario)


class ErroSemChave(ErroGroq):
    mensagem_usuario = "Falta a chave do Groq. Coloque-a em Configurações."


class ErroAutenticacao(ErroGroq):
    mensagem_usuario = "O Groq recusou a chave. Confira se ela está correta."


class ErroLimiteUso(ErroGroq):
    mensagem_usuario = "Muitos pedidos ao Groq. Espere um pouco e tente de novo."


class ErroModelo(ErroGroq):
    mensagem_usuario = "O modelo do Groq não existe mais. Troque o modelo em Configurações."


class ErroRede(ErroGroq):
    mensagem_usuario = "Sem conexão com o Groq. O resto do app continua funcionando."


class ErroResposta(ErroGroq):
    mensagem_usuario = "O Groq respondeu algo que não consegui entender."


# Um transporte recebe (url, cabeçalhos, corpo em bytes, timeout) e devolve
# (código HTTP, cabeçalhos em minúsculas, texto do corpo). Falha de rede levanta OSError.
Transporte = Callable[[str, Mapping[str, str], bytes, float], tuple[int, dict[str, str], str]]
Dormir = Callable[[float], Awaitable[None]]


def transporte_urllib(url: str, cabecalhos: Mapping[str, str], corpo: bytes,
                      timeout: float) -> tuple[int, dict[str, str], str]:
    """Transporte padrão, com urllib."""
    pedido = urllib.request.Request(url, data=corpo, headers=dict(cabecalhos), method="POST")
    try:
        with urllib.request.urlopen(pedido, timeout=timeout) as resposta:
            texto = resposta.read().decode("utf-8", errors="replace")
            return resposta.status, {k.lower(): v for k, v in resposta.headers.items()}, texto
    except urllib.error.HTTPError as erro:  # códigos 4xx/5xx chegam aqui
        texto = erro.read().decode("utf-8", errors="replace")
        return erro.code, {k.lower(): v for k, v in erro.headers.items()}, texto
    except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError) as erro:
        raise OSError(str(erro)) from None


class ClienteGroq:
    """Faz chamadas ao Groq. `transporte` e `dormir` permitem testar sem rede."""

    def __init__(self, chave: Optional[str], modelo: str = MODELO_PADRAO,
                 timeout: float = 30.0, tentativas: int = 3, espera_base: float = 1.0,
                 transporte: Transporte = transporte_urllib,
                 dormir: Dormir = asyncio.sleep, url: str = URL_PADRAO) -> None:
        self.chave = (chave or "").strip()
        self.modelo = modelo
        self.timeout = timeout
        self.tentativas = max(1, tentativas)
        self.espera_base = espera_base
        self.transporte = transporte
        self.dormir = dormir
        self.url = url

    @property
    def configurado(self) -> bool:
        return bool(self.chave)

    def _corpo(self, mensagens: list[dict[str, str]], json_obrigatorio: bool,
               temperatura: float, max_tokens: int) -> bytes:
        corpo: dict[str, Any] = {"model": self.modelo, "messages": mensagens,
                                 "temperature": temperatura,
                                 "max_completion_tokens": max_tokens}
        if json_obrigatorio:
            corpo["response_format"] = {"type": "json_object"}
        return json.dumps(corpo, ensure_ascii=False).encode("utf-8")

    def _espera(self, tentativa: int, cabecalhos: Optional[Mapping[str, str]]) -> float:
        if cabecalhos is not None:
            try:
                pedida = float(cabecalhos.get("retry-after", ""))
                return min(max(pedida, 0.0), ESPERA_MAXIMA_S)
            except ValueError:
                pass
        return min(self.espera_base * (2 ** tentativa), ESPERA_MAXIMA_S)

    async def conversar(self, mensagens: list[dict[str, str]], *, json_obrigatorio: bool = False,
                        temperatura: float = 0.4, max_tokens: int = 800) -> str:
        """Envia a conversa e devolve o texto da resposta. Levanta um `ErroGroq` se falhar."""
        if not self.configurado:
            raise ErroSemChave()
        corpo = self._corpo(mensagens, json_obrigatorio, temperatura, max_tokens)
        cabecalhos = {"Authorization": f"Bearer {self.chave}",
                      "Content-Type": "application/json"}
        ultimo_erro: ErroGroq = ErroRede()
        for tentativa in range(self.tentativas):
            resposta_cab: Optional[dict[str, str]] = None
            try:
                codigo, resposta_cab, texto = await asyncio.to_thread(
                    self.transporte, self.url, cabecalhos, corpo, self.timeout)
            except OSError:
                ultimo_erro = ErroRede()
            else:
                if codigo == 200:
                    return self._ler_texto(texto)
                if codigo in (401, 403):
                    raise ErroAutenticacao()
                if codigo == 404 or (codigo == 400 and "model" in texto.lower()):
                    raise ErroModelo(f"HTTP {codigo}")
                if codigo == 429:
                    ultimo_erro = ErroLimiteUso()
                elif codigo >= 500:
                    ultimo_erro = ErroGroq(f"servidor do Groq indisponível (HTTP {codigo})")
                else:
                    raise ErroResposta(f"HTTP {codigo}")
            if tentativa < self.tentativas - 1:
                await self.dormir(self._espera(tentativa, resposta_cab))
        raise ultimo_erro

    @staticmethod
    def _ler_texto(corpo: str) -> str:
        try:
            texto = json.loads(corpo)["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError):
            raise ErroResposta("formato inesperado") from None
        if not isinstance(texto, str) or not texto.strip():
            raise ErroResposta("resposta vazia")
        return texto
