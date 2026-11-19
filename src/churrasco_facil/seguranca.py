"""Regras de segurança fixas. Elas vêm do código e não da IA, porque não podem errar.

As temperaturas são referências de segurança alimentar amplamente adotadas (por exemplo,
as do USDA). Um termômetro de cozinha é a forma mais confiável de conferir.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .catalogo_carnes import FRANGO, LINGUICA, SUINA, Corte


@dataclass(frozen=True)
class Aviso:
    id: str
    titulo: str
    texto: str
    grave: bool = False   # avisos graves aparecem em destaque


AVISOS_GERAIS = (
    Aviso("monoxido", "Nunca use a churrasqueira em lugar fechado",
          "A brasa solta monóxido de carbono, um gás sem cheiro que pode matar. Use sempre ao "
          "ar livre, longe de portas e janelas.", True),
    Aviso("acendedor", "Não use álcool nem gasolina para acender",
          "Líquido inflamável causa queimaduras graves. Use acendedor sólido ou jornal.",
          True),
    Aviso("criancas", "Crianças longe da brasa",
          "Marque uma distância segura em volta da churrasqueira e deixe um adulto responsável "
          "por ela o tempo todo."),
    Aviso("crua_pronta", "Separe o que é cru do que é pronto",
          "Use tábuas, facas e travessas diferentes para carne crua e carne pronta. Lave as "
          "mãos depois de pegar carne crua."),
    Aviso("tempo_fora", "Carne crua não fica horas fora da geladeira",
          "No máximo 2 horas em temperatura ambiente, ou 1 hora em dia muito quente. Tire da "
          "geladeira só o que vai para a grelha logo."),
    Aviso("cinzas", "Depois da festa",
          "Deixe a brasa esfriar por completo (várias horas) antes de descartar. Brasa "
          "aparentemente apagada ainda queima."),
)

AVISO_FRANGO = Aviso("frango", "Frango precisa ficar bem passado",
                     "Frango nunca pode ficar rosado por dentro. Referência: 74 °C no ponto "
                     "mais grosso, longe do osso.", True)
AVISO_PORCO = Aviso("porco", "Carne de porco: bem passada, mas não seca",
                    "Referência: 63 °C no centro, depois descanse alguns minutos.")
AVISO_LINGUICA = Aviso("linguica", "Linguiça: sem parte rosada",
                       "Referência: 71 °C no centro. Fogo baixo para não queimar por fora e "
                       "ficar crua por dentro.")
AVISO_TERMOMETRO = Aviso("termometro", "Um termômetro de cozinha ajuda muito",
                         "Para quem está começando, é a forma mais segura de saber o ponto "
                         "sem cortar a carne.")


def avisos_para(cortes: Iterable[Corte]) -> list[Aviso]:
    """Avisos gerais mais os específicos dos tipos de carne que estão no plano."""
    categorias = {c.categoria for c in cortes}
    avisos = list(AVISOS_GERAIS)
    if FRANGO in categorias:
        avisos.append(AVISO_FRANGO)
    if SUINA in categorias:
        avisos.append(AVISO_PORCO)
    if LINGUICA in categorias:
        avisos.append(AVISO_LINGUICA)
    avisos.append(AVISO_TERMOMETRO)
    # graves primeiro, mantendo a ordem original dentro de cada grupo
    return sorted(avisos, key=lambda a: not a.grave)
