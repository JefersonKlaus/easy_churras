"""O aplicativo: guarda o estado e leva o usuário de uma tela para outra."""
from __future__ import annotations

import inspect
import logging
from typing import Any, Optional, Union

import flet as ft

from .armazenamento import Armazenamento
from .calculadora import Parametros
from .assistente import Assistente
from .cliente_groq import ClienteGroq
from .modo_offline import AssistenteComReserva, AssistenteLocal, ConversaLocal
from .configuracao import (Configuracao, carregar_configuracao, cliente_da_configuracao,
                           parametros_da_configuracao)
from .conversa import Conversa
from .entradas import Rascunho
from .planejador import Plano, montar_plano, resumo_plano
from .telas import assistente_passos, configuracoes, conversa, cronograma, inicio, lista, plano

logger = logging.getLogger(__name__)


class AppChurrasco:
    """Estado compartilhado entre as telas."""

    def __init__(self, page: ft.Page, banco: Optional[Armazenamento] = None,
                 config: Optional[Configuracao] = None) -> None:
        self.page = page
        self.config = config if config is not None else carregar_configuracao()
        self.banco = banco if banco is not None else Armazenamento()
        self.rascunho = Rascunho()
        self.plano: Optional[Plano] = None
        self.plano_id: Optional[int] = None
        self.motivos: dict[str, str] = {}      # por que o Groq sugeriu cada corte
        self.aviso: str = ""                   # recado para a próxima tela (ex.: sem IA)
        self.conversa: Optional[Union[Conversa, ConversaLocal]] = None
        self.ocupado = False

    # ------------------------------------------------------------------ ajudantes

    def cliente(self) -> ClienteGroq:
        return cliente_da_configuracao(self.config)

    def assistente(self):
        """Assistente com IA e reserva offline; sem chave, só o assistente local."""
        cliente = self.cliente()
        if not cliente.configurado:
            return AssistenteLocal()
        return AssistenteComReserva(Assistente(cliente))

    def parametros(self) -> Parametros:
        return parametros_da_configuracao(self.config)

    def atualizar(self) -> None:
        self.page.update()

    def mostrar(self, controles: list[ft.Control]) -> None:
        """Troca o conteúdo da página."""
        self.page.clean()
        self.page.add(ft.Column(controls=controles, spacing=12, scroll=ft.ScrollMode.AUTO,
                                expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER))

    async def copiar(self, texto: str) -> bool:
        """Copia para a área de transferência. A API muda entre versões do Flet: tenta as
        formas conhecidas e devolve False se nenhuma funcionar."""
        formas = []
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

    # ------------------------------------------------------------------ navegação

    def ir_inicio(self) -> None:
        self.mostrar(inicio.montar(self))

    def ir_assistente(self, passo: int = 0) -> None:
        self.mostrar(assistente_passos.montar(self, passo))

    def ir_plano(self) -> None:
        self.mostrar(plano.montar(self))

    def ir_lista(self) -> None:
        self.mostrar(lista.montar(self))

    def ir_cronograma(self) -> None:
        self.mostrar(cronograma.montar(self))

    def ir_conversa(self) -> None:
        if self.plano is not None and self.conversa is None:
            cliente = self.cliente()
            if cliente.configurado:
                self.conversa = Conversa(cliente, resumo_plano(self.plano),
                                         ConversaLocal(self.plano))
            else:
                self.conversa = ConversaLocal(self.plano)
        self.mostrar(conversa.montar(self))

    def ir_configuracoes(self) -> None:
        self.mostrar(configuracoes.montar(self))

    def abrir_salvo(self, id: int) -> None:
        """Carrega um plano salvo e mostra a tela do plano."""
        pedido, explicacao = self.banco.carregar(id)
        self.plano = montar_plano(pedido, self.parametros(), self.config.precos, explicacao)
        self.plano_id, self.motivos, self.aviso, self.conversa = id, {}, "", None
        self.ir_plano()

    def novo_plano(self, pedido_plano: Plano, motivos: dict[str, str], aviso: str) -> None:
        self.plano, self.plano_id, self.motivos = pedido_plano, None, motivos
        self.aviso, self.conversa = aviso, None
        self.ir_plano()


async def main(page: ft.Page) -> None:
    """Ponto de entrada passado para `ft.run`."""
    page.title = "Churrasco Fácil"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 14
    try:
        page.window.width = 430
        page.window.height = 900
    except Exception:  # janela não configurável (web/celular): sem problema
        logger.debug("window não configurável", exc_info=True)
    AppChurrasco(page).ir_inicio()
