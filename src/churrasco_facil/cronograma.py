"""Cronograma de trás para frente a partir da hora de servir."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable

from .catalogo_carnes import VEGETARIANO, Corte

MINUTOS_PARA_BRASA = 50       # tempo até a brasa ficar coberta de cinza branca
MINUTOS_FORA_DA_GELADEIRA = 30
MINUTOS_TEMPERO = 15


@dataclass(frozen=True)
class Etapa:
    hora: datetime
    titulo: str
    detalhe: str
    tipo: str           # compras, preparo, fogo, grelha, servir, depois (dá a cor na tela)
    chave: str = ""     # qual etapa é: compras, bebidas, guarnicoes, carvao, geladeira,
    #                     temperar, grelha, descansar, servir ou limpar
    categoria: str = ""  # categoria do corte, nas etapas de um corte


def _antes(servir: datetime, minutos: int) -> datetime:
    return servir - timedelta(minutes=minutos)


def inicio_do_corte(servir: datetime, corte: Corte) -> datetime:
    """Quando o corte vai para a grelha para ficar pronto (e descansado) na hora de servir."""
    return _antes(servir, corte.tempo_minutos + corte.descanso_minutos)


def gerar_cronograma(hora_servir: datetime, cortes: Iterable[Corte]) -> list[Etapa]:
    """Devolve as etapas em ordem de hora."""
    cortes = sorted(cortes, key=lambda c: inicio_do_corte(hora_servir, c))
    etapas: list[Etapa] = []
    vespera = (hora_servir - timedelta(days=1)).replace(hour=17, minute=0, second=0,
                                                         microsecond=0)
    etapas.append(Etapa(vespera, "Comprar tudo", "Faça as compras na véspera e guarde a "
                        "carne na geladeira, bem embalada.", "compras", "compras"))
    etapas.append(Etapa(_antes(hora_servir, 180), "Colocar as bebidas no gelo",
                        "Bebida gelada demora: comece cedo.", "preparo", "bebidas"))
    etapas.append(Etapa(_antes(hora_servir, 120), "Preparar vinagrete, farofa e arroz",
                        "Deixe as guarnições prontas antes de a carne chegar à grelha.",
                        "preparo", "guarnicoes"))
    if cortes:
        primeiro = inicio_do_corte(hora_servir, cortes[0])
        etapas.append(Etapa(primeiro - timedelta(minutes=MINUTOS_PARA_BRASA),
                            "Acender o carvão",
                            "Espere a brasa ficar coberta de cinza branca (uns 40 a 50 "
                            "minutos) antes de colocar carne.", "fogo", "carvao"))
        etapas.append(Etapa(primeiro - timedelta(minutes=MINUTOS_FORA_DA_GELADEIRA),
                            "Tirar a carne da geladeira",
                            "Só o que vai para a grelha agora. O resto continua gelado.",
                            "preparo", "geladeira"))
    for corte in cortes:
        inicio = inicio_do_corte(hora_servir, corte)
        if corte.categoria != VEGETARIANO:
            etapas.append(Etapa(inicio - timedelta(minutes=MINUTOS_TEMPERO),
                                f"Temperar: {corte.nome}",
                                "Sal grosso na hora; não precisa de muito mais.", "preparo",
                                "temperar", corte.categoria))
        etapas.append(Etapa(inicio, f"Na grelha: {corte.nome}",
                            f"Cerca de {corte.tempo_minutos} min. {corte.ponto}", "grelha",
                            "grelha", corte.categoria))
        if corte.descanso_minutos:
            etapas.append(Etapa(_antes(hora_servir, corte.descanso_minutos),
                                f"Tirar e descansar: {corte.nome}",
                                f"Descanse {corte.descanso_minutos} min antes de cortar.",
                                "grelha", "descansar", corte.categoria))
    etapas.append(Etapa(hora_servir, "Servir!", "Corte a carne contra a fibra e sirva "
                        "aos poucos para ela não esfriar.", "servir", "servir"))
    etapas.append(Etapa(hora_servir + timedelta(hours=3), "Apagar e limpar",
                        "Deixe a brasa esfriar por completo antes de descartar.", "depois",
                        "limpar"))
    return sorted(etapas, key=lambda e: e.hora)


def formatar_hora(hora: datetime) -> str:
    return hora.strftime("%H:%M")
