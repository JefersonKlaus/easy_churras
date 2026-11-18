"""Aba Carnes: o que vai na grelha e quanto custa. Dali se compartilha o plano.

Não há botão de salvar: o plano é salvo sozinho ao abrir Compras ou Horários.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

import flet as ft

from ..catalogo_carnes import Corte
from ..compartilhar import texto_whatsapp
from ..dinheiro import formatar_reais
from ..lista_compras import formatar_quantidade
from ..produtos import ItemPlano
from . import navegacao
from . import tema as t
from . import widgets as w

if TYPE_CHECKING:
    from ..app import AppChurrasco

DIFICULDADE = {1: "fácil", 2: "média", 3: "difícil"}


def _carne(item: ItemPlano, motivo: str, atualizar: Callable[[], None]) -> ft.Control:
    """Nome e quantidade. As dicas só aparecem quando a pessoa toca."""
    corte: Corte = item.produto
    dicas: list[ft.Control] = [
        w.dica(f"Dificuldade {DIFICULDADE.get(corte.dificuldade, '')} · "
               f"cerca de {corte.tempo_minutos} min na grelha"),
        ft.Text(corte.dica, size=14, color=t.TEXTO, text_align=w.CENTRO),
    ]
    if corte.ponto:
        dicas.append(w.dica(f"Ponto: {corte.ponto}"))
    if motivo:
        dicas.append(ft.Text(f"Por que escolhi: {motivo}", size=13, color=t.SUCESSO,
                             text_align=w.CENTRO))
    cabeca = ft.Row(controls=[
        ft.Text(corte.nome, size=17, weight=ft.FontWeight.W_600, expand=True, color=t.TEXTO),
        ft.Text(formatar_quantidade(item), size=17, weight=ft.FontWeight.W_700,
                color=t.PRIMARIA),
    ])
    return w.expansivel([cabeca], dicas, atualizar, "dicas")


def montar(app: AppChurrasco) -> w.Tela:
    plano = app.plano
    if plano is None:
        return navegacao.sem_plano(app)
    mensagem = ft.Text(app.aviso, size=13, color=t.SECUNDARIO, text_align=w.CENTRO)
    app.aviso = ""
    area_texto = ft.TextField(multiline=True, min_lines=6, max_lines=14, read_only=True,
                              visible=False)

    async def compartilhar(_evento: Any) -> None:
        texto = texto_whatsapp(plano)
        area_texto.value, area_texto.visible = texto, True
        copiado = await app.copiar(texto)
        mensagem.value = ("Texto copiado! Cole no WhatsApp." if copiado else
                          "Selecione o texto abaixo e copie.")
        app.atualizar()

    controles: list[ft.Control] = [
        mensagem, w.dica("Toque em uma carne para ver as dicas.")]
    controles += [_carne(item, app.motivos.get(item.produto.id, ""), app.atualizar)
                  for item in plano.compras.itens if isinstance(item.produto, Corte)]
    controles += [
        ft.Text(f"Total do churrasco: {formatar_reais(plano.custo_total)} "
                f"({formatar_reais(plano.custo_por_pessoa)} por pessoa)", size=18,
                weight=ft.FontWeight.W_700, color=t.TEXTO, text_align=w.CENTRO),
        w.linha_botoes([w.botao_principal("Compartilhar", compartilhar, ft.Icons.SHARE)]),
        area_texto,
    ]
    return w.Tela(controles, topo=navegacao.cabecalho(app, navegacao.CARNES))
