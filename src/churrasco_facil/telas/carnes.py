"""Aba Carnes: as carnes do churrasco, já com as melhores da opção escolhida marcadas. A pessoa
pode marcar e desmarcar à vontade: a carne marcada sobe para "No seu churrasco" e a
desmarcada desce para "Outras carnes". Custo, compras e horários se refazem na hora.

No alto da tela (fixo, à vista mesmo com a lista rolada), uma faixa diz se a carne escolhida
está certa para o grupo: vermelha se falta, verde se está certa e amarela se é demais.
Tocar numa carne mostra o que combina com ela e como escolher na hora de comprar (como
preparar fica nos Horários). O botão Salvar fica embaixo, em todas as abas.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

import flet as ft

from ..catalogo_carnes import VEGETARIANO, Corte, cortes_de_carne
from ..dinheiro import formatar_reais
from ..lista_compras import formatar_peso, formatar_quantidade
from ..planejador import FALTA, SOBRA, Plano
from . import navegacao
from . import tema as t
from . import widgets as w

if TYPE_CHECKING:
    from ..app import AppChurrasco


def _dica(rotulo: str, texto: str) -> ft.Control:
    """Uma dica com o rótulo na frente: 'Combina com: Farofa...'."""
    return ft.Text(f"{rotulo}: {texto}", size=14, color=t.TEXTO, text_align=w.CENTRO)


def _dicas(corte: Corte) -> list[ft.Control]:
    """O que aparece ao tocar numa carne, só dicas de escolha: como é vendida, o que combina
    e como escolher na hora de comprar. Como preparar fica nos Horários; como pedir ao
    açougueiro, nas Compras."""
    dicas: list[ft.Control] = [
        w.dica(f"Vendido por {corte.embalagem}, de cerca de {formatar_peso(corte.peca_g)}")]
    if corte.combina_com:
        dicas.append(_dica("Combina com", corte.combina_com))
    if corte.como_escolher:
        dicas.append(_dica("Na hora de comprar", corte.como_escolher))
    return dicas


# nível do alerta -> (cor do texto e do ícone, fundo, borda, ícone)
FALTA_CARNE, CARNE_CERTA, CARNE_DEMAIS = "falta", "certa", "demais"
CORES_DO_ALERTA = {
    FALTA_CARNE: (t.PERIGO, t.PERIGO_CLARO, t.PERIGO_BORDA, ft.Icons.ERROR_OUTLINE),
    CARNE_CERTA: (t.CERTO, t.CERTO_CLARO, t.CERTO_BORDA, ft.Icons.CHECK_CIRCLE_OUTLINE),
    CARNE_DEMAIS: (t.ATENCAO, t.ATENCAO_CLARO, t.ATENCAO_BORDA, ft.Icons.WARNING_AMBER),
}


def alerta_da_carne(plano: Plano) -> tuple[str, str]:
    """(nível, texto) do alerta: vermelho se falta carne, verde se está certa (inclusive um
    pouco a mais, normal com peças inteiras) e amarelo se é carne demais."""
    comprada = formatar_peso(plano.gramas_de_carne)
    indicada = formatar_peso(plano.carne_indicada_g)
    pessoas = plano.pedido.convidados.pessoas
    situacao = plano.situacao_da_carne()
    if situacao == FALTA:
        return FALTA_CARNE, (f"Falta carne: {comprada} para {pessoas} pessoas, e o indicado é "
                             f"{indicada}. Marque mais uma carne.")
    if situacao == SOBRA:
        return CARNE_DEMAIS, (f"Carne demais: {comprada} para {pessoas} pessoas, e o indicado é "
                              f"{indicada}. Desmarque alguma carne.")
    if plano.gramas_de_carne > plano.carne_indicada_g:
        return CARNE_CERTA, (f"Carne certa: {comprada} para {pessoas} pessoas. Um pouco mais "
                             f"que o indicado ({indicada}), tudo bem.")
    return CARNE_CERTA, (f"Carne certa: {comprada} para {pessoas} pessoas "
                         f"(o indicado é {indicada}).")


class _Alerta:
    """Faixa fixa no alto da tela que diz se a carne está certa: vermelha (falta), verde
    (certa) ou amarela (demais)."""

    def __init__(self, plano: Plano) -> None:
        self._texto = ft.Text("", size=14, weight=ft.FontWeight.W_600, text_align=w.CENTRO,
                              expand=True)
        self._icone = ft.Icon(icon=ft.Icons.CHECK_CIRCLE_OUTLINE, size=22)
        self.controle = ft.Container(
            content=ft.Row(controls=[self._icone, self._texto],
                           vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=12, border_radius=t.RAIO)
        self.mostrar(plano)

    def mostrar(self, plano: Plano) -> None:
        self.avisar(*alerta_da_carne(plano))

    def avisar(self, nivel: str, texto: str) -> None:
        cor, fundo, borda, icone = CORES_DO_ALERTA[nivel]
        self.nivel = nivel
        self._texto.value, self._texto.color = texto, cor
        self._icone.icon, self._icone.color = icone, cor
        self.controle.bgcolor, self.controle.border = fundo, ft.Border.all(1, borda)


class _Resumo:
    """Os números do churrasco logo no começo: quanto custa e para quantos. Os textos são
    trocados no lugar quando as carnes mudam, sem redesenhar a tela."""

    def __init__(self, plano: Plano) -> None:
        self._total = ft.Text("", size=30, weight=ft.FontWeight.W_700, color=t.PRIMARIA,
                              text_align=w.CENTRO)
        self._por_pessoa = ft.Text("", size=15, color=t.TEXTO, text_align=w.CENTRO)
        self._grupo = w.dica("")
        self.controle = w.cartao([self._total, self._por_pessoa, self._grupo],
                                 fundo=t.PRIMARIA_CLARA, borda=t.PRIMARIA_CLARA)
        self.mostrar(plano)

    def mostrar(self, plano: Plano) -> None:
        self._total.value = formatar_reais(plano.custo_total)
        self._por_pessoa.value = "total com carnes, bebidas e carvão"
        self._grupo.value = (f"{formatar_reais(plano.custo_por_pessoa)} por pessoa · "
                             f"{formatar_peso(plano.gramas_de_carne)} de carne")


class _Carnes:
    """As carnes para marcar, em dois grupos: as marcadas em cima ("No seu churrasco") e as
    outras embaixo. Marcar leva a carne para o fim das marcadas; desmarcar, para as outras."""

    def __init__(self, app: AppChurrasco, ao_mudar: Callable[[], None],
                 avisar: Callable[[str, str], None]) -> None:
        self.app, self._ao_mudar, self._avisar = app, ao_mudar, avisar
        plano = app.plano
        assert plano is not None
        compradas = {i.produto.id: i.produto for i in plano.compras.carnes}
        self._cortes = {**compradas, **{c.id: c for c in cortes_de_carne()
                                        if c.id not in compradas}}
        self._marcar: dict[str, ft.Checkbox] = {}
        self._quanto: dict[str, ft.Text] = {}
        self._cartoes = {id: self._cartao(corte) for id, corte in self._cortes.items()}
        self._titulo_marcadas = w.secao("No seu churrasco")
        self._titulo_outras = w.secao("Outras carnes")
        self.lista = ft.Column(spacing=t.ESPACO,
                               horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
        self.mostrar(plano)

    def _cartao(self, corte: Corte) -> ft.Control:
        self._marcar[corte.id] = ft.Checkbox(value=False, on_change=self._trocar(corte.id),
                                             active_color=t.PRIMARIA,
                                             semantics_label=f"Levar {corte.nome}")
        self._quanto[corte.id] = ft.Text("", size=16, weight=ft.FontWeight.W_700,
                                         color=t.PRIMARIA)
        cabeca = ft.Row(controls=[
            self._marcar[corte.id],
            ft.Text(corte.nome, size=17, weight=ft.FontWeight.W_600, expand=True,
                    color=t.TEXTO),
            self._quanto[corte.id],
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER)
        return w.expansivel([cabeca], _dicas(corte), self.app.atualizar, "dicas")

    def marcadas(self) -> list[str]:
        """As carnes marcadas, na ordem em que aparecem."""
        return [id for id in self._ordem if self._marcar[id].value]

    def mostrar(self, plano: Plano) -> None:
        """Marca o que está na compra, diz quanto de cada um e põe cada carne no seu grupo."""
        compradas = {i.produto.id: i for i in plano.compras.carnes}
        for id, caixa in self._marcar.items():
            item = compradas.get(id)
            caixa.value = item is not None
            self._quanto[id].value = formatar_quantidade(item) if item else ""
            self._quanto[id].visible = item is not None
        outras = [id for id in self._cortes if id not in compradas]
        self._ordem = list(compradas) + outras
        self.lista.controls = [self._titulo_marcadas,
                               *(self._cartoes[id] for id in compradas),
                               self._titulo_outras,
                               *(self._cartoes[id] for id in outras)]

    def _trocar(self, id: str) -> Callable[[Any], None]:
        def tratador(evento: Any) -> None:
            antes = [i for i in self._ordem if i != id and self._marcar[i].value]
            if not evento.control.value:              # desmarcou
                if not antes:                         # sem nenhuma carne não há churrasco
                    evento.control.value = True
                    self._avisar(FALTA_CARNE, "Deixe pelo menos uma carne marcada.")
                    self.app.atualizar()
                    return
                self.app.trocar_cortes(antes)
            else:                                     # marcou: vai para o fim das marcadas
                self.app.trocar_cortes([*antes, id])
            self._ao_mudar()
        return tratador


def _vegetarianos(plano: Plano, atualizar: Callable[[], None]) -> list[ft.Control]:
    """A grelha de quem não come carne: o app escolhe, aqui só se vê o que vai e as dicas."""
    itens = [i for i in plano.compras.itens
             if isinstance(i.produto, Corte) and i.produto.categoria == VEGETARIANO]
    if not itens:
        return []
    cartoes: list[ft.Control] = [w.secao("Para quem não come carne")]
    for item in itens:
        cabeca = ft.Row(controls=[
            ft.Text(item.produto.nome, size=17, weight=ft.FontWeight.W_600, expand=True,
                    color=t.TEXTO),
            ft.Text(formatar_quantidade(item), size=16, weight=ft.FontWeight.W_700,
                    color=t.PRIMARIA)])
        cartoes.append(w.expansivel([cabeca], _dicas(item.produto), atualizar, "dicas"))
    return cartoes


def montar(app: AppChurrasco) -> w.Tela:
    plano = app.plano
    if plano is None:
        return navegacao.sem_plano(app)
    rodape = navegacao.RodapeDoPlano(app)
    resumo = _Resumo(plano)
    alerta = _Alerta(plano)

    def carnes_mudaram() -> None:
        novo = app.plano
        assert novo is not None
        resumo.mostrar(novo)
        alerta.mostrar(novo)
        carnes.mostrar(novo)
        rodape.atualizar()
        app.atualizar()

    conv = plano.pedido.convidados
    controles: list[ft.Control] = [resumo.controle]
    if conv.comem_carne or conv.criancas:
        carnes = _Carnes(app, carnes_mudaram, alerta.avisar)
        controles.append(w.dica("Já marcamos as melhores carnes desta opção. Marque ou "
                                "desmarque para trocar. Toque numa carne para ver o que "
                                "combina e como comprar."))
        controles.append(carnes.lista)
    controles += _vegetarianos(plano, app.atualizar)
    return w.Tela(controles, topo=[*navegacao.cabecalho(app), alerta.controle],
                  rodape=rodape.controles)
