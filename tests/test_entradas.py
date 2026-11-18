from datetime import date, datetime, time

import pytest

from churrasco_facil.entradas import (Rascunho, combinar, formatar_data, ler_data, ler_hora,
                                      proximo_sabado)

HOJE = date(2026, 11, 17)   # uma terça-feira
AGORA = datetime(2026, 11, 17, 10, 0)
NADA = dict(adultos=None, criancas=None, vegetarianos=None, bebem_alcool=None,
            duracao_horas=None)


def interpretar(rascunho, **valores):
    return rascunho.aplicar_interpretacao(**{**NADA, **valores})


# ---------------------------------------------------------------- leitura dos campos

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


def test_combinar_data_e_hora():
    assert combinar(date(2026, 11, 21), time(14, 0)) == datetime(2026, 11, 21, 14, 0)


# ---------------------------------------------------------------- Rascunho

def test_rascunho_comeca_no_proximo_sabado_as_14h():
    r = Rascunho()
    assert (r.data_texto, r.hora_texto) == (formatar_data(proximo_sabado()), "14:00")


def test_ajustar_limites_mantem_vegetarianos_e_quem_bebe_entre_os_adultos():
    r = Rascunho(adultos=2, vegetarianos=5, bebem_alcool=9)
    r.ajustar_limites()
    assert (r.vegetarianos, r.bebem_alcool) == (2, 2)


def test_rascunho_vira_convidados():
    c = Rascunho(adultos=4, criancas=1, vegetarianos=1, bebem_alcool=2,
                 duracao_horas=5).para_convidados()
    assert (c.adultos, c.criancas, c.vegetarianos, c.bebem_alcool, c.duracao_horas) == \
        (4, 1, 1, 2, 5.0)


def test_rascunho_sem_ninguem_nao_vira_convidados():
    with pytest.raises(ValueError):
        Rascunho(adultos=0, criancas=0).para_convidados()


def test_data_hora_no_futuro_e_aceita():
    r = Rascunho(data_texto="17/11/2026", hora_texto="18:30")
    assert r.para_data_hora(AGORA) == datetime(2026, 11, 17, 18, 30)


def test_data_hora_no_passado_e_recusada():
    r = Rascunho(data_texto="17/11/2026", hora_texto="09:00")
    with pytest.raises(ValueError):
        r.para_data_hora(AGORA)


def test_aplicar_interpretacao_so_muda_o_que_veio():
    r = Rascunho(adultos=8, criancas=2, bebem_alcool=4)
    interpretar(r, adultos=12)
    assert (r.adultos, r.criancas, r.bebem_alcool) == (12, 2, 4)


def test_aplicar_interpretacao_respeita_os_limites_dos_adultos():
    r = Rascunho(adultos=8)
    interpretar(r, vegetarianos=20)
    assert r.vegetarianos == 8


def test_aplicar_interpretacao_arredonda_a_duracao():
    r = Rascunho()
    interpretar(r, duracao_horas=4.4)
    assert r.duracao_horas == 4


def test_aplicar_interpretacao_descreve_o_que_mudou():
    assert interpretar(Rascunho(), adultos=12, criancas=3) == ["12 adultos", "3 crianças"]


def test_aplicar_interpretacao_descreve_a_duracao_como_tempo_de_festa():
    assert interpretar(Rascunho(), duracao_horas=5) == ["festa de 5 horas"]


def test_aplicar_interpretacao_vazia_nao_muda_nada():
    assert interpretar(Rascunho()) == []


def test_rascunho_comeca_com_tudo_na_conta():
    assert Rascunho().secoes_fora == set()
