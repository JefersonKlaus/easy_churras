"""Junta tudo: do pedido (quem vem, quando, a opção e as carnes) ao plano completo: compras,
horários e avisos. Também diz se a carne escolhida está certa para o grupo."""
from __future__ import annotations

from dataclasses import KW_ONLY, dataclass, field, replace
from datetime import datetime
from typing import Iterable, Mapping, Optional

from .calculadora import gramas_de_carne, itens_para_lembrar
from .catalogo_carnes import CORTES, Corte
from .compras import Compras, custo_por_pessoa, planejar_compras
from .convidados import Convidados
from .cronograma import Etapa, gerar_cronograma
from .parametros import Parametros
from .pecas import FOLGA_PERCENTUAL, ajustar_pecas
from .produtos import ItemPlano
from .seguranca import Aviso, avisos_para

FALTA, SOBRA = "falta", "sobra"          # situacao_da_carne()
SOBRA_PERCENTUAL = 25                    # acima disso (e com peça a mais), é carne demais


@dataclass(frozen=True)
class Pedido:
    """O que o usuário informou. É só isso que precisa ser salvo: o plano é recalculado."""

    convidados: Convidados
    hora_servir: datetime
    _: KW_ONLY                           # o resto só por nome: nada troca de lugar sem querer
    pesos_preferidos: dict[str, int] = field(default_factory=dict)   # a mistura da opção
    nome: str = "Meu churrasco"
    # Carnes que a pessoa marcou: id do corte -> peças. Vazio: o app escolhe as melhores
    # da opção (os `pesos_preferidos`).
    pecas_escolhidas: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class Plano:
    pedido: Pedido
    compras: Compras
    cortes: list[Corte]
    cronograma: list[Etapa]
    avisos: list[Aviso]
    lembretes: list[ItemPlano] = field(default_factory=list)   # fora da conta
    carne_indicada_g: int = 0          # quanto de carne o grupo precisa (a conta por pessoa)

    @property
    def custo_total(self) -> int:
        return self.compras.custo_total

    @property
    def custo_por_pessoa(self) -> int:
        return custo_por_pessoa(self.compras.custo_total, self.pedido.convidados.pessoas)

    @property
    def gramas_de_carne(self) -> int:
        """Quanto de carne o plano compra (sem contar a grelha vegetariana)."""
        return self.compras.gramas_de_carne

    def situacao_da_carne(self) -> str:
        """FALTA, SOBRA ou "" (na medida), comparando a carne comprada com a indicada.

        - FALTA: menos que o indicado, além da folga de FOLGA_PERCENTUAL.
        - SOBRA: passou mais de SOBRA_PERCENTUAL do indicado e dá para tirar uma peça
          inteira (de qualquer carne) e ainda ter todo o indicado. Com peças inteiras é normal
          passar um pouco; isso não conta como sobra.
        """
        indicada, comprada = self.carne_indicada_g, self.gramas_de_carne
        if indicada <= 0:
            return ""
        minimo = indicada - indicada * FOLGA_PERCENTUAL // 100
        if comprada < minimo:
            return FALTA
        passou = comprada - indicada > indicada * SOBRA_PERCENTUAL // 100
        if passou and any(comprada - i.produto.peca_g >= indicada for i in self.compras.carnes):
            return SOBRA
        return ""


def cortes_do_plano(itens: list[ItemPlano]) -> list[Corte]:
    """Cortes que vão à grelha: os que foram comprados. Como se compra em peças inteiras, um
    grupo pequeno pode não levar todos os cortes da mistura; horários e avisos seguem a
    compra, para não mandar grelhar (nem avisar sobre) o que ninguém comprou."""
    return [i.produto for i in itens if isinstance(i.produto, Corte)]


def montar_plano(pedido: Pedido, par: Optional[Parametros] = None,
                 precos: Optional[Mapping[str, int]] = None) -> Plano:
    """Calcula compras, cronograma e avisos. Mesmo pedido, mesmo plano, sempre."""
    compras = planejar_compras(pedido.convidados, par, precos, pedido.pesos_preferidos or None,
                               pedido.pecas_escolhidas or None)
    cortes = cortes_do_plano(compras.itens)
    return Plano(
        pedido=pedido,
        compras=compras,
        cortes=cortes,
        cronograma=gerar_cronograma(pedido.hora_servir, cortes,
                                    com_cerveja=pedido.convidados.bebem_alcool > 0),
        avisos=avisos_para(cortes),
        lembretes=itens_para_lembrar(pedido.convidados, par),
        carne_indicada_g=gramas_de_carne(pedido.convidados, par or Parametros()),
    )


def trocar_carnes(plano: Plano, marcadas: Iterable[str],
                  par: Optional[Parametros] = None) -> Pedido:
    """O pedido com as carnes que a pessoa deixou marcadas (na ordem da lista). Só muda a
    carne marcada ou desmarcada (`ajustar_pecas`); se faltar ou sobrar carne, a tela avisa."""
    pedido = plano.pedido
    ids = [i for i in dict.fromkeys(marcadas) if i in CORTES]
    atuais = {i.produto.id: -(-i.quantidade // i.produto.peca_g) for i in plano.compras.carnes}
    pecas = ajustar_pecas(atuais, ids, gramas_de_carne(pedido.convidados, par or Parametros()),
                          {i: CORTES[i].peca_g for i in ids})
    return replace(pedido, pecas_escolhidas=pecas)
