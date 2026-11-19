"""Quem vem: a validação do grupo."""
import pytest

from churrasco_facil.convidados import Convidados


@pytest.mark.parametrize("dados", [
    dict(adultos=0), dict(adultos=-1), dict(adultos=2, criancas=-1),
    dict(adultos=2, vegetarianos=3), dict(adultos=2, bebem_alcool=3),
    dict(adultos=2, duracao_horas=0.5), dict(adultos=2, duracao_horas=13),
    dict(adultos=150, criancas=51),
])
def test_convidados_invalidos_levantam_valueerror(dados):
    with pytest.raises(ValueError):
        Convidados(**dados)


def test_grupo_so_de_criancas_e_permitido():
    assert Convidados(adultos=0, criancas=2).pessoas == 2
