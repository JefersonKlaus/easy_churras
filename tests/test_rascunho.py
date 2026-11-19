"""O rascunho do planejamento: o que a pessoa contou nos passos."""
from datetime import datetime

import pytest

from churrasco_facil.entradas import formatar_data, proximo_sabado
from churrasco_facil.rascunho import Rascunho

AGORA = datetime(2026, 11, 17, 10, 0)


NADA = dict(adultos=None, criancas=None, vegetarianos=None, bebem_alcool=None,
            duracao_horas=None)


def interpretar(rascunho, **valores):
    return rascunho.aplicar_interpretacao(**{**NADA, **valores})


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
