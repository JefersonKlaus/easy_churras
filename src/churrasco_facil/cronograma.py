"""Cronograma de trás para frente a partir da hora de servir.

Cada etapa é um lembrete simples, de uma linha. Na véspera: comprar, passar a carne do
congelador para a geladeira e gelar as bebidas. No dia: acender o carvão, pôr cada carne na
grelha (começando pelo porco) e tirar cada uma, esperando uns minutos antes de servir.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable

from .catalogo_carnes import CORTES_DE_PORCO, VEGETARIANO, Corte

MINUTOS_PARA_BRASA = 50       # tempo até a brasa ficar coberta de cinza branca
MINUTOS_FORA_DA_GELADEIRA = 30
MINUTOS_PORCO_ANTES = 20      # o porco vai para a grelha pelo menos 20 min antes das outras


@dataclass(frozen=True)
class Etapa:
    hora: datetime
    titulo: str
    detalhe: str
    tipo: str           # compras, preparo, fogo, grelha, servir, depois (dá a cor na tela)
    chave: str = ""     # qual etapa é: compras, descongelar, bebidas, farofa, carvao,
    #                     geladeira, grelha, descansar, servir ou limpar
    categoria: str = ""  # categoria do corte, nas etapas de um corte
    resumo: str = ""     # a linha curta, quando a etapa aparece junto com outras num cartão


def _antes(servir: datetime, minutos: int) -> datetime:
    return servir - timedelta(minutes=minutos)


def inicio_do_corte(servir: datetime, corte: Corte) -> datetime:
    """Quando o corte vai para a grelha para ficar pronto (e descansado) na hora de servir."""
    return _antes(servir, corte.tempo_minutos + corte.descanso_minutos)


def inicios_na_grelha(servir: datetime, cortes: Iterable[Corte]) -> dict[str, datetime]:
    """A hora de cada corte ir para a grelha. Cada um fica pronto na hora de servir, mas o
    porco começa primeiro: pelo menos MINUTOS_PORCO_ANTES antes das outras carnes (e vira
    petisco enquanto o resto assa)."""
    inicios = {c.id: inicio_do_corte(servir, c) for c in cortes}
    outras = [h for i, h in inicios.items() if i not in CORTES_DE_PORCO]
    if outras:
        limite = min(outras) - timedelta(minutes=MINUTOS_PORCO_ANTES)
        for i in inicios:
            if i in CORTES_DE_PORCO:
                inicios[i] = min(inicios[i], limite)
    return inicios


def _vespera(hora_servir: datetime, com_cerveja: bool) -> list[Etapa]:
    dia = (hora_servir - timedelta(days=1)).replace(second=0, microsecond=0)
    return [
        Etapa(dia.replace(hour=17, minute=0), "Comprar tudo da lista",
              "Guarde a carne na geladeira (ou no congelador), bem embalada.", "compras",
              "compras"),
        Etapa(dia.replace(hour=18, minute=0), "Passar a carne do congelador para a geladeira",
              "Se a carne estiver congelada: ela descongela aos poucos, sem sair do frio. "
              "Nunca descongele na pia.", "preparo", "descongelar"),
        Etapa(dia.replace(hour=18, minute=0),
              "Colocar a cerveja na geladeira" if com_cerveja
              else "Colocar os refrigerantes na geladeira",
              "Os refrigerantes e a água também. Bebida demora para gelar: por isso, na "
              "véspera." if com_cerveja else "E a água também. Bebida demora para gelar: por "
              "isso, na véspera.", "preparo", "bebidas"),
    ]


def gerar_cronograma(hora_servir: datetime, cortes: Iterable[Corte],
                     com_cerveja: bool = True) -> list[Etapa]:
    """Devolve as etapas em ordem de hora."""
    cortes = list(cortes)
    inicios = inicios_na_grelha(hora_servir, cortes)
    cortes.sort(key=lambda c: inicios[c.id])
    etapas = _vespera(hora_servir, com_cerveja)
    etapas.append(Etapa(_antes(hora_servir, 120), "Preparar a farofa",
                        "Deixe a farofa pronta antes de a carne chegar à grelha.", "preparo",
                        "farofa"))
    if cortes:
        primeiro = inicios[cortes[0].id]
        etapas.append(Etapa(primeiro - timedelta(minutes=MINUTOS_PARA_BRASA), "Acender o carvão",
                            "Espere a brasa ficar coberta de cinza branca (uns 40 a 50 "
                            "minutos) antes de colocar carne.", "fogo", "carvao"))
        etapas.append(Etapa(primeiro - timedelta(minutes=MINUTOS_FORA_DA_GELADEIRA),
                            "Tirar a carne da geladeira",
                            "Só o que vai para a grelha agora. O resto continua gelado.",
                            "preparo", "geladeira"))
    for corte in cortes:
        inicio = inicios[corte.id]
        tempero = "Tempere com sal grosso na hora. " if corte.categoria != VEGETARIANO else ""
        # na hora de grelhar, as dicas de preparo: tempo, ponto e o conselho do corte
        detalhe = " ".join(p for p in (tempero + f"Cerca de {corte.tempo_minutos} min.",
                                       corte.ponto, corte.preparo) if p)
        etapas.append(Etapa(inicio, f"Na grelha: {corte.nome}", detalhe, "grelha", "grelha",
                            corte.categoria, resumo=corte.nome))
        pronto = inicio + timedelta(minutes=corte.tempo_minutos)
        cedo = pronto + timedelta(minutes=corte.descanso_minutos) < hora_servir
        petisco = " Ficou pronto antes: sirva de petisco." if cedo else ""
        if corte.descanso_minutos:
            etapas.append(Etapa(pronto, f"Tirar e esperar {corte.descanso_minutos} min: "
                                        f"{corte.nome}",
                                "Espere antes de cortar e servir: o caldo fica na carne."
                                + petisco, "grelha", "descansar", corte.categoria,
                                resumo=f"{corte.nome} · esperar {corte.descanso_minutos} min"))
        elif cedo:
            etapas.append(Etapa(pronto, f"Tirar e servir: {corte.nome}", petisco.strip(),
                                "grelha", "descansar", corte.categoria,
                                resumo=f"{corte.nome} · servir"))
    etapas.append(Etapa(hora_servir, "Servir!", "Corte a carne contra a fibra e sirva "
                        "aos poucos para ela não esfriar.", "servir", "servir",
                        resumo="Servir!"))
    etapas.append(Etapa(hora_servir + timedelta(hours=3), "Apagar e limpar",
                        "Deixe a brasa esfriar por completo antes de descartar.", "depois",
                        "limpar"))
    return sorted(etapas, key=lambda e: e.hora)
