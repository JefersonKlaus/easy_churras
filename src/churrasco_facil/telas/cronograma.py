"""Tela dos horários: o que fazer e quando."""
from __future__ import annotations

from typing import TYPE_CHECKING

import flet as ft

from ..cronograma import formatar_hora
from . import widgets as w

if TYPE_CHECKING:
    from ..app import AppChurrasco

COR_POR_TIPO = {"fogo": w.LARANJA, "servir": w.VERDE, "compras": w.CINZA}


def montar(app: AppChurrasco) -> list[ft.Control]:
    plano = app.plano
    if plano is None:
        return [w.titulo("Nenhum plano aberto"),
                ft.Button("Início", on_click=lambda _e: app.ir_inicio())]
    controles: list[ft.Control] = [
        w.titulo("Horários"),
        w.subtitulo("Contados de trás para frente a partir da hora de servir. Tempos são "
                    "estimativas: confira sempre o ponto da carne."),
    ]
    dia_anterior = None
    for etapa in plano.cronograma:
        if etapa.hora.date() != dia_anterior:
            dia_anterior = etapa.hora.date()
            controles.append(w.secao(etapa.hora.strftime("%d/%m")))
        cor = COR_POR_TIPO.get(etapa.tipo, w.MARROM)
        controles.append(ft.Row(controls=[
            ft.Text(formatar_hora(etapa.hora), size=16, weight=ft.FontWeight.BOLD, color=cor,
                    width=56),
            ft.Column(controls=[ft.Text(etapa.titulo, size=15, weight=ft.FontWeight.W_500),
                                ft.Text(etapa.detalhe, size=13, color=w.CINZA)],
                      spacing=2, expand=True),
        ], vertical_alignment=ft.CrossAxisAlignment.START))
    controles.append(ft.Button("Voltar ao plano", on_click=lambda _e: app.ir_plano()))
    return controles
