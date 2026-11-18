"""Assistente em 4 passos, um assunto por tela: preços, quem vem, quando e a escolha.

Em cima, ícones mostram em que passo a pessoa está; embaixo, Voltar e Próximo ficam fixos.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Optional

import flet as ft

from ..cliente_groq import ErroGroq
from ..configuracao import juntar_precos, salvar_configuracao
from ..dinheiro import formatar_reais, valor_para_campo
from ..opcoes import Opcao, OpcaoCalculada, calcular_opcoes, grupos_de_precos
from ..planejador import Pedido, montar_plano
from ..produtos import SECOES_OPCIONAIS, Produto
from . import navegacao
from . import tema as t
from . import widgets as w

if TYPE_CHECKING:
    from ..app import AppChurrasco

PASSOS = ("Preços", "Quem vem", "Quando", "Escolha o churrasco")
ICONES = (ft.Icons.PAYMENTS, ft.Icons.GROUPS, ft.Icons.EVENT, ft.Icons.RESTAURANT_MENU)
PRECOS, QUEM_VEM, QUANDO, ESCOLHA = range(len(PASSOS))
COR_DO_ESTADO = {"feito": t.SUCESSO, "atual": t.PRIMARIA, "depois": t.APAGADO}
# O que a pessoa deixa de comprar quando tira a seção da conta.
O_QUE_TEM_NA_SECAO = {"Hortifruti": "Tomate, cebola e pimentão do vinagrete, e a salada."}


def _ir(app: AppChurrasco, passo: int) -> Callable[[Any], None]:
    def tratador(_evento: Any) -> None:
        if passo < 0:
            app.ir_inicio()
        else:
            app.ir_assistente(passo)
    return tratador


def _indicador(passo: int) -> ft.Control:
    """Um ícone por passo: verde os feitos, laranja (e maior) o atual, cinza os que faltam."""
    itens: list[ft.Control] = []
    for i, (nome, icone) in enumerate(zip(PASSOS, ICONES, strict=True)):
        estado = "feito" if i < passo else "atual" if i == passo else "depois"
        if i:
            itens.append(ft.Container(width=28, height=3, border_radius=2,
                                      bgcolor=COR_DO_ESTADO["feito" if i <= passo
                                                            else "depois"]))
        itens.append(ft.Icon(icon=icone, tooltip=nome, data=estado,
                             color=COR_DO_ESTADO[estado], size=34 if estado == "atual" else 26))
    return ft.Row(controls=itens, alignment=ft.MainAxisAlignment.CENTER,
                  vertical_alignment=ft.CrossAxisAlignment.CENTER)


def _topo(app: AppChurrasco, passo: int) -> list[ft.Control]:
    """Fixo em cima: o X para sair, os ícones dos passos e o título do passo."""
    sair = navegacao.inicio(app, ft.Icons.CLOSE)
    return [ft.Row(controls=[sair, ft.Container(content=_indicador(passo), expand=True),
                             ft.Container(width=48)]),
            w.titulo(PASSOS[passo])]


def _voltar(app: AppChurrasco, passo: int) -> ft.Control:
    return w.botao_secundario("Voltar", _ir(app, passo - 1))


def _rodape(app: AppChurrasco, passo: int, erro: ft.Control,
            proximo: Optional[Callable[[Any], None]] = None) -> list[ft.Control]:
    """Recado de erro e os botões, fixos embaixo da tela."""
    botoes = [_voltar(app, passo)]
    if proximo is not None:
        botoes.append(w.botao_principal("Próximo", proximo))
    return [erro, w.linha_botoes(botoes)]


# ---------------------------------------------------------------- 1. preços

def _por(produto: Produto) -> str:
    return "/kg" if produto.unidade == "g" and produto.por_quantidade == 1000 else "/un"


def _campo_de_preco(app: AppChurrasco, produto: Produto) -> ft.TextField:
    preco = app.config.precos.get(produto.id, produto.preco)
    return ft.TextField(label=produto.nome, prefix="R$ ", suffix=_por(produto), dense=True,
                        value=valor_para_campo(preco), border_radius=12, text_size=16,
                        text_align=w.CENTRO)


def _pergunta_da_secao(app: AppChurrasco, secao: str, campos: ft.Column) -> list[ft.Control]:
    """Chave 'entra na conta?' de uma seção opcional. Fora da conta, os preços somem."""
    r = app.rascunho

    def mudou(evento: Any) -> None:
        incluir = bool(evento.control.value)
        if incluir:
            r.secoes_fora.discard(secao)
        else:
            r.secoes_fora.add(secao)
        campos.visible = incluir
        app.atualizar()

    return [ft.Switch(label=f"Incluir {secao.lower()} na conta",
                      value=secao not in r.secoes_fora, on_change=mudou),
            w.dica(O_QUE_TEM_NA_SECAO.get(secao, ""))]


def _passo_precos(app: AppChurrasco) -> w.Tela:
    config, r = app.config, app.rascunho
    erro = w.erro("")
    campos: dict[str, ft.TextField] = {}
    controles: list[ft.Control] = [
        w.subtitulo("Confira os preços do seu mercado. Ficam salvos para a próxima vez.")]
    for grupo, produtos in grupos_de_precos():
        da_secao = {p.id: _campo_de_preco(app, p) for p in produtos}
        campos.update(da_secao)
        coluna = ft.Column(controls=list(da_secao.values()), spacing=8,
                           visible=grupo not in r.secoes_fora)
        controles.append(w.secao(grupo))
        if grupo in SECOES_OPCIONAIS:
            controles += _pergunta_da_secao(app, grupo, coluna)
        controles.append(coluna)

    def proximo(_evento: Any) -> None:
        fora = {p.id for g, ps in grupos_de_precos() if g in r.secoes_fora for p in ps}
        try:
            config.precos = juntar_precos(config.precos, {
                id: str(campo.value or "") for id, campo in campos.items() if id not in fora})
        except ValueError as problema:
            erro.value = f"Confira o preço. {problema}"
            app.atualizar()
            return
        salvar_configuracao(config)
        app.ir_assistente(QUEM_VEM)

    return w.Tela(controles, topo=_topo(app, PRECOS), rodape=_rodape(app, PRECOS, erro, proximo))


# ---------------------------------------------------------------- 2. quem vem

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
        app.ir_assistente(QUEM_VEM)

    return [campo, w.linha_botoes([w.botao_secundario("Entender o texto", entender,
                                                      ft.Icons.AUTO_AWESOME)]), mensagem]


def _guardar(app: AppChurrasco, campo: str) -> Callable[[Any], None]:
    def tratador(valor: Any) -> None:
        setattr(app.rascunho, campo, valor)
    return tratador


def _passo_quem_vem(app: AppChurrasco) -> w.Tela:
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
                                        _guardar(app, "criancas"), app.atualizar)
    contadores["vegetarianos"] = w.Contador("Vegetarianos (entre os adultos)", r.vegetarianos,
                                            0, r.adultos, _guardar(app, "vegetarianos"),
                                            app.atualizar)
    contadores["bebem_alcool"] = w.Contador("Adultos que bebem álcool", r.bebem_alcool, 0,
                                            r.adultos, _guardar(app, "bebem_alcool"),
                                            app.atualizar)

    def proximo(_evento: Any) -> None:
        try:
            r.para_convidados()
        except ValueError as problema:
            erro.value = str(problema)
            app.atualizar()
            return
        app.ir_assistente(QUANDO)

    controles: list[ft.Control] = []
    if app.aviso:
        controles.append(w.dica(app.aviso))
        app.aviso = ""
    controles += [c.controle for c in contadores.values()]
    if app.cliente().configurado:
        controles += _texto_livre(app)
    return w.Tela(controles, topo=_topo(app, QUEM_VEM),
                  rodape=_rodape(app, QUEM_VEM, erro, proximo))


# ---------------------------------------------------------------- 3. quando

def _passo_quando(app: AppChurrasco) -> w.Tela:
    r = app.rascunho
    erro = w.erro("")
    duracao = w.Contador("Duração da festa (horas)", r.duracao_horas, 1, 12,
                         _guardar(app, "duracao_horas"), app.atualizar)

    def proximo(_evento: Any) -> None:
        try:
            r.para_data_hora()
        except ValueError as problema:
            erro.value = str(problema)
            app.atualizar()
            return
        app.ir_assistente(ESCOLHA)

    return w.Tela([
        w.campo_texto("Data", r.data_texto, _guardar(app, "data_texto"), "dd/mm/aaaa"),
        w.campo_texto("Hora de servir", r.hora_texto, _guardar(app, "hora_texto"), "14:00"),
        duracao.controle,
        w.dica("Quanto tempo os convidados vão ficar. Festa mais longa pede mais carne e "
               "bebida."),
    ], topo=_topo(app, QUANDO), rodape=_rodape(app, QUANDO, erro, proximo))


# ---------------------------------------------------------------- 4. escolha

def _cartao_de_opcao(calculada: OpcaoCalculada, escolher: Callable[[Any], None]
                     ) -> ft.Control:
    opcao = calculada.opcao
    return w.cartao([
        ft.Text(opcao.titulo, size=21, weight=ft.FontWeight.W_700, color=t.TEXTO,
                text_align=w.CENTRO),
        ft.Text(opcao.descricao, size=15, color=t.SECUNDARIO, text_align=w.CENTRO),
        ft.Text(f"{formatar_reais(calculada.custo_total)} no total · "
                f"{formatar_reais(calculada.custo_por_pessoa)} por pessoa", size=17,
                weight=ft.FontWeight.W_700, color=t.PRIMARIA, text_align=w.CENTRO),
    ], on_click=escolher)


def _passo_escolha(app: AppChurrasco) -> w.Tela:
    r = app.rascunho
    erro = w.erro("")
    try:
        convidados = r.para_convidados()
    except ValueError as problema:
        erro.value = str(problema)
        return w.Tela([], topo=_topo(app, ESCOLHA), rodape=_rodape(app, ESCOLHA, erro))
    fora = tuple(s for s in SECOES_OPCIONAIS if s in r.secoes_fora)

    def escolher(opcao: Opcao) -> Callable[[Any], None]:
        def tratador(_evento: Any) -> None:
            try:
                hora = r.para_data_hora()
            except ValueError as problema:
                erro.value = str(problema)
                app.atualizar()
                return
            pedido = Pedido(convidados, hora, None, opcao.pesos, f"Churrasco {opcao.titulo}",
                            fora)
            app.novo_plano(montar_plano(pedido, app.parametros(), app.config.precos), {}, "")
        return tratador

    sem = f" Sem {' e '.join(s.lower() for s in fora)}." if fora else ""
    controles: list[ft.Control] = [
        w.subtitulo(f"Para {convidados.pessoas} pessoas, com bebida e carvão.{sem}"),
        w.dica("Toque na opção que você quer.")]
    controles += [_cartao_de_opcao(c, escolher(c.opcao))
                  for c in calcular_opcoes(convidados, app.parametros(), app.config.precos,
                                           fora)]
    return w.Tela(controles, topo=_topo(app, ESCOLHA), rodape=_rodape(app, ESCOLHA, erro))


def montar(app: AppChurrasco, passo: int) -> w.Tela:
    passos = (_passo_precos, _passo_quem_vem, _passo_quando, _passo_escolha)
    return passos[max(0, min(passo, len(passos) - 1))](app)
