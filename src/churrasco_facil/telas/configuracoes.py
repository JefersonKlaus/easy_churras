"""Tela de configurações: chave do Groq, modelo, preços e quantidades."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import flet as ft

from ..calculadora import Parametros
from ..catalogo_carnes import cortes_de_carne
from ..cliente_groq import ClienteGroq, ErroGroq
from ..configuracao import PRECO_MAXIMO, salvar_configuracao
from ..dinheiro import reais_para_centavos
from . import widgets as w

if TYPE_CHECKING:
    from ..app import AppChurrasco


def _texto_preco(centavos: int) -> str:
    return f"{centavos / 100:.2f}".replace(".", ",")


def montar(app: AppChurrasco) -> list[ft.Control]:
    config = app.config
    padrao = Parametros()
    atual = app.parametros()
    mensagem = ft.Text("", size=14, color=w.CINZA)
    campos: dict[str, ft.TextField] = {}

    chave = ft.TextField(label="Chave do Groq", value=config.chave_groq, password=True,
                         can_reveal_password=True,
                         hint_text="Fica só neste aparelho. Também vale a variável GROQ_API_KEY.")
    modelo = ft.TextField(label="Modelo do Groq", value=config.modelo)
    for corte in cortes_de_carne():
        preco = config.precos.get(corte.id, corte.preco)
        campos[corte.id] = ft.TextField(label=f"{corte.nome} (R$ por kg)",
                                        value=_texto_preco(preco))
    carne_adulto = ft.TextField(label="Carne por adulto (gramas)", value=str(atual.carne_adulto_g))
    carne_crianca = ft.TextField(label="Carne por criança (gramas)",
                                 value=str(atual.carne_crianca_g))

    def ler_inteiro(campo: ft.TextField, nome: str) -> int:
        try:
            valor = int(str(campo.value).strip())
        except ValueError:
            raise ValueError(f"{nome}: escreva só números") from None
        if not 50 <= valor <= 2000:
            raise ValueError(f"{nome}: use um valor entre 50 e 2000")
        return valor

    def salvar(_evento: Any) -> None:
        try:
            precos: dict[str, int] = {}
            for id, campo in campos.items():
                centavos = reais_para_centavos(str(campo.value))
                if centavos > PRECO_MAXIMO:
                    raise ValueError("preço alto demais")
                if centavos != next(c.preco for c in cortes_de_carne() if c.id == id):
                    precos[id] = centavos
            parametros: dict[str, float] = {}
            adulto = ler_inteiro(carne_adulto, "Carne por adulto")
            crianca = ler_inteiro(carne_crianca, "Carne por criança")
            if adulto != padrao.carne_adulto_g:
                parametros["carne_adulto_g"] = adulto
            if crianca != padrao.carne_crianca_g:
                parametros["carne_crianca_g"] = crianca
        except ValueError as erro:
            mensagem.value, mensagem.color = f"Confira os números: {erro}", w.VERMELHO
            app.atualizar()
            return
        config.chave_groq = str(chave.value or "").strip()
        config.modelo = str(modelo.value or "").strip() or config.modelo
        config.precos, config.parametros = precos, parametros
        ok = salvar_configuracao(config)
        mensagem.value = "Configurações salvas." if ok else "Não consegui salvar no aparelho."
        mensagem.color = w.VERDE if ok else w.VERMELHO
        app.atualizar()

    async def testar(_evento: Any) -> None:
        if app.ocupado:
            return
        cliente = ClienteGroq(str(chave.value or "").strip(),
                              modelo=str(modelo.value or "").strip() or config.modelo,
                              tentativas=1)
        if not cliente.configurado:
            mensagem.value, mensagem.color = "Escreva a chave primeiro.", w.VERMELHO
            app.atualizar()
            return
        app.ocupado, mensagem.value, mensagem.color = True, "Testando...", w.CINZA
        app.atualizar()
        try:
            await cliente.conversar([{"role": "user", "content": "Responda só: ok"}],
                                    max_tokens=5)
            mensagem.value, mensagem.color = "Conexão funcionando!", w.VERDE
        except ErroGroq as erro:
            mensagem.value, mensagem.color = erro.mensagem_usuario, w.VERMELHO
        finally:
            app.ocupado = False
        app.atualizar()

    return [
        w.titulo("Configurações"),
        w.secao("Groq (IA)"), chave, modelo,
        ft.OutlinedButton("Testar conexão", on_click=testar),
        w.secao("Quantidades"), carne_adulto, carne_crianca,
        w.secao("Preços das carnes"),
        w.subtitulo("Confira os preços da sua cidade: o app usa estes valores nas contas."),
        *campos.values(),
        mensagem,
        w.linha_botoes([ft.Button("Salvar", on_click=salvar),
                        ft.OutlinedButton("Voltar", on_click=lambda _e: app.ir_inicio())]),
    ]
