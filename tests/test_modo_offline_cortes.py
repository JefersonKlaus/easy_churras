"""Modo offline: sugerir cortes por regras, sem IA."""
import json

import pytest

from churrasco_facil.calculadora import Convidados
from churrasco_facil.catalogo_carnes import CORTES, VEGETARIANO
from churrasco_facil.esquemas import interpretar_sugestoes
from churrasco_facil.modo_offline import sugerir_cortes_local


def ids(conv, orcamento=None):
    return [s.id for s in sugerir_cortes_local(conv, orcamento)]


@pytest.fixture(params=[(conv, orcamento)
                        for conv in (Convidados(adultos=1), Convidados(adultos=8, criancas=3),
                                     Convidados(adultos=30, criancas=5))
                        for orcamento in (None, 10000, 80000, 500000)],
                ids=lambda p: f"{p[0].pessoas}p-{p[1]}")
def sugestoes(request):
    return sugerir_cortes_local(*request.param)


@pytest.mark.parametrize("orcamento, corte", [(150000, "picanha"), (None, "picanha"),
                                              (30000, "alcatra")])
def test_cortes_acompanham_o_orcamento(orcamento, corte):
    assert corte in ids(Convidados(adultos=10), orcamento)


def test_orcamento_apertado_nao_sugere_picanha():
    assert "picanha" not in ids(Convidados(adultos=10), 30000)


def test_sugere_de_3_a_6_cortes(sugestoes):
    assert 3 <= len(sugestoes) <= 6


def test_nao_repete_cortes(sugestoes):
    assert len({s.id for s in sugestoes}) == len(sugestoes)


def test_so_sugere_carnes_do_catalogo(sugestoes):
    assert all(s.id in CORTES and CORTES[s.id].categoria != VEGETARIANO for s in sugestoes)


def test_so_sugere_cortes_faceis(sugestoes):
    assert all(CORTES[s.id].dificuldade <= 2 for s in sugestoes)


def test_todo_corte_tem_motivo(sugestoes):
    assert all(s.motivo for s in sugestoes)


def test_criancas_ganham_linguica_de_frango():
    assert "linguica_frango" in ids(Convidados(adultos=6, criancas=2))


def test_sem_criancas_nao_tem_linguica_de_frango():
    assert "linguica_frango" not in ids(Convidados(adultos=6))


def test_grupo_grande_recebe_maminha():
    assert "maminha" in ids(Convidados(adultos=30))


def test_grupo_grande_com_orcamento_economico_nao_recebe_maminha():
    assert "maminha" not in ids(Convidados(adultos=30), 80000)


def test_sugestao_local_passa_pelo_mesmo_validador_da_ia():
    sugestoes = sugerir_cortes_local(Convidados(adultos=10), None)
    texto = json.dumps({"cortes": [{"id": s.id, "motivo": s.motivo} for s in sugestoes]})
    assert interpretar_sugestoes(texto) == sugestoes
