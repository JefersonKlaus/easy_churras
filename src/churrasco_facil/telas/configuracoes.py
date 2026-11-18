"""Tela de configurações: só a chave do Groq (a IA é opcional)."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import flet as ft

from ..cliente_groq import ClienteGroq, ErroGroq
from ..configuracao import salvar_configuracao
from . import tema as t
from . import widgets as w

if TYPE_CHECKING:
    from ..app import AppChurrasco


def montar(app: AppChurrasco) -> w.Tela:
    config = app.config
    mensagem = ft.Text("", size=15, color=t.SECUNDARIO, text_align=w.CENTRO)
    chave = ft.TextField(label="Chave do Groq", value=config.chave_groq, password=True,
                         can_reveal_password=True, border_radius=12, text_size=16,
                         text_align=w.CENTRO,
                         hint_text="Fica só neste aparelho. Também vale a variável GROQ_API_KEY.")
    situacao = ("IA ligada: o Mestre do Churrasco usa o Groq." if app.cliente().configurado
                else "Sem chave, o app funciona igual, com respostas prontas e sem internet.")

    def chave_digitada() -> str:
        return str(chave.value or "").strip()

    def salvar(_evento: Any) -> None:
        config.chave_groq = chave_digitada()
        ok = salvar_configuracao(config)
        mensagem.value = "Configurações salvas." if ok else "Não consegui salvar no aparelho."
        mensagem.color = t.SUCESSO if ok else t.PERIGO
        app.atualizar()

    async def testar(_evento: Any) -> None:
        if app.ocupado:
            return
        cliente = ClienteGroq(chave_digitada(), modelo=config.modelo, tentativas=1)
        if not cliente.configurado:
            mensagem.value, mensagem.color = "Escreva a chave primeiro.", t.PERIGO
            app.atualizar()
            return
        app.ocupado, mensagem.value, mensagem.color = True, "Testando...", t.SECUNDARIO
        app.atualizar()
        try:
            await cliente.conversar([{"role": "user", "content": "Responda só: ok"}],
                                    max_tokens=5)
            mensagem.value, mensagem.color = "Conexão funcionando!", t.SUCESSO
        except ErroGroq as erro:
            mensagem.value, mensagem.color = erro.mensagem_usuario, t.PERIGO
        finally:
            app.ocupado = False
        app.atualizar()

    voltar = w.botao_icone(ft.Icons.ARROW_BACK, "Voltar", lambda _e: app.ir_inicio())
    return w.Tela(
        [w.subtitulo(situacao), chave, mensagem],
        topo=[w.cabecalho("Configurações", esquerda=voltar)],
        rodape=[w.linha_botoes([w.botao_secundario("Testar conexão", testar),
                                w.botao_principal("Salvar", salvar)])])
