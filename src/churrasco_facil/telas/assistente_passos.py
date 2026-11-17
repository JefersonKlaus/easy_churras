"""Assistente em 3 passos: quem vem, quando e quanto gastar, e revisão."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

import flet as ft

from ..assistente import pesos_das_sugestoes
from ..cliente_groq import ErroGroq
from ..entradas import ler_orcamento
from ..planejador import Pedido, montar_plano
from . import widgets as w

if TYPE_CHECKING:
    from ..app import AppChurrasco

TOTAL_PASSOS = 3


def _ir(app: AppChurrasco, passo: int) -> Callable[[Any], None]:
    def tratador(_evento: Any) -> None:
        if passo < 0:
            app.ir_inicio()
        else:
            app.ir_assistente(passo)
    return tratador


def _cabecalho(passo: int, nome: str) -> list[ft.Control]:
    return [w.titulo(nome), w.subtitulo(f"Passo {passo + 1} de {TOTAL_PASSOS}")]


def _navegacao(app: AppChurrasco, passo: int, proximo: ft.Control) -> ft.Control:
    voltar = ft.OutlinedButton("Voltar", on_click=_ir(app, passo - 1))
    return w.linha_botoes([voltar, proximo])


# ---------------------------------------------------------------- passo 1: convidados

def _passo_convidados(app: AppChurrasco) -> list[ft.Control]:
    r = app.rascunho
    contadores: dict[str, w.Contador] = {}

    def mudou_adultos(valor: int) -> None:
        r.adultos = valor
        r.ajustar_limites()
        for campo in ("vegetarianos", "bebem_alcool"):
            contadores[campo].maximo = valor
            contadores[campo].definir(getattr(r, campo))

    def guardar(campo: str) -> Callable[[int], None]:
        def tratador(valor: int) -> None:
            setattr(r, campo, valor)
        return tratador

    contadores["adultos"] = w.Contador("Adultos", r.adultos, 0, 100, mudou_adultos,
                                       app.atualizar)
    contadores["criancas"] = w.Contador("Crianças", r.criancas, 0, 100, guardar("criancas"),
                                        app.atualizar)
    contadores["vegetarianos"] = w.Contador("Vegetarianos (entre os adultos)", r.vegetarianos,
                                            0, r.adultos, guardar("vegetarianos"), app.atualizar)
    contadores["bebem_alcool"] = w.Contador("Adultos que bebem álcool", r.bebem_alcool, 0,
                                            r.adultos, guardar("bebem_alcool"), app.atualizar)
    mensagem = ft.Text("", size=13, color=w.CINZA)
    texto_livre = ft.TextField(label="Ou conte em poucas palavras", multiline=True, min_lines=2,
                               max_lines=5, value=r.texto_livre,
                               hint_text="Ex.: churrasco sábado para 12 pessoas, 3 crianças, "
                                         "1 vegetariano, uns 400 reais. Não escreva nomes.",
                               on_change=lambda e: setattr(r, "texto_livre",
                                                           str(e.control.value or "")))

    async def entender(_evento: Any) -> None:
        if app.ocupado:
            return
        app.ocupado, mensagem.value, mensagem.color = True, "Lendo o seu pedido...", w.CINZA
        app.atualizar()
        assistente = app.assistente()
        aviso_reserva = ""
        try:
            entendido = await assistente.interpretar_pedido(r.texto_livre)
            aviso_reserva = f"{assistente.aviso} " if assistente.aviso else ""
            mudou = r.aplicar_interpretacao(
                entendido.adultos, entendido.criancas, entendido.vegetarianos,
                entendido.bebem_alcool, entendido.duracao_horas, entendido.orcamento_centavos)
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
        app.ir_assistente(0)

    controles = _cabecalho(0, "Quem vem?")
    if app.aviso:
        controles.append(ft.Text(app.aviso, size=13, color=w.CINZA))
        app.aviso = ""
    controles += [c.controle for c in contadores.values()]
    controles += [texto_livre, ft.OutlinedButton("Entender o texto", on_click=entender),
                  mensagem,
                  _navegacao(app, 0, ft.Button("Próximo", on_click=_ir(app, 1)))]
    return controles


# ---------------------------------------------------------------- passo 2: quando e quanto

def _passo_quando(app: AppChurrasco) -> list[ft.Control]:
    r = app.rascunho
    duracao = w.Contador("Duração (horas)", r.duracao_horas, 1, 12,
                         lambda v: setattr(r, "duracao_horas", v), app.atualizar)
    controles = _cabecalho(1, "Quando e quanto?")
    controles += [
        w.campo_texto("Data", r.data_texto, lambda v: setattr(r, "data_texto", v),
                      "dd/mm/aaaa"),
        w.campo_texto("Hora de servir", r.hora_texto, lambda v: setattr(r, "hora_texto", v),
                      "14:00"),
        duracao.controle,
        w.campo_texto("Orçamento em R$ (deixe vazio se não tem limite)", r.orcamento_texto,
                      lambda v: setattr(r, "orcamento_texto", v), "400,00"),
        _navegacao(app, 1, ft.Button("Próximo", on_click=_ir(app, 2))),
    ]
    return controles


# ---------------------------------------------------------------- passo 3: revisar

def _passo_revisar(app: AppChurrasco) -> list[ft.Control]:
    r = app.rascunho
    mensagem = ft.Text("", size=14, color=w.VERMELHO)
    ia_disponivel = app.cliente().configurado
    chave_ia = ft.Switch(label=("Deixar a IA sugerir os cortes" if ia_disponivel
                                else "Sugerir os cortes automaticamente (sem internet)"),
                         value=r.usar_ia,
                         on_change=lambda e: setattr(r, "usar_ia", bool(e.control.value)))

    async def criar(_evento: Any) -> None:
        if app.ocupado:
            return
        try:
            convidados = r.para_convidados()
            hora = r.para_data_hora()
            orcamento = ler_orcamento(r.orcamento_texto)
        except ValueError as erro:
            mensagem.value = str(erro)
            app.atualizar()
            return
        app.ocupado, mensagem.value, mensagem.color = True, "Montando o seu plano...", w.CINZA
        app.atualizar()
        pesos: dict[str, int] = {}
        motivos: dict[str, str] = {}
        aviso = ""
        try:
            if r.usar_ia:
                assistente = app.assistente()
                try:
                    sugestoes = await assistente.sugerir_cortes(convidados, orcamento)
                    pesos = pesos_das_sugestoes(sugestoes)
                    motivos = {s.id: s.motivo for s in sugestoes if s.motivo}
                    aviso = assistente.aviso
                except (ErroGroq, ValueError) as erro:
                    aviso = f"Montei com o plano padrão desta vez. {getattr(erro, 'mensagem_usuario', erro)}"
            pedido = Pedido(convidados, hora, orcamento, pesos, r.nome.strip() or "Meu churrasco")
            plano = montar_plano(pedido, app.parametros(), app.config.precos)
        finally:
            app.ocupado = False
        app.novo_plano(plano, motivos, aviso)

    resumo = (f"{r.adultos} adultos, {r.criancas} crianças, {r.vegetarianos} vegetarianos, "
              f"{r.bebem_alcool} bebem álcool. Dia {r.data_texto} às {r.hora_texto}, "
              f"{r.duracao_horas} horas. "
              + (f"Orçamento R$ {r.orcamento_texto}." if r.orcamento_texto.strip()
                 else "Sem limite de orçamento."))
    return _cabecalho(2, "Confira e monte o plano") + [
        w.cartao([ft.Text(resumo, size=15)]),
        w.campo_texto("Nome do churrasco", r.nome, lambda v: setattr(r, "nome", v)),
        chave_ia, mensagem,
        _navegacao(app, 2, ft.Button("Montar plano", on_click=criar)),
    ]


def montar(app: AppChurrasco, passo: int) -> list[ft.Control]:
    passos = (_passo_convidados, _passo_quando, _passo_revisar)
    return passos[max(0, min(passo, TOTAL_PASSOS - 1))](app)
