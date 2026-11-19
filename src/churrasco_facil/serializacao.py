"""O pedido em dicionário (JSON) e de volta. É o que fica salvo: o plano é recalculado.
A leitura aceita registros de versões antigas e descarta o que não for válido."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from .catalogo_carnes import CORTES
from .convidados import Convidados
from .planejador import Pedido


def pedido_para_dict(pedido: Pedido) -> dict[str, Any]:
    c = pedido.convidados
    return {
        "nome": pedido.nome,
        "hora_servir": pedido.hora_servir.isoformat(timespec="minutes"),
        "pesos_preferidos": pedido.pesos_preferidos,
        "pecas_escolhidas": pedido.pecas_escolhidas,
        "convidados": {"adultos": c.adultos, "criancas": c.criancas,
                       "vegetarianos": c.vegetarianos, "bebem_alcool": c.bebem_alcool,
                       "duracao_horas": c.duracao_horas},
    }


def pedido_de_dict(dados: dict[str, Any]) -> Pedido:
    """Reconstrói o pedido. Levanta ValueError se o registro estiver corrompido. Campos de
    versões antigas que o app não usa mais (orçamento, seções fora) ficam de fora."""
    try:
        conv = dados["convidados"]
        pesos = dados.get("pesos_preferidos") or {}
        escolhidas = dados.get("pecas_escolhidas") or {}    # planos antigos não têm
        return Pedido(
            convidados=Convidados(adultos=int(conv["adultos"]), criancas=int(conv["criancas"]),
                                  vegetarianos=int(conv["vegetarianos"]),
                                  bebem_alcool=int(conv["bebem_alcool"]),
                                  duracao_horas=float(conv["duracao_horas"])),
            hora_servir=datetime.fromisoformat(dados["hora_servir"]),
            pesos_preferidos={k: int(v) for k, v in pesos.items() if k in CORTES},
            nome=str(dados.get("nome") or "Meu churrasco")[:60],
            pecas_escolhidas={k: int(v) for k, v in escolhidas.items()
                              if k in CORTES and int(v) > 0},
        )
    except (KeyError, TypeError, AttributeError) as erro:
        raise ValueError(f"registro inválido: {erro}") from None
