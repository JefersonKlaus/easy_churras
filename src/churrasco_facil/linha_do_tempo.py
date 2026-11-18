"""Horários e cuidados juntos: cada aviso de segurança aparece na hora em que importa.

Ex.: "nunca use álcool" na hora de acender o carvão; "frango a 74 °C" quando o frango vai
para a grelha. Assim a pessoa sabe quando precisa tomar cada cuidado.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .catalogo_carnes import FRANGO, LINGUICA, SUINA
from .cronograma import Etapa
from .seguranca import Aviso

# id do aviso -> chave da etapa em que ele deve aparecer
ETAPA_DO_AVISO = {
    "monoxido": "carvao", "acendedor": "carvao", "criancas": "carvao",
    "tempo_fora": "geladeira", "crua_pronta": "servir", "cinzas": "limpar",
    "frango": "grelha", "porco": "grelha", "linguica": "grelha", "termometro": "grelha",
}
# avisos de um tipo de carne: aparecem quando aquele tipo vai para a grelha
CATEGORIA_DO_AVISO = {"frango": FRANGO, "porco": SUINA, "linguica": LINGUICA}


@dataclass(frozen=True)
class Momento:
    """Uma etapa do cronograma e os cuidados que valem naquela hora."""

    etapa: Etapa
    avisos: tuple[Aviso, ...] = ()


def _combina(aviso: Aviso, etapa: Etapa) -> bool:
    if ETAPA_DO_AVISO.get(aviso.id) != etapa.chave:
        return False
    categoria = CATEGORIA_DO_AVISO.get(aviso.id)
    return categoria is None or etapa.categoria == categoria


def linha_do_tempo(cronograma: list[Etapa], avisos: Iterable[Aviso]) -> list[Momento]:
    """Cada aviso vai para a primeira etapa em que ele importa, uma vez só.

    Um aviso sem etapa certa no plano vai para a primeira etapa, para nunca sumir.
    """
    por_etapa: list[list[Aviso]] = [[] for _ in cronograma]
    for aviso in avisos:
        destino = next((i for i, e in enumerate(cronograma) if _combina(aviso, e)), 0)
        if cronograma:
            por_etapa[destino].append(aviso)
    return [Momento(e, tuple(a)) for e, a in zip(cronograma, por_etapa, strict=True)]
