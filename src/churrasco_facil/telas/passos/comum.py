"""O que os 4 passos têm em comum: os ícones dos passos e o título, fixos em cima; Voltar e
Próximo (com o recado de erro), fixos embaixo."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Optional

import flet as ft

from .. import tema as t
from .. import widgets as w

if TYPE_CHECKING:
    from ...app import AppChurrasco

PASSOS = ("Preços", "Quem vem", "Quando", "Escolha o churrasco")
ICONES = (ft.Icons.PAYMENTS, ft.Icons.GROUPS, ft.Icons.EVENT, ft.Icons.RESTAURANT_MENU)
PRECOS, QUEM_VEM, QUANDO, ESCOLHA = range(len(PASSOS))
COR_DO_ESTADO = {"feito": t.SUCESSO, "atual": t.PRIMARIA, "depois": t.APAGADO}


def ir_para(app: AppChurrasco, passo: int) -> Callable[[Any], None]:
    def tratador(_evento: Any) -> None:
        if passo < 0:
            app.ir_inicio()
        else:
            app.ir_assistente(passo)
    return tratador


def indicador(passo: int) -> ft.Control:
    """Um ícone por passo: verde os feitos, laranja (e maior) o atual, cinza os que faltam."""
    itens: list[ft.Control] = []
    for i, (nome, icone) in enumerate(zip(PASSOS, ICONES, strict=True)):
        estado = "feito" if i < passo else "atual" if i == passo else "depois"
        if i:
            itens.append(ft.Container(width=28, height=3, border_radius=2,
                                      bgcolor=COR_DO_ESTADO["feito" if i <= passo
                                                            else "depois"]))
        itens.append(ft.Icon(icon=icone, tooltip=nome, data=estado,
                             color=COR_DO_ESTADO[estado], size=34 if estado == "atual" else 26))
    return ft.Row(controls=itens, alignment=ft.MainAxisAlignment.CENTER,
                  vertical_alignment=ft.CrossAxisAlignment.CENTER)


def topo(app: AppChurrasco, passo: int) -> list[ft.Control]:
    """Fixo em cima: o X para sair, os ícones dos passos e o título do passo."""
    sair = w.botao_icone(ft.Icons.CLOSE, "Sair do planejamento", lambda _e: app.ir_inicio())
    return [ft.Row(controls=[sair, ft.Container(content=indicador(passo), expand=True),
                             ft.Container(width=48)]),
            w.titulo(PASSOS[passo])]


def botao_voltar(app: AppChurrasco, passo: int) -> ft.Control:
    return w.botao_secundario("Voltar", ir_para(app, passo - 1))


def rodape(app: AppChurrasco, passo: int, erro: ft.Control,
            proximo: Optional[Callable[[Any], None]] = None) -> list[ft.Control]:
    """Recado de erro e os botões, fixos embaixo da tela."""
    botoes = [botao_voltar(app, passo)]
    if proximo is not None:
        botoes.append(w.botao_principal("Próximo", proximo))
    return [erro, w.linha_botoes(botoes)]


def guardar(app: AppChurrasco, campo: str) -> Callable[[Any], None]:
    def tratador(valor: Any) -> None:
        setattr(app.rascunho, campo, valor)
    return tratador
