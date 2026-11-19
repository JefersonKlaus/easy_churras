"""Navegação do plano: cabeçalho comum, o botão de baixo (Salvar e, depois de salvo, Início)
e as abas, fixos embaixo."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import flet as ft

from ..datas import descrever_data
from . import tema as t
from . import widgets as w

if TYPE_CHECKING:
    from ..app import AppChurrasco

# (rótulo, ícone, método do app que abre a aba)
ABAS = (
    ("Carnes", ft.Icons.OUTDOOR_GRILL, "ir_carnes"),
    ("Compras", ft.Icons.SHOPPING_CART, "ir_compras"),
    ("Horários", ft.Icons.SCHEDULE, "ir_horarios"),
)
CARNES, COMPRAS, HORARIOS = range(len(ABAS))


def barra(app: AppChurrasco, aba: int) -> ft.NavigationBar:
    """Barra fixa no rodapé com as abas do plano."""
    def trocar(evento: Any) -> None:
        getattr(app, ABAS[evento.control.selected_index][2])()

    return ft.NavigationBar(
        selected_index=aba, on_change=trocar, bgcolor=t.SUPERFICIE,
        indicator_color=t.PRIMARIA_CLARA,
        destinations=[ft.NavigationBarDestination(icon=icone, label=rotulo)
                      for rotulo, icone, _ in ABAS])


def cabecalho(app: AppChurrasco) -> list[ft.Control]:
    """O churrasco aberto: nome, quando e para quantos. A aba em que a pessoa está aparece
    marcada na barra de baixo; para sair, o botão de baixo (Salvar, depois Início)."""
    plano = app.plano
    assert plano is not None
    pedido = plano.pedido
    return [w.cabecalho(pedido.nome, f"{descrever_data(pedido.hora_servir)} · "
                                     f"{pedido.convidados.pessoas} pessoas", tamanho=22)]


class RodapeDoPlano:
    """O botão fixo embaixo de todas as abas do plano (logo acima delas): Salvar enquanto há
    mudança por salvar; depois de salvo, Início, para voltar à tela inicial."""

    def __init__(self, app: AppChurrasco) -> None:
        self.app = app
        self.linha = w.linha_botoes([])
        self.salvo = ft.Text("Salvo em Meus churrascos.", size=13, color=t.CERTO,
                             weight=ft.FontWeight.W_600, text_align=w.CENTRO)
        self.atualizar()

    @property
    def controles(self) -> list[ft.Control]:
        return [self.salvo, self.linha]

    def atualizar(self) -> None:
        """Mostra o botão certo para o estado do plano (com mudanças ou já salvo)."""
        self.salvo.visible = self.app.salvo
        if self.app.salvo:
            botao = w.botao_principal("Início", lambda _e: self.app.ir_inicio(), ft.Icons.HOME)
        else:
            botao = w.botao_principal("Salvar", self._salvar, ft.Icons.SAVE)
        self.linha.controls = [botao]

    def _salvar(self, _evento: Any) -> None:
        self.app.salvar_plano()
        self.atualizar()
        self.app.atualizar()


def sem_plano(app: AppChurrasco) -> w.Tela:
    return w.Tela([w.titulo("Nenhum plano aberto"),
                   w.linha_botoes([w.botao_principal("Início", lambda _e: app.ir_inicio())])])
