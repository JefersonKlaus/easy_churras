"""Aba Horários: o que fazer, a que horas, e os cuidados de cada hora."""
from __future__ import annotations

from typing import TYPE_CHECKING

import flet as ft

from ..cronograma import formatar_hora
from ..linha_do_tempo import Momento, linha_do_tempo
from ..seguranca import Aviso
from . import navegacao
from . import tema as t
from . import widgets as w

if TYPE_CHECKING:
    from ..app import AppChurrasco

COR_POR_TIPO = {"fogo": t.PRIMARIA, "servir": t.SUCESSO, "compras": t.SECUNDARIO}


def _cuidado(aviso: Aviso) -> ft.Control:
    """Linha curta com o aviso, sempre à vista embaixo do horário."""
    cor = t.PERIGO if aviso.grave else t.TEXTO
    return ft.Row(controls=[ft.Icon(icon=ft.Icons.WARNING_AMBER, color=cor, size=16),
                            ft.Text(aviso.titulo, size=13, color=cor, expand=True)],
                  spacing=6)


def _momento(momento: Momento, atualizar) -> ft.Control:
    etapa = momento.etapa
    cabeca: list[ft.Control] = [ft.Row(controls=[
        ft.Text(formatar_hora(etapa.hora), size=16, weight=ft.FontWeight.BOLD,
                color=COR_POR_TIPO.get(etapa.tipo, t.TEXTO), width=56),
        ft.Text(etapa.titulo, size=15, weight=ft.FontWeight.W_500, expand=True),
    ])]
    cabeca += [_cuidado(a) for a in momento.avisos]
    detalhes = [ft.Text(etapa.detalhe, size=13, color=t.TEXTO, text_align=w.CENTRO)]
    detalhes += [ft.Text(a.texto, size=13, color=t.PERIGO if a.grave else t.TEXTO,
                         text_align=w.CENTRO) for a in momento.avisos]
    grave = any(a.grave for a in momento.avisos)
    return w.expansivel(cabeca, detalhes, atualizar,
                        fundo=t.PERIGO_CLARO if grave else t.SUPERFICIE,
                        borda=t.PERIGO_BORDA if grave else t.BORDA)


def montar(app: AppChurrasco) -> w.Tela:
    plano = app.plano
    if plano is None:
        return navegacao.sem_plano(app)
    controles: list[ft.Control] = navegacao.recado(app)
    controles.append(w.dica("Toque em um horário para ver o que fazer. O triângulo marca um "
                            "cuidado daquela hora."))
    dia_anterior = None
    for momento in linha_do_tempo(plano.cronograma, plano.avisos):
        if momento.etapa.hora.date() != dia_anterior:
            dia_anterior = momento.etapa.hora.date()
            controles.append(w.secao(momento.etapa.hora.strftime("%d/%m")))
        controles.append(_momento(momento, app.atualizar))
    return w.Tela(controles, topo=navegacao.cabecalho(app, navegacao.HORARIOS))
