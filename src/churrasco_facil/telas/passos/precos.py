"""Passo 1: conferir os preços do mercado (ficam salvos para a próxima vez)."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import flet as ft

from ...configuracao import salvar_configuracao
from ...dinheiro import valor_para_campo
from ...precos import grupos_de_precos, juntar_precos
from ...produtos import Produto
from .. import widgets as w
from . import comum as c

if TYPE_CHECKING:
    from ...app import AppChurrasco


def _por(produto: Produto) -> str:
    return "/kg" if produto.unidade == "g" and produto.por_quantidade == 1000 else "/un"


def _campo_de_preco(app: AppChurrasco, produto: Produto) -> ft.TextField:
    preco = app.config.precos.get(produto.id, produto.preco)
    return ft.TextField(label=produto.nome, prefix="R$ ", suffix=_por(produto), dense=True,
                        value=valor_para_campo(preco), border_radius=12, text_size=16,
                        text_align=w.CENTRO)


def montar(app: AppChurrasco) -> w.Tela:
    config = app.config
    erro = w.erro("")
    campos: dict[str, ft.TextField] = {}
    controles: list[ft.Control] = [
        w.subtitulo("Confira os preços do seu mercado. Ficam salvos para a próxima vez.")]
    for grupo, produtos in grupos_de_precos():
        da_secao = {p.id: _campo_de_preco(app, p) for p in produtos}
        campos.update(da_secao)
        controles.append(w.secao(grupo))
        # campos com a largura toda, como os outros campos do app
        controles.append(ft.Column(controls=list(da_secao.values()), spacing=8,
                                   horizontal_alignment=ft.CrossAxisAlignment.STRETCH))

    def proximo(_evento: Any) -> None:
        try:
            config.precos = juntar_precos(config.precos, {
                id: str(campo.value or "") for id, campo in campos.items()})
        except ValueError as problema:
            erro.value = f"Confira o preço. {problema}"
            app.atualizar()
            return
        salvar_configuracao(config)
        app.ir_assistente(c.QUEM_VEM)

    return w.Tela(controles, topo=c.topo(app, c.PRECOS),
                  rodape=c.rodape(app, c.PRECOS, erro, proximo))
