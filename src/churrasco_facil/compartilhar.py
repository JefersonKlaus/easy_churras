"""Textos prontos para colar no WhatsApp (negrito com asteriscos)."""
from __future__ import annotations

from .cronograma import formatar_hora
from .dinheiro import formatar_reais
from .lista_compras import agrupar_por_secao, formatar_quantidade
from .planejador import Plano, descrever_data


def texto_resumo(plano: Plano) -> str:
    conv = plano.pedido.convidados
    linhas = [f"*{plano.pedido.nome}*",
              f"{descrever_data(plano.pedido.hora_servir)}",
              f"{conv.adultos} adultos e {conv.criancas} crianças",
              f"Custo estimado: {formatar_reais(plano.custo_total)} "
              f"({formatar_reais(plano.custo_por_pessoa)} por pessoa)"]
    if plano.compras.estourou:
        linhas.append(f"Atenção: passa {formatar_reais(plano.compras.excedente)} do orçamento.")
    return "\n".join(linhas)


def texto_lista(plano: Plano) -> str:
    blocos = ["*Lista de compras*"]
    for secao, itens in agrupar_por_secao(plano.compras.itens).items():
        blocos.append(f"\n*{secao}*")
        blocos.extend(f"- {i.produto.nome}: {formatar_quantidade(i)}" for i in itens)
    return "\n".join(blocos)


def texto_cronograma(plano: Plano) -> str:
    linhas = ["*Horários*"]
    linhas.extend(f"{formatar_hora(e.hora)} - {e.titulo}" for e in plano.cronograma
                  if e.tipo != "depois")
    return "\n".join(linhas)


def texto_whatsapp(plano: Plano) -> str:
    """Resumo, lista de compras e horários, nessa ordem."""
    return "\n\n".join([texto_resumo(plano), texto_lista(plano), texto_cronograma(plano)])
