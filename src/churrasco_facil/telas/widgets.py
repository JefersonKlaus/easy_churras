"""Componentes das telas, todos com o mesmo visual (as cores e medidas vêm do `tema`).

Tudo fica centralizado: textos, valores dos campos e o conteúdo dos cartões.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional

import flet as ft

from . import tema as t


@dataclass
class Tela:
    """O que uma tela mostra: `conteudo` rola; `topo` e `rodape` ficam sempre à vista."""

    conteudo: list[ft.Control]
    topo: list[ft.Control] = field(default_factory=list)
    rodape: list[ft.Control] = field(default_factory=list)


# ---------------------------------------------------------------- textos

CENTRO = ft.TextAlign.CENTER


def titulo(texto: str, tamanho: int = 26) -> ft.Text:
    return ft.Text(texto, size=tamanho, weight=ft.FontWeight.W_700, color=t.TEXTO,
                   text_align=CENTRO)


def subtitulo(texto: str) -> ft.Text:
    return ft.Text(texto, size=15, color=t.SECUNDARIO, text_align=CENTRO)


def secao(texto: str) -> ft.Text:
    return ft.Text(texto, size=18, weight=ft.FontWeight.W_600, color=t.TEXTO,
                   text_align=CENTRO)


def dica(texto: str) -> ft.Text:
    """Texto pequeno de apoio ("toque para ver...")."""
    return ft.Text(texto, size=13, color=t.SECUNDARIO, text_align=CENTRO)


def erro(texto: str) -> ft.Text:
    return ft.Text(texto, size=15, color=t.PERIGO, weight=ft.FontWeight.W_500,
                   text_align=CENTRO)


# ---------------------------------------------------------------- botões

def _estilo_botao() -> ft.ButtonStyle:
    return ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=t.RAIO_BOTAO),
                          text_style=ft.TextStyle(size=17, weight=ft.FontWeight.W_600))


def botao_principal(texto: str, on_click: Callable[[Any], Any],
                    icone: Optional[str] = None) -> ft.FilledButton:
    """A ação principal da tela: grande, cheia e na cor de destaque."""
    return ft.FilledButton(texto, icon=icone, on_click=on_click, height=t.ALTURA_BOTAO,
                           expand=True, style=_estilo_botao())


def botao_secundario(texto: str, on_click: Callable[[Any], Any],
                     icone: Optional[str] = None) -> ft.OutlinedButton:
    """Ação de apoio: mesmo tamanho da principal, só com contorno."""
    return ft.OutlinedButton(texto, icon=icone, on_click=on_click, height=t.ALTURA_BOTAO,
                             expand=True, style=_estilo_botao())


def botao_icone(icone: str, dica_: str, on_click: Callable[[Any], Any]) -> ft.IconButton:
    """Ícone que faz uma ação. A `dica_` aparece ao segurar e é lida por leitores de tela."""
    return ft.IconButton(icon=icone, tooltip=dica_, on_click=on_click, icon_size=26,
                         icon_color=t.TEXTO, width=48, height=48)


def linha_botoes(botoes: list[ft.Control]) -> ft.Row:
    """Botões lado a lado, dividindo a largura por igual."""
    return ft.Row(controls=botoes, spacing=12)


# ---------------------------------------------------------------- blocos

def _coluna(controles: list[ft.Control], espaco: int = 8) -> ft.Column:
    """Coluna com o conteúdo centralizado."""
    return ft.Column(controls=controles, spacing=espaco,
                     horizontal_alignment=ft.CrossAxisAlignment.CENTER)


def cartao(controles: list[ft.Control], fundo: str = t.SUPERFICIE, borda: str = t.BORDA,
           on_click: Optional[Callable[[Any], Any]] = None) -> ft.Container:
    """Bloco branco de cantos arredondados. Com `on_click`, o cartão inteiro é um botão."""
    return ft.Container(content=_coluna(controles), padding=t.ESPACO, bgcolor=fundo,
                        border_radius=t.RAIO, border=ft.Border.all(1, borda),
                        ink=on_click is not None, on_click=on_click)


def cabecalho(titulo_: str, subtitulo_: str = "", esquerda: Optional[ft.Control] = None,
              direita: Optional[ft.Control] = None, tamanho: int = 26) -> ft.Column:
    """Título centralizado, com um ícone opcional de cada lado (ex.: voltar, configurações).

    Os ícones ficam na altura do título e um espaço do mesmo tamanho equilibra o outro lado,
    para o título ficar no meio. O subtítulo vem embaixo, com a largura toda."""
    nome = titulo(titulo_, tamanho)
    nome.expand = True
    vazio = ft.Container(width=48) if esquerda or direita else None
    linha = ft.Row(controls=[c for c in (esquerda or vazio, nome, direita or vazio)
                             if c is not None],
                   vertical_alignment=ft.CrossAxisAlignment.CENTER)
    controles: list[ft.Control] = [linha]
    if subtitulo_:
        controles.append(subtitulo(subtitulo_))
    return ft.Column(controls=controles, spacing=2,
                     horizontal_alignment=ft.CrossAxisAlignment.STRETCH)


def expansivel(cabeca: list[ft.Control], detalhes: list[ft.Control],
               atualizar: Callable[[], None], nome_detalhes: str = "detalhes",
               fundo: str = t.SUPERFICIE, borda: str = t.BORDA) -> ft.Control:
    """Cartão que mostra só a `cabeca`, com uma seta à direita. Um toque no cartão mostra
    (ou esconde) os `detalhes`, e a seta vira para cima (ou para baixo)."""
    corpo = _coluna(detalhes, espaco=6)
    corpo.visible = False
    seta = ft.Icon(icon=ft.Icons.EXPAND_MORE, color=t.PRIMARIA, size=26,
                   tooltip=f"Ver {nome_detalhes}")

    def alternar(_evento: Any) -> None:
        corpo.visible = not corpo.visible
        seta.icon = ft.Icons.EXPAND_LESS if corpo.visible else ft.Icons.EXPAND_MORE
        seta.tooltip = f"{'Esconder' if corpo.visible else 'Ver'} {nome_detalhes}"
        atualizar()

    topo = ft.Row(controls=[ft.Column(controls=cabeca, spacing=4, expand=True), seta],
                  vertical_alignment=ft.CrossAxisAlignment.CENTER)
    return cartao([topo, corpo], fundo, borda, on_click=alternar)


class Contador:
    """Cartão com o nome em cima e, embaixo, menos, o número e mais (botões redondos e
    grandes)."""

    def __init__(self, rotulo: str, valor: int, minimo: int, maximo: int,
                 ao_mudar: Callable[[int], None], atualizar: Callable[[], None]) -> None:
        self.rotulo = rotulo
        self.valor = valor
        self.minimo = minimo
        self.maximo = maximo
        self._ao_mudar = ao_mudar
        self._atualizar = atualizar
        self._numero = ft.Text(str(valor), size=24, weight=ft.FontWeight.W_700, width=48,
                               text_align=ft.TextAlign.CENTER, color=t.TEXTO)
        self.controle = cartao([
            ft.Text(rotulo, size=16, color=t.TEXTO, text_align=CENTRO),
            ft.Row(controls=[self._botao(ft.Icons.REMOVE, "Menos", self._menos),
                             self._numero,
                             self._botao(ft.Icons.ADD, "Mais", self._mais)],
                   alignment=ft.MainAxisAlignment.CENTER,
                   vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=16),
        ])

    @staticmethod
    def _botao(icone: str, dica_: str, on_click: Callable[[Any], None]) -> ft.IconButton:
        return ft.IconButton(icon=icone, tooltip=dica_, on_click=on_click, icon_size=24,
                             width=52, height=52, bgcolor=t.PRIMARIA_CLARA,
                             icon_color=t.PRIMARIA)

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
                dica_: Optional[str] = None, **extras: Any) -> ft.TextField:
    """Campo de texto que avisa a cada mudança."""
    def mudou(evento: Any) -> None:
        ao_mudar(str(evento.control.value or ""))
    return ft.TextField(label=rotulo, value=valor, hint_text=dica_, on_change=mudou,
                        border_radius=12, text_size=16, text_align=CENTRO, **extras)
