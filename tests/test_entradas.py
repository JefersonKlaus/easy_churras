from datetime import date, datetime, time

import pytest

from churrasco_facil.entradas import (Rascunho, combinar, formatar_data, ler_data, ler_hora,
                                      ler_orcamento, proximo_sabado)

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
def test_data_invalida(texto):
    with pytest.raises(ValueError):
        ler_data(texto, HOJE)


@pytest.mark.parametrize("texto, esperado", [
    ("14:00", time(14, 0)), ("14h", time(14, 0)), ("14h30", time(14, 30)),
    ("9", time(9, 0)), ("14:", time(14, 0)), (" 8.15 ", time(8, 15)),
])
def test_ler_hora(texto, esperado):
    assert ler_hora(texto) == esperado


@pytest.mark.parametrize("texto", ["", "abc", "25:00", "14:60", "1:2:3", "-1"])
def test_hora_invalida(texto):
    with pytest.raises(ValueError):
        ler_hora(texto)


def test_orcamento():
    assert ler_orcamento("") is None and ler_orcamento("   ") is None
    assert ler_orcamento("0") is None
    assert ler_orcamento("R$ 450,50") == 45050
    with pytest.raises(ValueError):
        ler_orcamento("muito")


def test_proximo_sabado():
    assert proximo_sabado(date(2026, 11, 17)) == date(2026, 11, 21)
    assert proximo_sabado(date(2026, 11, 21)) == date(2026, 11, 21)
    assert proximo_sabado(date(2026, 11, 22)) == date(2026, 11, 28)
    assert formatar_data(date(2026, 11, 5)) == "05/11/2026"
    assert combinar(date(2026, 11, 21), time(14, 0)) == datetime(2026, 11, 21, 14, 0)


def test_rascunho_padrao_e_limites():
    r = Rascunho()
    assert r.data_texto and r.hora_texto == "14:00"
    r.adultos, r.vegetarianos, r.bebem_alcool = 2, 5, 9
    r.ajustar_limites()
    assert (r.vegetarianos, r.bebem_alcool) == (2, 2)


def test_rascunho_vira_convidados_e_valida():
    r = Rascunho(adultos=4, criancas=1, vegetarianos=1, bebem_alcool=2, duracao_horas=5)
    c = r.para_convidados()
    assert (c.adultos, c.criancas, c.vegetarianos, c.bebem_alcool, c.duracao_horas) == \
        (4, 1, 1, 2, 5.0)
    r.adultos, r.criancas = 0, 0
    with pytest.raises(ValueError):
        r.para_convidados()


def test_data_hora_no_passado_e_recusada():
    agora = datetime(2026, 11, 17, 10, 0)
    r = Rascunho(data_texto="17/11/2026", hora_texto="09:00")
    with pytest.raises(ValueError):
        r.para_data_hora(agora)
    r.hora_texto = "18:30"
    assert r.para_data_hora(agora) == datetime(2026, 11, 17, 18, 30)


def test_aplicar_interpretacao_so_muda_o_que_veio():
    r = Rascunho(adultos=8, criancas=2, vegetarianos=0, bebem_alcool=4)
    mudou = r.aplicar_interpretacao(12, None, 20, None, 4.4, 40000)
    assert r.adultos == 12 and r.criancas == 2 and r.bebem_alcool == 4
    assert r.vegetarianos == 12                      # limitado ao número de adultos
    assert r.duracao_horas == 4 and r.orcamento_texto == "400,00"
    assert "12 adultos" in mudou and "orçamento R$ 400,00" in mudou
    assert Rascunho().aplicar_interpretacao(None, None, None, None, None, None) == []
