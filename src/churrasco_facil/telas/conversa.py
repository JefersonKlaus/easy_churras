"""Aba Mestre: a explicação do plano e as dúvidas, com o Mestre do Churrasco."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import flet as ft

from ..cliente_groq import ErroGroq
from ..planejador import montar_plano
from . import navegacao
from . import tema as t
from . import widgets as w

if TYPE_CHECKING:
    from ..app import AppChurrasco

SUGESTOES = ("Como sei que a carne está no ponto?", "E se começar a chover?",
             "O carvão está acabando, e agora?")


def _balao(texto: str, do_usuario: bool) -> ft.Control:
    return ft.Container(content=ft.Text(texto, size=15, color=t.TEXTO), padding=12,
                        border_radius=t.RAIO,
                        bgcolor=t.PRIMARIA_CLARA if do_usuario else t.SUPERFICIE,
                        border=None if do_usuario else ft.Border.all(1, t.BORDA))


def _explicacao(app: AppChurrasco, mensagem: ft.Text) -> ft.Control:
    """O texto da explicação, ou o botão para pedir uma."""
    plano = app.plano
    assert plano is not None
    if plano.explicacao:
        return w.cartao([ft.Text(plano.explicacao, size=14)])

    async def pedir(_evento: Any) -> None:
        if app.ocupado:
            return
        app.ocupado, mensagem.value = True, "O Mestre está pensando..."
        app.atualizar()
        try:
            assistente = app.assistente()
            texto = await assistente.explicar(plano)
        except (ErroGroq, ValueError) as erro:
            app.ocupado = False
            mensagem.value = getattr(erro, "mensagem_usuario", str(erro))
            app.atualizar()
            return
        app.plano = montar_plano(plano.pedido, app.parametros(), app.config.precos, texto)
        if app.plano_id is not None:
            app.banco.atualizar_explicacao(app.plano_id, texto)
        app.ocupado, app.aviso = False, assistente.aviso
        app.ir_conversa()

    return w.linha_botoes([w.botao_secundario("Explicar o meu plano", pedir,
                                              ft.Icons.AUTO_AWESOME)])


def montar(app: AppChurrasco) -> w.Tela:
    conversa = app.conversa
    if app.plano is None or conversa is None:
        return navegacao.sem_plano(app)
    offline = getattr(conversa, "offline", False)
    mensagem = ft.Text(app.aviso or ("Modo offline: respondo com dicas prontas de churrasco."
                                     if offline else ""), size=13, color=t.SECUNDARIO,
                       text_align=w.CENTRO)
    app.aviso = ""
    historico = ft.Column(controls=[_balao(m["content"], m["role"] == "user")
                                    for m in conversa.historico], spacing=8)
    pergunta = {"texto": ""}
    campo = ft.TextField(label="Sua dúvida", multiline=True, min_lines=1, max_lines=4,
                         border_radius=12, text_size=16,
                         on_change=lambda e: pergunta.update(texto=str(e.control.value or "")))

    async def enviar_texto(texto: str) -> None:
        if app.ocupado or not texto.strip():
            return
        app.ocupado, mensagem.value = True, "O Mestre está pensando..."
        historico.controls.append(_balao(texto.strip(), True))
        app.atualizar()
        try:
            resposta = await conversa.perguntar(texto)
            historico.controls.append(_balao(resposta, False))
            mensagem.value = ("Sem internet: respondi com dicas prontas."
                              if getattr(conversa, "offline", False) else "")
            campo.value, pergunta["texto"] = "", ""
        except ErroGroq as erro:
            historico.controls.pop()   # a pergunta não foi respondida: tira da tela
            mensagem.value = erro.mensagem_usuario
        except ValueError as erro:
            historico.controls.pop()
            mensagem.value = str(erro)
        finally:
            app.ocupado = False
        app.atualizar()

    async def enviar(_evento: Any) -> None:
        await enviar_texto(pergunta["texto"])

    def sugerir(texto: str) -> Any:
        async def tratador(_evento: Any) -> None:
            await enviar_texto(texto)
        return tratador

    def limpar(_evento: Any) -> None:
        conversa.limpar()
        app.ir_conversa()

    return w.Tela([
        mensagem,
        _explicacao(app, mensagem),
        historico, campo,
        w.linha_botoes([w.botao_principal("Enviar", enviar, ft.Icons.SEND)]),
        ft.Row(controls=[w.botao_leve(s, sugerir(s)) for s in SUGESTOES], wrap=True),
        w.botao_leve("Limpar conversa", limpar),
    ], topo=navegacao.cabecalho(app, navegacao.MESTRE))
