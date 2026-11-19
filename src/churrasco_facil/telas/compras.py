"""Aba Compras: o que comprar e quanto, por seção do mercado, e o que não esquecer. Daqui se
compartilha a lista (com quem vai ao mercado).

No cartão do açougue, cada carne diz como pedir ao açougueiro, e uma dica geral fica no alto
do cartão."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import flet as ft

from ..catalogo_carnes import DICA_DO_ACOUGUE, Corte
from ..compartilhar import texto_compras
from ..compras import custos_por_tipo
from ..dinheiro import formatar_reais
from ..lista_compras import agrupar_por_secao, formatar_quantidade
from ..planejador import Plano
from ..produtos import ACOUGUE, ItemPlano
from . import navegacao
from . import tema as t
from . import widgets as w
from .aparelho import COMPARTILHADO, COPIADO

if TYPE_CHECKING:
    from ..app import AppChurrasco


def _nota(item: ItemPlano) -> str:
    """O texto miúdo embaixo do nome: nas bebidas, quanto é indicado por pessoa; nas carnes
    do açougue, como pedir ao açougueiro."""
    if item.observacao:
        return item.observacao
    return item.produto.como_pedir if isinstance(item.produto, Corte) else ""


def _linha(item: ItemPlano) -> ft.Control:
    """Nome e quantidade, com a nota (se houver) embaixo do nome."""
    nome: ft.Control = ft.Text(item.produto.nome, size=14)
    if nota := _nota(item):
        nome = ft.Column(controls=[nome, ft.Text(nota, size=12, color=t.SECUNDARIO)],
                         spacing=0)
    nome.expand = True
    return ft.Row(controls=[nome, ft.Text(formatar_quantidade(item), size=14,
                                          weight=ft.FontWeight.BOLD)])


def _cartao_da_secao(secao: str, itens: list[ItemPlano]) -> ft.Control:
    """Um cartão por seção do mercado. O do açougue começa com a dica de como comprar."""
    topo: list[ft.Control] = [w.secao(secao)]
    if secao == ACOUGUE:
        topo.append(w.dica(DICA_DO_ACOUGUE))
    return w.cartao([*topo, *(_linha(i) for i in itens)])


def _valor(rotulo: str, centavos: int, destaque: bool = False) -> ft.Control:
    tamanho, peso = (17, ft.FontWeight.W_700) if destaque else (14, ft.FontWeight.W_500)
    return ft.Row(controls=[ft.Text(rotulo, size=tamanho, weight=peso, expand=True),
                            ft.Text(formatar_reais(centavos), size=tamanho, weight=peso)])


def _quanto_custa(plano: Plano) -> ft.Control:
    """O total e o que ele inclui (carnes, bebidas, carvão), parte por parte."""
    partes = custos_por_tipo(plano.compras.itens)
    return w.cartao([
        w.secao("Quanto custa"),
        *(_valor(nome, valor) for nome, valor in partes),
        _valor("Total estimado", plano.custo_total, destaque=True),
        w.dica("Com carnes, bebidas e carvão. O \"Não esqueça\" fica fora da conta."),
    ])


def montar(app: AppChurrasco) -> w.Tela:
    plano = app.plano
    if plano is None:
        return navegacao.sem_plano(app)
    mensagem = ft.Text("", size=13, color=t.SECUNDARIO, text_align=w.CENTRO, visible=False)
    # se não der para compartilhar nem copiar, o texto aparece aqui para a pessoa copiar
    area_texto = ft.TextField(multiline=True, min_lines=6, max_lines=14, read_only=True,
                              visible=False)

    async def compartilhar(_evento: Any) -> None:
        texto = texto_compras(plano)
        titulo = f"Lista de compras: {plano.pedido.nome}"
        resultado = await app.aparelho.compartilhar(texto, titulo)
        if resultado == COPIADO:
            mensagem.value = "Lista copiada! Cole no WhatsApp."
        elif not resultado:
            mensagem.value = "Selecione o texto abaixo e copie."
            area_texto.value, area_texto.visible = texto, True
        mensagem.visible = bool(resultado != COMPARTILHADO)
        app.atualizar()

    controles: list[ft.Control] = [_cartao_da_secao(secao, itens) for secao, itens
                                   in agrupar_por_secao(plano.compras.itens).items()]
    if plano.lembretes:
        controles.append(w.cartao([w.secao("Não esqueça"),
                                   w.dica("Fora da conta: só para lembrar."),
                                   *(_linha(i) for i in plano.lembretes)]))
    controles += [
        _quanto_custa(plano),
        mensagem,
        w.linha_botoes([w.botao_secundario("Compartilhar lista", compartilhar, ft.Icons.SHARE)]),
        area_texto,
    ]
    return w.Tela(controles, topo=navegacao.cabecalho(app),
                  rodape=navegacao.RodapeDoPlano(app).controles)
