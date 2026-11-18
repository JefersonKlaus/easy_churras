"""Tela inicial: começar um churrasco novo ou abrir um salvo."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

import flet as ft

from ..planejador import descrever_data
from . import widgets as w

if TYPE_CHECKING:
    from ..app import AppChurrasco


def _abrir(app: AppChurrasco, id: int) -> Callable[[Any], None]:
    def tratador(_evento: Any) -> None:
        app.abrir_salvo(id)
    return tratador


def _excluir(app: AppChurrasco, id: int) -> Callable[[Any], None]:
    def tratador(_evento: Any) -> None:
        app.banco.excluir(id)
        app.ir_inicio()
    return tratador


def montar(app: AppChurrasco) -> w.Tela:
    configurar = w.botao_icone(ft.Icons.SETTINGS, "Configurações",
                               lambda _e: app.ir_configuracoes())
    controles: list[ft.Control] = [
        w.cabecalho("Churrasco Fácil", "Seu primeiro churrasco sem sufoco: quanto comprar, "
                    "quanto custa e a que horas fazer cada coisa.", direita=configurar),
        w.linha_botoes([w.botao_principal("Planejar um churrasco",
                                          lambda _e: app.ir_assistente(0),
                                          ft.Icons.OUTDOOR_GRILL)]),
    ]
    salvos = app.banco.listar()
    if salvos:
        controles.append(w.secao("Meus churrascos"))
    for salvo in salvos:
        controles.append(w.cartao([
            ft.Row(controls=[
                ft.Column(controls=[ft.Text(salvo.nome, size=17, weight=ft.FontWeight.W_600),
                                    w.dica(descrever_data(salvo.hora_servir))],
                          spacing=2, expand=True),
                w.botao_icone(ft.Icons.DELETE_OUTLINE, "Excluir", _excluir(app, salvo.id)),
            ]),
            w.linha_botoes([w.botao_secundario("Abrir", _abrir(app, salvo.id))]),
        ]))
    return w.Tela(controles)
