"""Tela da lista de compras, por seção do mercado."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import flet as ft

from ..dinheiro import formatar_reais
from ..lista_compras import agrupar_por_secao, formatar_quantidade, texto_da_lista
from . import widgets as w

if TYPE_CHECKING:
    from ..app import AppChurrasco


def montar(app: AppChurrasco) -> list[ft.Control]:
    plano = app.plano
    if plano is None:
        return [w.titulo("Nenhum plano aberto"),
                ft.Button("Início", on_click=lambda _e: app.ir_inicio())]
    mensagem = ft.Text("", size=13, color=w.CINZA)

    async def copiar(_evento: Any) -> None:
        copiado = await app.copiar(texto_da_lista(plano.compras.itens))
        mensagem.value = "Lista copiada!" if copiado else "Não consegui copiar neste aparelho."
        app.atualizar()

    controles: list[ft.Control] = [w.titulo("Lista de compras"),
                                   w.subtitulo(f"{plano.pedido.nome} · "
                                               f"{plano.pedido.convidados.pessoas} pessoas")]
    for secao, itens in agrupar_por_secao(plano.compras.itens).items():
        linhas: list[ft.Control] = [w.secao(secao)]
        for item in itens:
            detalhe = f" ({item.observacao})" if item.observacao else ""
            linhas.append(ft.Row(controls=[
                ft.Text(f"{item.produto.nome}{detalhe}", size=14, expand=True),
                ft.Text(formatar_quantidade(item), size=14, weight=ft.FontWeight.BOLD),
                ft.Text(formatar_reais(item.custo), size=13, color=w.CINZA, width=84,
                        text_align=ft.TextAlign.RIGHT),
            ], vertical_alignment=ft.CrossAxisAlignment.START))
        controles.append(w.cartao(linhas))
    controles += [
        ft.Text(f"Total estimado: {formatar_reais(plano.custo_total)}", size=18,
                weight=ft.FontWeight.BOLD),
        mensagem,
        w.linha_botoes([ft.OutlinedButton("Copiar lista", on_click=copiar),
                        ft.Button("Voltar ao plano", on_click=lambda _e: app.ir_plano())]),
    ]
    return controles
