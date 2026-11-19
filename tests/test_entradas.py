"""Leitura do que a pessoa digita: datas e horas."""
from datetime import date, time

import pytest

from churrasco_facil.entradas import formatar_data, ler_data, ler_hora, proximo_sabado

HOJE = date(2026, 11, 17)   # uma terça-feira


@pytest.mark.parametrize("texto, esperado", [
    ("21/11/2026", date(2026, 11, 21)), ("21-11-2026", date(2026, 11, 21)),
    ("21.11.2026", date(2026, 11, 21)), ("5/1/27", date(2027, 1, 5)),
    ("21/11", date(2026, 11, 21)), ("17/11", date(2026, 11, 17)),
    ("1/1", date(2027, 1, 1)),                       # sem ano e já passou: ano que vem
])
def test_ler_data(texto, esperado):
    assert ler_data(texto, HOJE) == esperado


@pytest.mark.parametrize("texto", ["", "abc", "31/02/2026", "1/2/3/4", "32/1/2026", "10/13/2026"])
def test_ler_data_recusa_data_invalida(texto):
    with pytest.raises(ValueError):
        ler_data(texto, HOJE)


@pytest.mark.parametrize("texto, esperado", [
    ("14:00", time(14, 0)), ("14h", time(14, 0)), ("14h30", time(14, 30)),
    ("9", time(9, 0)), ("14:", time(14, 0)), (" 8.15 ", time(8, 15)),
])
def test_ler_hora(texto, esperado):
    assert ler_hora(texto) == esperado


@pytest.mark.parametrize("texto", ["", "abc", "25:00", "14:60", "1:2:3", "-1"])
def test_ler_hora_recusa_hora_invalida(texto):
    with pytest.raises(ValueError):
        ler_hora(texto)


@pytest.mark.parametrize("hoje, sabado", [
    (date(2026, 11, 17), date(2026, 11, 21)),       # terça
    (date(2026, 11, 21), date(2026, 11, 21)),       # o próprio sábado
    (date(2026, 11, 22), date(2026, 11, 28)),       # domingo
])
def test_proximo_sabado(hoje, sabado):
    assert proximo_sabado(hoje) == sabado


def test_formatar_data():
    assert formatar_data(date(2026, 11, 5)) == "05/11/2026"
