"""Tela de conversa com o Mestre do Churrasco."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import flet as ft

from ..cliente_groq import ErroGroq
from . import widgets as w

if TYPE_CHECKING:
    from ..app import AppChurrasco

SUGESTOES = ("Como sei que a carne está no ponto?", "E se começar a chover?",
             "O carvão está acabando, e agora?")


def _balao(texto: str, do_usuario: bool) -> ft.Control:
    return ft.Container(content=ft.Text(texto, size=14), padding=10, border_radius=10,
                        bgcolor="#E7E5E4" if do_usuario else w.FUNDO_CARTAO)


def montar(app: AppChurrasco) -> list[ft.Control]:
    conversa = app.conversa
    if conversa is None:
        return [w.titulo("Abra um plano primeiro"),
                ft.Button("Início", on_click=lambda _e: app.ir_inicio())]
    cliente_ok = app.cliente().configurado
    historico = ft.Column(controls=[_balao(m["content"], m["role"] == "user")
                                    for m in conversa.historico], spacing=8)
    mensagem = ft.Text("" if cliente_ok else
                       "Para conversar, coloque a chave do Groq em Configurações. O resto do "
                       "app funciona sem ela.", size=13, color=w.CINZA)
    pergunta = {"texto": ""}
    campo = ft.TextField(label="Sua dúvida", multiline=True, min_lines=1, max_lines=4,
                         disabled=not cliente_ok,
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
            mensagem.value, campo.value, pergunta["texto"] = "", "", ""
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

    return [
        w.titulo("Mestre do Churrasco"),
        w.subtitulo("Pergunte o que quiser sobre fogo, ponto da carne e imprevistos. Não "
                    "escreva nomes nem dados pessoais."),
        historico, mensagem, campo,
        w.linha_botoes([ft.Button("Enviar", on_click=enviar, disabled=not cliente_ok)]),
        w.linha_botoes([ft.OutlinedButton(s, on_click=sugerir(s), disabled=not cliente_ok)
                        for s in SUGESTOES]),
        w.linha_botoes([ft.OutlinedButton("Limpar conversa", on_click=limpar),
                        ft.Button("Voltar ao plano", on_click=lambda _e: app.ir_plano())]),
    ]
