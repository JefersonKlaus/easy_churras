"""O texto que se compartilha: a lista de compras, pronta para o WhatsApp (negrito com
asteriscos). É o que vai para quem for ao mercado."""
from __future__ import annotations

from .datas import descrever_data
from .dinheiro import formatar_reais
from .lista_compras import agrupar_por_secao, linha_do_item
from .planejador import Plano


def texto_compras(plano: Plano) -> str:
    """Qual churrasco, a lista por seção do mercado, o que não pode esquecer e o total."""
    pedido = plano.pedido
    blocos = [f"*{pedido.nome}*",
              f"{descrever_data(pedido.hora_servir)} · {pedido.convidados.pessoas} pessoas",
              "\n*Lista de compras*"]
    for secao, itens in agrupar_por_secao(plano.compras.itens).items():
        blocos.append(f"\n*{secao}*")
        blocos.extend(f"- {linha_do_item(i, com_preco=False)}" for i in itens)
    if plano.lembretes:
        blocos.append("\n*Não esqueça*")
        blocos.extend(f"- {linha_do_item(i, com_preco=False)}" for i in plano.lembretes)
    blocos.append(f"\nTotal estimado (carnes, bebidas e carvão): "
                  f"{formatar_reais(plano.custo_total)}")
    return "\n".join(blocos)
