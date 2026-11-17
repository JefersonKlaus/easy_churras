"""Tela inicial: planos salvos e atalhos."""
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


def _novo(app: AppChurrasco) -> Callable[[Any], None]:
    def tratador(_evento: Any) -> None:
        app.ir_assistente(0)
    return tratador


def _configurar(app: AppChurrasco) -> Callable[[Any], None]:
    def tratador(_evento: Any) -> None:
        app.ir_configuracoes()
    return tratador


def montar(app: AppChurrasco) -> list[ft.Control]:
    ia_ligada = app.cliente().configurado
    controles: list[ft.Control] = [
        w.titulo("Churrasco Fácil"),
        w.subtitulo("Seu primeiro churrasco sem sufoco: quanto comprar, quanto custa e a que "
                    "horas fazer cada coisa."),
        ft.Button("Planejar um churrasco", on_click=_novo(app)),
        ft.Text("IA conectada: o Mestre do Churrasco pode ajudar." if ia_ligada else
                "IA desligada. O app funciona sem ela; para ligar, coloque a chave do Groq "
                "em Configurações.", size=13, color=w.VERDE if ia_ligada else w.CINZA),
    ]
    salvos = app.banco.listar()
    if salvos:
        controles.append(w.secao("Planos salvos"))
    for salvo in salvos:
        controles.append(w.cartao([
            ft.Text(salvo.nome, size=16, weight=ft.FontWeight.BOLD),
            ft.Text(descrever_data(salvo.hora_servir), size=13, color=w.CINZA),
            w.linha_botoes([ft.Button("Abrir", on_click=_abrir(app, salvo.id)),
                            ft.OutlinedButton("Excluir", on_click=_excluir(app, salvo.id))]),
        ]))
    controles.append(ft.OutlinedButton("Configurações", on_click=_configurar(app)))
    return controles
