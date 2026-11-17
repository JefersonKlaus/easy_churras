"""Peças de tela reutilizáveis."""
from __future__ import annotations

from typing import Any, Callable, Optional

import flet as ft

MARROM = "#7C2D12"
LARANJA = "#EA580C"
CINZA = "#57534E"
FUNDO_CARTAO = "#FFF7ED"
FUNDO_AVISO = "#FEE2E2"
VERMELHO = "#B91C1C"
VERDE = "#15803D"


def titulo(texto: str) -> ft.Control:
    return ft.Text(texto, size=24, weight=ft.FontWeight.BOLD, color=MARROM)


def subtitulo(texto: str) -> ft.Control:
    return ft.Text(texto, size=14, color=CINZA)


def secao(texto: str) -> ft.Control:
    return ft.Text(texto, size=17, weight=ft.FontWeight.BOLD, color=MARROM)


def cartao(controles: list[ft.Control], fundo: str = FUNDO_CARTAO) -> ft.Control:
    return ft.Container(content=ft.Column(controls=controles, spacing=6), padding=12,
                        bgcolor=fundo, border_radius=10)


def erro(texto: str) -> ft.Text:
    return ft.Text(texto, size=14, color=VERMELHO, weight=ft.FontWeight.W_500)


def linha_botoes(botoes: list[ft.Control]) -> ft.Control:
    return ft.Row(controls=botoes, wrap=True, spacing=8,
                  alignment=ft.MainAxisAlignment.CENTER)


class Contador:
    """Linha com texto, botão de menos, número e botão de mais."""

    def __init__(self, rotulo: str, valor: int, minimo: int, maximo: int,
                 ao_mudar: Callable[[int], None], atualizar: Callable[[], None]) -> None:
        self.rotulo = rotulo
        self.valor = valor
        self.minimo = minimo
        self.maximo = maximo
        self._ao_mudar = ao_mudar
        self._atualizar = atualizar
        self._numero = ft.Text(str(valor), size=20, weight=ft.FontWeight.BOLD, width=44,
                               text_align=ft.TextAlign.CENTER)
        self.controle = ft.Row(controls=[
            ft.Text(rotulo, size=16, expand=True),
            ft.OutlinedButton("-", on_click=self._menos),
            self._numero,
            ft.OutlinedButton("+", on_click=self._mais),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER)

    def definir(self, valor: int) -> None:
        """Muda o número respeitando os limites (sem chamar `ao_mudar`)."""
        self.valor = max(self.minimo, min(self.maximo, valor))
        self._numero.value = str(self.valor)

    def _mudar(self, novo: int) -> None:
        novo = max(self.minimo, min(self.maximo, novo))
        if novo == self.valor:
            return
        self.definir(novo)
        self._ao_mudar(self.valor)
        self._atualizar()

    def _menos(self, _evento: Any) -> None:
        self._mudar(self.valor - 1)

    def _mais(self, _evento: Any) -> None:
        self._mudar(self.valor + 1)


def campo_texto(rotulo: str, valor: str, ao_mudar: Callable[[str], None],
                dica: Optional[str] = None, **extras: Any) -> ft.TextField:
    """Campo de texto que avisa a cada mudança."""
    def mudou(evento: Any) -> None:
        ao_mudar(str(evento.control.value or ""))
    return ft.TextField(label=rotulo, value=valor, hint_text=dica, on_change=mudou, **extras)


def espera(texto: str) -> ft.Control:
    """Indicador de 'pensando...'."""
    return ft.Row(controls=[ft.ProgressRing(width=18, height=18), ft.Text(texto, size=14)],
                  alignment=ft.MainAxisAlignment.CENTER)
