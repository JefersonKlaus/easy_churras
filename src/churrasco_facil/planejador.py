"""Junta tudo: do pedido (quem vem, quando, quanto) ao plano completo, sem usar a IA."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Mapping, Optional

from .calculadora import Convidados, Parametros
from .catalogo_carnes import CORTES, MISTURA_VEGETARIANA, VEGETARIANO, Corte
from .cronograma import Etapa, formatar_hora, gerar_cronograma
from .dinheiro import formatar_reais
from .orcamento import ResultadoOrcamento, custo_por_pessoa, planejar_compras
from .seguranca import Aviso, avisos_para

DIAS_DA_SEMANA = ("segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo")


@dataclass(frozen=True)
class Pedido:
    """O que o usuário informou. É só isso que precisa ser salvo: o plano é recalculado."""

    convidados: Convidados
    hora_servir: datetime
    orcamento: Optional[int] = None                    # centavos, None = sem limite
    pesos_preferidos: dict[str, int] = field(default_factory=dict)
    nome: str = "Meu churrasco"


@dataclass(frozen=True)
class Plano:
    pedido: Pedido
    compras: ResultadoOrcamento
    cortes: list[Corte]
    cronograma: list[Etapa]
    avisos: list[Aviso]
    explicacao: Optional[str] = None

    @property
    def custo_total(self) -> int:
        return self.compras.custo_total

    @property
    def custo_por_pessoa(self) -> int:
        return custo_por_pessoa(self.compras.custo_total, self.pedido.convidados.pessoas)


def cortes_do_plano(pesos: Mapping[str, int], vegetarianos: int) -> list[Corte]:
    """Cortes que vão à grelha: os escolhidos e, se houver vegetarianos, as opções deles."""
    ids = [i for i in pesos if i in CORTES]
    if vegetarianos > 0:
        ids += list(MISTURA_VEGETARIANA)
    return [CORTES[i] for i in ids]


def montar_plano(pedido: Pedido, par: Optional[Parametros] = None,
                 precos: Optional[Mapping[str, int]] = None,
                 explicacao: Optional[str] = None) -> Plano:
    """Calcula compras, cronograma e avisos. Mesmo pedido, mesmo plano, sempre."""
    compras = planejar_compras(pedido.convidados, pedido.orcamento, par, precos,
                               pedido.pesos_preferidos or None)
    cortes = cortes_do_plano(compras.pesos, pedido.convidados.vegetarianos)
    return Plano(
        pedido=pedido,
        compras=compras,
        cortes=cortes,
        cronograma=gerar_cronograma(pedido.hora_servir, cortes),
        avisos=avisos_para(cortes),
        explicacao=explicacao,
    )


def descrever_data(hora: datetime) -> str:
    """'sábado, 21/11 às 14:00'."""
    return f"{DIAS_DA_SEMANA[hora.weekday()]}, {hora:%d/%m} às {formatar_hora(hora)}"


def resumo_pedido(conv: Convidados, orcamento: Optional[int]) -> str:
    """Texto curto com os números do grupo, para enviar ao Groq (sem nomes de pessoas)."""
    partes = [f"{conv.adultos} adultos", f"{conv.criancas} crianças",
              f"{conv.vegetarianos} vegetarianos", f"{conv.bebem_alcool} bebem álcool",
              f"duração {conv.duracao_horas:g} horas"]
    partes.append(f"orçamento {formatar_reais(orcamento)}" if orcamento else "sem orçamento")
    return "; ".join(partes)


def resumo_plano(plano: Plano) -> str:
    """O plano em texto, para dar contexto ao Groq. Só números que o código calculou."""
    linhas = [resumo_pedido(plano.pedido.convidados, plano.pedido.orcamento),
              f"Hora de servir: {descrever_data(plano.pedido.hora_servir)}"]
    carnes = [f"{i.produto.nome} ({i.quantidade} g)" for i in plano.compras.itens
              if isinstance(i.produto, Corte) and i.produto.categoria != VEGETARIANO]
    linhas.append("Carnes: " + (", ".join(carnes) if carnes else "nenhuma"))
    if plano.pedido.convidados.vegetarianos:
        veg = [i.produto.nome for i in plano.compras.itens
               if isinstance(i.produto, Corte) and i.produto.categoria == VEGETARIANO]
        linhas.append("Para vegetarianos: " + ", ".join(veg))
    linhas.append(f"Custo estimado: {formatar_reais(plano.custo_total)}"
                  + (" (acima do orçamento)" if plano.compras.estourou else ""))
    linhas.append("Avisos de segurança do app: "
                  + "; ".join(a.titulo for a in plano.avisos if a.grave))
    return "\n".join(linhas)
