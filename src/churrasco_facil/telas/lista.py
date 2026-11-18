"""Aba Compras: o que comprar e quanto, por seção do mercado, e o que não esquecer."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import flet as ft

from ..dinheiro import formatar_reais
from ..lista_compras import (agrupar_por_secao, formatar_quantidade, texto_da_lista,
                             texto_dos_lembretes)
from ..produtos import ItemPlano
from . import navegacao
from . import tema as t
from . import widgets as w

if TYPE_CHECKING:
    from ..app import AppChurrasco


def _linha(item: ItemPlano) -> ft.Control:
    return ft.Row(controls=[ft.Text(item.produto.nome, size=14, expand=True),
                            ft.Text(formatar_quantidade(item), size=14,
                                    weight=ft.FontWeight.BOLD)])


def montar(app: AppChurrasco) -> w.Tela:
    plano = app.plano
    if plano is None:
        return navegacao.sem_plano(app)
    mensagem = ft.Text("", size=13, color=t.SECUNDARIO, text_align=w.CENTRO)

    async def copiar(_evento: Any) -> None:
        texto = "\n\n".join(t for t in (texto_da_lista(plano.compras.itens),
                                        texto_dos_lembretes(plano.lembretes)) if t)
        copiado = await app.copiar(texto)
        mensagem.value = "Lista copiada!" if copiado else "Não consegui copiar neste aparelho."
        app.atualizar()

    controles: list[ft.Control] = navegacao.recado(app)
    controles += [w.cartao([w.secao(secao), *(_linha(i) for i in itens)])
                  for secao, itens in agrupar_por_secao(plano.compras.itens).items()]
    if plano.lembretes:
        controles.append(w.cartao([w.secao("Não esqueça"),
                                   w.dica("Fora da conta: só para lembrar."),
                                   *(_linha(i) for i in plano.lembretes)]))
    controles += [
        ft.Text(f"Total estimado: {formatar_reais(plano.custo_total)}", size=18,
                weight=ft.FontWeight.W_700, color=t.TEXTO, text_align=w.CENTRO),
        mensagem,
        w.linha_botoes([w.botao_secundario("Copiar lista", copiar, ft.Icons.CONTENT_COPY)]),
    ]
    return w.Tela(controles, topo=navegacao.cabecalho(app, navegacao.COMPRAS))
