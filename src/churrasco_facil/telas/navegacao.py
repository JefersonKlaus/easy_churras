"""Navegação do plano: abas no rodapé e cabeçalho comum (com o ícone de início)."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import flet as ft

from ..planejador import descrever_data
from . import tema as t
from . import widgets as w

if TYPE_CHECKING:
    from ..app import AppChurrasco

# (rótulo, ícone, método do app que abre a aba)
ABAS = (
    ("Carnes", ft.Icons.OUTDOOR_GRILL, "ir_plano"),
    ("Compras", ft.Icons.SHOPPING_CART, "ir_lista"),
    ("Horários", ft.Icons.SCHEDULE, "ir_cronograma"),
    ("Mestre", ft.Icons.CHAT, "ir_conversa"),
)
CARNES, COMPRAS, HORARIOS, MESTRE = range(len(ABAS))


def barra(app: AppChurrasco, aba: int) -> ft.NavigationBar:
    """Barra fixa no rodapé com as abas do plano."""
    def trocar(evento: Any) -> None:
        getattr(app, ABAS[evento.control.selected_index][2])()

    return ft.NavigationBar(
        selected_index=aba, on_change=trocar, bgcolor=t.SUPERFICIE,
        indicator_color=t.PRIMARIA_CLARA,
        destinations=[ft.NavigationBarDestination(icon=icone, label=rotulo)
                      for rotulo, icone, _ in ABAS])


def inicio(app: AppChurrasco, icone: str = ft.Icons.HOME) -> ft.IconButton:
    """Ícone que leva à tela inicial."""
    return w.botao_icone(icone, "Início", lambda _e: app.ir_inicio())


def cabecalho(app: AppChurrasco, aba: int) -> list[ft.Control]:
    """Nome da aba, de qual churrasco ela é e o ícone de início."""
    plano = app.plano
    assert plano is not None
    return [w.cabecalho(ABAS[aba][0],
                        f"{plano.pedido.nome} · {descrever_data(plano.pedido.hora_servir)}",
                        direita=inicio(app))]


def recado(app: AppChurrasco) -> list[ft.Control]:
    """O recado deixado para esta tela (ex.: "plano salvo"), mostrado uma vez só."""
    texto, app.aviso = app.aviso, ""
    return [ft.Text(texto, size=14, color=t.SUCESSO, weight=ft.FontWeight.W_600,
                    text_align=w.CENTRO)] if texto else []


def sem_plano(app: AppChurrasco) -> w.Tela:
    return w.Tela([w.titulo("Nenhum plano aberto"),
                   w.linha_botoes([w.botao_principal("Início", lambda _e: app.ir_inicio())])])
