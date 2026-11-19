"""Passo 2: quem vem (adultos, crianças, vegetarianos, quem bebe). Com a chave do Groq, dá
para contar em palavras."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import flet as ft

from ...cliente_groq import ErroGroq
from .. import tema as t
from .. import widgets as w
from . import comum as c

if TYPE_CHECKING:
    from ...app import AppChurrasco


def _texto_livre(app: AppChurrasco) -> list[ft.Control]:
    """Campo para contar quem vem em palavras. Quem lê é a IA do Groq."""
    r = app.rascunho
    mensagem = ft.Text("", size=13, color=t.SECUNDARIO, text_align=w.CENTRO)
    campo = ft.TextField(label="Ou conte em poucas palavras", multiline=True, min_lines=2,
                         max_lines=5, value=r.texto_livre, border_radius=12, text_size=16,
                         hint_text="Ex.: 12 pessoas, 3 crianças, 1 vegetariano. "
                                   "Não escreva nomes.",
                         on_change=lambda e: setattr(r, "texto_livre",
                                                     str(e.control.value or "")))

    async def entender(_evento: Any) -> None:
        if app.ocupado:
            return
        app.ocupado, mensagem.value = True, "Lendo o seu pedido..."
        app.atualizar()
        assistente = app.assistente()
        try:
            entendido = await assistente.interpretar_pedido(r.texto_livre)
            aviso_reserva = f"{assistente.aviso} " if assistente.aviso else ""
            mudou = r.aplicar_interpretacao(entendido.adultos, entendido.criancas,
                                            entendido.vegetarianos, entendido.bebem_alcool,
                                            entendido.duracao_horas)
            if mudou:
                faltou = (f" Falta confirmar: {', '.join(entendido.faltando)}."
                          if entendido.faltando else "")
                resultado = (f"{aviso_reserva}Entendi: {', '.join(mudou)}.{faltou} "
                             "Confira os números.")
            else:
                resultado = f"{aviso_reserva}Não consegui entender números no seu texto."
        except ErroGroq as erro:
            resultado = erro.mensagem_usuario
        except ValueError as erro:
            resultado = str(erro)
        finally:
            app.ocupado = False
        app.aviso = resultado      # a tela é redesenhada com os números novos e este recado
        app.ir_assistente(c.QUEM_VEM)

    return [campo, w.linha_botoes([w.botao_secundario("Entender o texto", entender,
                                                      ft.Icons.AUTO_AWESOME)]), mensagem]


def montar(app: AppChurrasco) -> w.Tela:
    r = app.rascunho
    erro = w.erro("")
    contadores: dict[str, w.Contador] = {}

    def mudou_adultos(valor: int) -> None:
        r.adultos = valor
        r.ajustar_limites()
        for campo in ("vegetarianos", "bebem_alcool"):
            contadores[campo].maximo = valor
            contadores[campo].definir(getattr(r, campo))

    contadores["adultos"] = w.Contador("Adultos", r.adultos, 0, 100, mudou_adultos,
                                       app.atualizar)
    contadores["criancas"] = w.Contador("Crianças", r.criancas, 0, 100,
                                        c.guardar(app, "criancas"), app.atualizar)
    contadores["vegetarianos"] = w.Contador("Vegetarianos (entre os adultos)", r.vegetarianos,
                                            0, r.adultos, c.guardar(app, "vegetarianos"),
                                            app.atualizar)
    contadores["bebem_alcool"] = w.Contador("Adultos que bebem álcool", r.bebem_alcool, 0,
                                            r.adultos, c.guardar(app, "bebem_alcool"),
                                            app.atualizar)

    def proximo(_evento: Any) -> None:
        try:
            r.para_convidados()
        except ValueError as problema:
            erro.value = str(problema)
            app.atualizar()
            return
        app.ir_assistente(c.QUANDO)

    controles: list[ft.Control] = []
    if app.aviso:
        controles.append(w.dica(app.aviso))
        app.aviso = ""
    controles += [c.controle for c in contadores.values()]
    if app.cliente().configurado:
        controles += _texto_livre(app)
    return w.Tela(controles, topo=c.topo(app, c.QUEM_VEM),
                  rodape=c.rodape(app, c.QUEM_VEM, erro, proximo))
