import pytest

from churrasco_facil.catalogo_carnes import CORTES
from churrasco_facil.seguranca import (AVISO_FRANGO, AVISO_LINGUICA, AVISO_PORCO, AVISOS_GERAIS,
                                       avisos_para)


def ids_dos_avisos(*cortes):
    return [a.id for a in avisos_para([CORTES[c] for c in cortes])]


def test_avisos_gerais_sempre_aparecem():
    assert {a.id for a in AVISOS_GERAIS} <= set(ids_dos_avisos("picanha"))


def test_avisos_graves_vem_primeiro():
    graves = [a.grave for a in avisos_para([CORTES["picanha"], CORTES["coxa_sobrecoxa"]])]
    assert graves == sorted(graves, reverse=True)


@pytest.mark.parametrize("corte, aviso", [
    ("coxa_sobrecoxa", AVISO_FRANGO), ("bisteca_suina", AVISO_PORCO),
    ("linguica_toscana", AVISO_LINGUICA),
])
def test_aviso_especifico_aparece_com_o_tipo_de_carne(corte, aviso):
    assert aviso.id in ids_dos_avisos(corte)


@pytest.mark.parametrize("aviso", [AVISO_FRANGO, AVISO_PORCO, AVISO_LINGUICA])
def test_aviso_especifico_nao_aparece_sem_o_tipo_de_carne(aviso):
    assert aviso.id not in ids_dos_avisos("picanha")


def test_aviso_de_frango_e_grave_e_cita_a_temperatura():
    assert AVISO_FRANGO.grave and "74" in AVISO_FRANGO.texto


def test_aviso_de_lugar_fechado_e_grave():
    monoxido = next(a for a in AVISOS_GERAIS if a.id == "monoxido")
    assert monoxido.grave and "fechado" in monoxido.titulo
