"""Horários e cuidados juntos: cada aviso na hora em que importa."""
import pytest
from dados import SERVIR

from churrasco_facil.catalogo_carnes import CORTES
from churrasco_facil.cronograma import gerar_cronograma
from churrasco_facil.linha_do_tempo import cartoes, linha_do_tempo
from churrasco_facil.seguranca import avisos_para

CORTES_DO_TESTE = [CORTES[i] for i in ("picanha", "coxa_sobrecoxa", "bisteca_suina",
                                       "linguica_toscana")]


@pytest.fixture
def momentos():
    return linha_do_tempo(gerar_cronograma(SERVIR, CORTES_DO_TESTE), avisos_para(CORTES_DO_TESTE))


def onde_aparece(momentos, id_aviso):
    return [m.etapa.titulo for m in momentos if id_aviso in {a.id for a in m.avisos}]


def test_tem_um_momento_por_etapa_na_mesma_ordem(momentos):
    assert [m.etapa for m in momentos] == gerar_cronograma(SERVIR, CORTES_DO_TESTE)


@pytest.mark.parametrize("aviso, etapa", [
    ("monoxido", "Acender o carvão"), ("acendedor", "Acender o carvão"),
    ("criancas", "Acender o carvão"), ("tempo_fora", "Tirar a carne da geladeira"),
    ("frango", "Na grelha: Coxa e sobrecoxa de frango"),
    ("porco", "Na grelha: Bisteca suína"), ("linguica", "Na grelha: Linguiça toscana"),
    ("crua_pronta", "Servir!"), ("cinzas", "Apagar e limpar"),
])
def test_aviso_aparece_na_hora_em_que_importa(momentos, aviso, etapa):
    assert onde_aparece(momentos, aviso) == [etapa]


def test_termometro_aparece_quando_a_primeira_carne_vai_para_a_grelha(momentos):
    primeira_grelha = next(m.etapa.titulo for m in momentos if m.etapa.chave == "grelha")
    assert onde_aparece(momentos, "termometro") == [primeira_grelha]


def test_todo_aviso_do_plano_aparece_uma_vez(momentos):
    ids = [a.id for m in momentos for a in m.avisos]
    assert sorted(ids) == sorted(a.id for a in avisos_para(CORTES_DO_TESTE))


def test_aviso_sem_etapa_certa_vai_para_a_primeira_etapa():
    from churrasco_facil.seguranca import Aviso
    solto = Aviso("novo", "Aviso novo", "Sem etapa combinada.")
    momentos = linha_do_tempo(gerar_cronograma(SERVIR, []), [solto])
    assert momentos[0].avisos == (solto,)


def test_sem_etapas_nao_ha_momentos():
    assert linha_do_tempo([], avisos_para(CORTES_DO_TESTE)) == []


def test_cartoes_juntam_grelha_e_servir_sem_perder_etapa_nem_cuidado(momentos):
    lista = cartoes(momentos)
    assert sum(len(c.momentos) for c in lista) == len(momentos)
    assert [a.id for c in lista for a in c.avisos] == [a.id for m in momentos for a in m.avisos]
    assert [c.titulo for c in lista if c.junto] == ["Na grelha", "Tirar e servir"]

