"""O aplicativo: guarda o estado e leva o usuário de uma tela para outra."""
from __future__ import annotations

import logging
from typing import Iterable, Optional

import flet as ft

from .armazenamento import Armazenamento
from .assistente import Assistente
from .cliente_groq import ClienteGroq
from .configuracao import (Configuracao, carregar_configuracao, cliente_da_configuracao,
                           parametros_da_configuracao)
from .modo_offline.assistente_local import AssistenteLocal
from .modo_offline.reserva import AssistenteComReserva
from .parametros import Parametros
from .planejador import Plano, montar_plano, trocar_carnes
from .rascunho import Rascunho
from .telas import carnes, compras, configuracoes, horarios, inicio, navegacao, passos, tema
from .telas.aparelho import Aparelho
from .telas.widgets import Tela

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
        self.salvo = False                     # o plano aberto está igual ao que foi salvo?
        self.aba = navegacao.CARNES            # a aba do plano que está aberta
        self.aviso: str = ""                   # recado para a próxima tela (ex.: sem IA)
        self.ocupado = False                   # esperando o Groq: não aceita outro toque
        self.aparelho = Aparelho(page)

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

    def mostrar(self, tela: Tela, aba: Optional[int] = None) -> None:
        """Troca a tela. O topo e o rodapé da tela ficam fixos; só o conteúdo rola.
        Nas abas do plano, a barra de abas aparece no rodapé."""
        com_abas = aba is not None and self.plano is not None
        if com_abas:
            self.aba = aba
        self.page.navigation_bar = navegacao.barra(self, aba) if com_abas else None
        self.page.clean()
        self.page.add(*tela.topo,
                      ft.Column(controls=tela.conteudo, spacing=tema.ESPACO,
                                scroll=ft.ScrollMode.AUTO, expand=True,
                                horizontal_alignment=ft.CrossAxisAlignment.STRETCH),
                      *tela.rodape)

    # ------------------------------------------------------------------ navegação

    def ir_inicio(self) -> None:
        self.mostrar(inicio.montar(self))

    def ir_assistente(self, passo: int = 0) -> None:
        self.mostrar(passos.montar(self, passo))

    def ir_carnes(self) -> None:
        self.mostrar(carnes.montar(self), navegacao.CARNES)

    def ir_compras(self) -> None:
        self.mostrar(compras.montar(self), navegacao.COMPRAS)

    def ir_horarios(self) -> None:
        self.mostrar(horarios.montar(self), navegacao.HORARIOS)

    def ir_configuracoes(self) -> None:
        self.mostrar(configuracoes.montar(self))

    def salvar_plano(self) -> None:
        """Salva o plano aberto em "Meus churrascos" (botão Salvar). Se ele já foi salvo
        antes, grava por cima, em vez de criar outro."""
        if self.plano is None:
            return
        if self.plano_id is None:
            self.plano_id = self.banco.salvar(self.plano.pedido)
        else:
            self.banco.atualizar(self.plano_id, self.plano.pedido)
        self.salvo = True

    def trocar_cortes(self, ids: Iterable[str]) -> None:
        """A pessoa marcou ou desmarcou carnes: o plano é refeito (e fica por salvar)."""
        if self.plano is None:
            return
        pedido = trocar_carnes(self.plano, ids, self.parametros())
        self.plano = montar_plano(pedido, self.parametros(), self.config.precos)
        self.salvo = False

    def abrir_salvo(self, id: int) -> None:
        """Carrega um plano salvo e mostra a tela do plano."""
        self.plano = montar_plano(self.banco.carregar(id), self.parametros(), self.config.precos)
        self.plano_id, self.salvo, self.aviso = id, True, ""
        self.ir_carnes()

    def novo_plano(self, novo: Plano) -> None:
        """O plano da opção escolhida, com as melhores carnes dela. Ainda não está salvo."""
        self.plano, self.plano_id, self.salvo, self.aviso = novo, None, False, ""
        self.ir_carnes()


async def main(page: ft.Page) -> None:
    """Ponto de entrada passado para `ft.run`."""
    page.title = "Churrasco Fácil"
    tema.aplicar(page)
    app = AppChurrasco(page)
    await app.aparelho.travar_em_retrato()
    try:
        page.window.width = 430
        page.window.height = 900
    except Exception:  # janela não configurável (web/celular): sem problema
        logger.debug("window não configurável", exc_info=True)
    app.ir_inicio()
