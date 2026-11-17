"""Tela do plano: custo, cortes, explicação, avisos e atalhos."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

import flet as ft

from ..catalogo_carnes import CORTES, VEGETARIANO, Corte
from ..cliente_groq import ErroGroq
from ..compartilhar import texto_whatsapp
from ..dinheiro import formatar_reais
from ..lista_compras import formatar_quantidade
from ..orcamento import maiores_gastos
from ..planejador import Plano, descrever_data, montar_plano
from . import widgets as w

if TYPE_CHECKING:
    from ..app import AppChurrasco

DIFICULDADE = {1: "fácil", 2: "média", 3: "difícil"}


def _cartao_de_custo(plano: Plano) -> ft.Control:
    compras = plano.compras
    linhas: list[ft.Control] = [
        ft.Text(f"Custo estimado: {formatar_reais(plano.custo_total)}", size=18,
                weight=ft.FontWeight.BOLD),
        ft.Text(f"Cerca de {formatar_reais(plano.custo_por_pessoa)} por pessoa", size=14,
                color=w.CINZA),
    ]
    if compras.trocas:
        nomes = ", ".join(f"{_nome(a)} por {_nome(b)}" for a, b in compras.trocas)
        linhas.append(ft.Text(f"Para caber no orçamento troquei: {nomes}.", size=13,
                              color=w.CINZA))
    if compras.estourou:
        linhas.append(w.erro(f"Passa {formatar_reais(compras.excedente)} do orçamento."))
        gastos = ", ".join(f"{i.produto.nome} ({formatar_reais(i.custo)})"
                           for i in maiores_gastos(compras.itens))
        linhas.append(ft.Text(f"Onde mais pesa: {gastos}. Reduzir aí ajuda mais.", size=13,
                              color=w.CINZA))
    linhas.append(ft.Text("Preços são estimativas: ajuste em Configurações.", size=12,
                          color=w.CINZA))
    return w.cartao(linhas)


def _nome(id: str) -> str:
    return CORTES[id].nome if id in CORTES else id


def _cartao_de_corte(item: Any, motivo: str) -> ft.Control:
    corte: Corte = item.produto
    linhas: list[ft.Control] = [
        ft.Text(f"{corte.nome}: {formatar_quantidade(item)}", size=16,
                weight=ft.FontWeight.BOLD),
        ft.Text(f"Dificuldade {DIFICULDADE.get(corte.dificuldade, '')} · "
                f"cerca de {corte.tempo_minutos} min na grelha", size=13, color=w.CINZA),
        ft.Text(corte.dica, size=14),
    ]
    if corte.ponto:
        linhas.append(ft.Text(f"Ponto: {corte.ponto}", size=13, color=w.CINZA))
    if motivo:
        linhas.append(ft.Text(f"Por que escolhi: {motivo}", size=13, color=w.VERDE))
    return w.cartao(linhas)


def _avisos(plano: Plano) -> list[ft.Control]:
    controles: list[ft.Control] = [w.secao("Segurança")]
    for aviso in plano.avisos:
        fundo = w.FUNDO_AVISO if aviso.grave else w.FUNDO_CARTAO
        controles.append(w.cartao([
            ft.Text(aviso.titulo, size=15, weight=ft.FontWeight.BOLD,
                    color=w.VERMELHO if aviso.grave else w.MARROM),
            ft.Text(aviso.texto, size=13),
        ], fundo))
    return controles


def montar(app: AppChurrasco) -> list[ft.Control]:
    plano = app.plano
    if plano is None:
        return [w.titulo("Nenhum plano aberto"),
                ft.Button("Voltar", on_click=lambda _e: app.ir_inicio())]
    mensagem = ft.Text(app.aviso, size=13, color=w.CINZA)
    app.aviso = ""
    area_texto = ft.TextField(multiline=True, min_lines=6, max_lines=14, read_only=True,
                              visible=False)
    explicacao = ft.Text(plano.explicacao or "", size=14, visible=bool(plano.explicacao))
    cliente_ok = app.cliente().configurado

    async def pedir_explicacao(_evento: Any) -> None:
        if app.ocupado:
            return
        app.ocupado, mensagem.value = True, "O Mestre está pensando..."
        app.atualizar()
        try:
            assistente = app.assistente()
            texto = await assistente.explicar(plano)
            app.plano = montar_plano(plano.pedido, app.parametros(), app.config.precos, texto)
            if app.plano_id is not None:
                app.banco.atualizar_explicacao(app.plano_id, texto)
            app.ocupado = False
            app.aviso = assistente.aviso
            app.ir_plano()
            return
        except (ErroGroq, ValueError) as erro:
            mensagem.value = getattr(erro, "mensagem_usuario", str(erro))
        app.ocupado = False
        app.atualizar()

    def salvar(_evento: Any) -> None:
        if app.plano_id is None:
            app.plano_id = app.banco.salvar(plano.pedido, plano.explicacao)
            mensagem.value = "Plano salvo na tela inicial."
        else:
            mensagem.value = "Este plano já está salvo."
        app.atualizar()

    async def compartilhar(_evento: Any) -> None:
        texto = texto_whatsapp(plano)
        area_texto.value, area_texto.visible = texto, True
        copiado = await app.copiar(texto)
        mensagem.value = ("Texto copiado! Cole no WhatsApp." if copiado else
                          "Selecione o texto abaixo e copie.")
        app.atualizar()

    pedir = ft.OutlinedButton("Explicar o plano", on_click=pedir_explicacao)
    controles: list[ft.Control] = [
        w.titulo(plano.pedido.nome), w.subtitulo(descrever_data(plano.pedido.hora_servir)),
        mensagem, _cartao_de_custo(plano),
    ]
    controles.append(w.secao("O que vai na grelha"))
    for item in plano.compras.itens:
        if isinstance(item.produto, Corte):
            motivo = app.motivos.get(item.produto.id, "")
            controles.append(_cartao_de_corte(item, motivo))
    if plano.pedido.convidados.vegetarianos == 0 and not any(
            c.categoria == VEGETARIANO for c in plano.cortes):
        controles.append(ft.Text("Ninguém é vegetariano neste churrasco.", size=12,
                                 color=w.CINZA))
    controles += [w.secao("Explicação do Mestre"), explicacao]
    if not plano.explicacao:
        controles.append(pedir)
        if not cliente_ok:
            controles.append(ft.Text("Sem a chave do Groq, a explicação é feita pelo "
                                     "assistente do app, sem internet.", size=12,
                                     color=w.CINZA))
    controles += _avisos(plano)
    controles += [
        w.linha_botoes([
            ft.Button("Lista de compras", on_click=lambda _e: app.ir_lista()),
            ft.Button("Horários", on_click=lambda _e: app.ir_cronograma()),
            ft.Button("Perguntar ao Mestre", on_click=lambda _e: app.ir_conversa()),
        ]),
        w.linha_botoes([
            ft.OutlinedButton("Compartilhar", on_click=compartilhar),
            ft.OutlinedButton("Salvar", on_click=salvar),
            ft.OutlinedButton("Início", on_click=lambda _e: app.ir_inicio()),
        ]),
        area_texto,
    ]
    return controles
