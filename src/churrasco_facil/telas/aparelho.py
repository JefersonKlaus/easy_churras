"""O que o app usa do aparelho: área de transferência, compartilhar e a tela em pé.

As APIs mudam entre versões do Flet; aqui ficam as tentativas e o que fazer quando o aparelho
não tem o recurso, para as telas só pedirem "copie" ou "compartilhe".
"""
from __future__ import annotations

import inspect
import logging
from typing import Any

import flet as ft

logger = logging.getLogger(__name__)

# O que aconteceu ao compartilhar: abriu o compartilhar do aparelho, ou só deu para copiar.
COMPARTILHADO, COPIADO = "compartilhado", "copiado"


class Aparelho:
    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self._servicos: dict[str, Any] = {}    # serviços do Flet 1.0, criados uma vez só

    async def copiar(self, texto: str) -> bool:
        """Copia para a área de transferência. Tenta as formas conhecidas (cada versão do Flet
        tem a sua) e devolve False se nenhuma funcionar."""
        formas = [lambda: self._servico("copiar", ft.Clipboard).set(texto)]   # Flet 1.0
        if hasattr(self.page, "set_clipboard"):
            formas.append(lambda: self.page.set_clipboard(texto))
        area = getattr(self.page, "clipboard", None)
        if area is not None and hasattr(area, "set"):
            formas.append(lambda: area.set(texto))
        for forma in formas:
            try:
                resultado: Any = forma()
                if inspect.isawaitable(resultado):
                    await resultado
                return True
            except Exception:  # a API de cada versão do Flet falha de um jeito diferente
                logger.debug("forma de copiar falhou", exc_info=True)
        return False

    async def compartilhar(self, texto: str, titulo: str) -> str:
        """Abre o compartilhar do aparelho (WhatsApp, e-mail...). Onde não há (ex.: navegador
        de computador), copia o texto. Devolve COMPARTILHADO, COPIADO ou "" (nada deu certo:
        a tela mostra o texto para a pessoa copiar)."""
        try:
            await self._servico("compartilhar", ft.Share).share_text(
                texto, title=titulo, subject=titulo, download_fallback_enabled=False,
                mail_to_fallback_enabled=False)
            return COMPARTILHADO
        except Exception:  # sem compartilhar neste aparelho ou nesta versão do Flet
            logger.debug("compartilhar não funcionou; tentando copiar", exc_info=True)
        return COPIADO if await self.copiar(texto) else ""

    async def travar_em_retrato(self) -> None:
        """No celular, o app fica sempre em pé (retrato). No computador e na web o Flet não
        deixa travar: lá a janela já abre em pé (430 x 900)."""
        plataforma = getattr(self.page, "platform", None)
        if plataforma is None or not plataforma.is_mobile():
            return
        try:
            await self.page.set_allowed_device_orientations([ft.DeviceOrientation.PORTRAIT_UP])
        except Exception:  # versão do Flet ou aparelho sem suporte: segue sem travar
            logger.debug("não consegui travar a tela em retrato", exc_info=True)

    def _servico(self, nome: str, fabrica: Any) -> Any:
        """No Flet 1.0 a área de transferência e o compartilhar são serviços: cada um é
        criado uma vez só."""
        if nome not in self._servicos:
            self._servicos[nome] = fabrica()
        return self._servicos[nome]
