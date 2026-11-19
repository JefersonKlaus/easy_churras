"""Aba Horários: lembretes simples, da véspera até o fim da festa. O que vai para a grelha fica
num cartão só, e tirar cada carne e servir em outro. O cuidado de cada hora fica a um toque."""
from __future__ import annotations

from typing import TYPE_CHECKING

import flet as ft

from ..datas import DIAS_DA_SEMANA, formatar_hora
from ..linha_do_tempo import Cartao, Momento, cartoes, linha_do_tempo
from ..seguranca import Aviso
from . import navegacao
from . import tema as t
from . import widgets as w

if TYPE_CHECKING:
    from ..app import AppChurrasco

COR_POR_TIPO = {"fogo": t.PRIMARIA, "servir": t.SUCESSO, "compras": t.SECUNDARIO}


def _cuidado(aviso: Aviso) -> ft.Control:
    """O cuidado daquela hora, nos detalhes: o título em destaque e a explicação."""
    cor = t.PERIGO if aviso.grave else t.TEXTO
    return ft.Column(controls=[
        ft.Row(controls=[ft.Icon(icon=ft.Icons.WARNING_AMBER, color=cor, size=16),
                         ft.Text(aviso.titulo, size=13, color=cor, weight=ft.FontWeight.W_600,
                                 expand=True)], spacing=6),
        ft.Text(aviso.texto, size=13, color=cor)], spacing=2)


def _linha_do_item(momento: Momento) -> ft.Control:
    """Um item dentro de um cartão junto: a hora e a linha curta (ex.: '13:27  Picanha')."""
    etapa = momento.etapa
    return ft.Row(controls=[
        ft.Text(formatar_hora(etapa.hora), size=14, weight=ft.FontWeight.W_600,
                color=COR_POR_TIPO.get(etapa.tipo, t.TEXTO), width=56),
        ft.Text(etapa.resumo or etapa.titulo, size=14, color=t.TEXTO, expand=True)])


def _detalhes(cartao: Cartao) -> list[ft.Control]:
    """O que aparece ao tocar: os cuidados e o que fazer (de cada item, nos cartões juntos)."""
    detalhes: list[ft.Control] = [_cuidado(a) for a in cartao.avisos]
    for momento in cartao.momentos:
        etapa = momento.etapa
        if cartao.junto and etapa.detalhe:
            detalhes.append(ft.Text(etapa.resumo or etapa.titulo, size=13, color=t.TEXTO,
                                    weight=ft.FontWeight.W_600, text_align=w.CENTRO))
        if etapa.detalhe:
            detalhes.append(ft.Text(etapa.detalhe, size=13, color=t.TEXTO, text_align=w.CENTRO))
    return detalhes


def _cartao(cartao: Cartao, atualizar) -> ft.Control:
    """Um lembrete: a hora e o que fazer. Nos cartões juntos ("Na grelha", "Tirar e servir"),
    cada carne vem numa linha com a sua hora. Se há um cuidado, o cartão ganha um triângulo
    (vermelho, se for grave); tocar mostra o cuidado e os detalhes."""
    primeira = cartao.momentos[0].etapa
    grave = any(a.grave for a in cartao.avisos)
    linha: list[ft.Control] = [
        ft.Text(formatar_hora(cartao.hora), size=16, weight=ft.FontWeight.BOLD,
                color=COR_POR_TIPO.get(primeira.tipo, t.TEXTO), width=56),
        ft.Text(cartao.titulo, size=15, weight=ft.FontWeight.W_600 if cartao.junto
                else ft.FontWeight.W_500, expand=True)]
    if cartao.avisos:
        linha.append(ft.Icon(icon=ft.Icons.WARNING_AMBER, size=20,
                             color=t.PERIGO if grave else t.SECUNDARIO,
                             tooltip="Tem um cuidado nesta hora"))
    cabeca: list[ft.Control] = [ft.Row(controls=linha,
                                       vertical_alignment=ft.CrossAxisAlignment.CENTER)]
    if cartao.junto:
        cabeca += [_linha_do_item(m) for m in cartao.momentos]
    return w.expansivel(cabeca, _detalhes(cartao), atualizar,
                        fundo=t.PERIGO_CLARO if grave else t.SUPERFICIE,
                        borda=t.PERIGO_BORDA if grave else t.BORDA)


def _dia(hora, servir) -> str:
    """'Na véspera · sexta, 20/11' ou 'No dia · sábado, 21/11'."""
    quando = "No dia" if hora.date() == servir.date() else (
        "Na véspera" if hora.date() < servir.date() else "Depois")
    return f"{quando} · {DIAS_DA_SEMANA[hora.weekday()]}, {hora:%d/%m}"


def montar(app: AppChurrasco) -> w.Tela:
    plano = app.plano
    if plano is None:
        return navegacao.sem_plano(app)
    controles: list[ft.Control] = []
    controles.append(w.dica("Um lembrete por hora. O triângulo marca um cuidado: toque para "
                            "ver."))
    dia_anterior = None
    for cartao in cartoes(linha_do_tempo(plano.cronograma, plano.avisos)):
        if cartao.hora.date() != dia_anterior:
            dia_anterior = cartao.hora.date()
            controles.append(w.secao(_dia(cartao.hora, plano.pedido.hora_servir)))
        controles.append(_cartao(cartao, app.atualizar))
    return w.Tela(controles, topo=navegacao.cabecalho(app),
                  rodape=navegacao.RodapeDoPlano(app).controles)
