"""Passo 4: escolher o churrasco (Caprichado, Tradicional ou Simples), vendo o que cada
um compra de carne e quanto custa para o grupo."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

import flet as ft

from ...dinheiro import formatar_reais
from ...lista_compras import formatar_peso
from ...opcoes import Opcao, OpcaoCalculada, calcular_opcoes
from ...planejador import Pedido, montar_plano
from .. import tema as t
from .. import widgets as w
from . import comum as c

if TYPE_CHECKING:
    from ...app import AppChurrasco


def _em_texto(nomes: list[str]) -> str:
    """['Picanha', 'Maminha', 'Alcatra'] -> 'picanha, maminha e alcatra'."""
    nomes = [n.lower() for n in nomes]
    return " e ".join([", ".join(nomes[:-1]), nomes[-1]] if len(nomes) > 1 else nomes)


def _cartao_de_opcao(calculada: OpcaoCalculada, escolher: Callable[[Any], None]
                     ) -> ft.Control:
    """O nome da opção, o que se compra de carne (muda com o tamanho do grupo, porque a
    carne vem em peças inteiras) e quanto custa."""
    opcao, compras = calculada.opcao, calculada.compras
    carne = (f"{formatar_peso(compras.gramas_de_carne)} de carne: "
             f"{_em_texto([i.produto.nome for i in compras.carnes])}." if compras.carnes
             else "Sem carne: só a grelha vegetariana.")
    return w.cartao([
        ft.Text(opcao.titulo, size=21, weight=ft.FontWeight.W_700, color=t.TEXTO,
                text_align=w.CENTRO),
        ft.Text(opcao.descricao, size=15, color=t.SECUNDARIO, text_align=w.CENTRO),
        ft.Text(carne, size=14, color=t.TEXTO, text_align=w.CENTRO),
        ft.Text(f"{formatar_reais(calculada.custo_total)} no total · "
                f"{formatar_reais(calculada.custo_por_pessoa)} por pessoa", size=17,
                weight=ft.FontWeight.W_700, color=t.PRIMARIA, text_align=w.CENTRO),
    ], on_click=escolher)


def montar(app: AppChurrasco) -> w.Tela:
    r = app.rascunho
    erro = w.erro("")
    try:
        convidados = r.para_convidados()
    except ValueError as problema:
        erro.value = str(problema)
        return w.Tela([], topo=c.topo(app, c.ESCOLHA), rodape=c.rodape(app, c.ESCOLHA, erro))

    def escolher(opcao: Opcao) -> Callable[[Any], None]:
        def tratador(_evento: Any) -> None:
            try:
                hora = r.para_data_hora()
            except ValueError as problema:
                erro.value = str(problema)
                app.atualizar()
                return
            pedido = Pedido(convidados, hora, pesos_preferidos=opcao.pesos,
                            nome=f"Churrasco {opcao.titulo}")
            app.novo_plano(montar_plano(pedido, app.parametros(), app.config.precos))
        return tratador

    controles: list[ft.Control] = [
        w.subtitulo(f"Para {convidados.pessoas} pessoas, com bebidas e carvão."),
        w.dica("Toque na opção que você quer. Depois dá para trocar as carnes.")]
    controles += [_cartao_de_opcao(c, escolher(c.opcao))
                  for c in calcular_opcoes(convidados, app.parametros(), app.config.precos)]
    return w.Tela(controles, topo=c.topo(app, c.ESCOLHA), rodape=c.rodape(app, c.ESCOLHA, erro))
