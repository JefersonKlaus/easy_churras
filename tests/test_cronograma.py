from datetime import datetime, timedelta

import pytest

from churrasco_facil.catalogo_carnes import CORTES
from churrasco_facil.cronograma import (MINUTOS_PARA_BRASA, formatar_hora, gerar_cronograma,
                                        inicio_do_corte)
from dados import SERVIR


def por_titulo(etapas):
    return {e.titulo: e for e in etapas}


def titulos(cortes):
    return [e.titulo for e in gerar_cronograma(SERVIR, cortes)]


PICANHA_NA_GRELHA = SERVIR - timedelta(minutes=25 + 8)     # 25 min de grelha + 8 de descanso


@pytest.mark.parametrize("titulo, hora", [
    ("Comprar tudo", datetime(2026, 11, 20, 17, 0)),
    ("Acender o carvão", PICANHA_NA_GRELHA - timedelta(minutes=MINUTOS_PARA_BRASA)),
    ("Tirar a carne da geladeira", PICANHA_NA_GRELHA - timedelta(minutes=30)),
    ("Temperar: Picanha", PICANHA_NA_GRELHA - timedelta(minutes=15)),
    ("Na grelha: Picanha", PICANHA_NA_GRELHA),
    ("Tirar e descansar: Picanha", SERVIR - timedelta(minutes=8)),
    ("Servir!", SERVIR),
    ("Apagar e limpar", SERVIR + timedelta(hours=3)),
])
def test_etapas_sao_contadas_de_tras_para_frente(titulo, hora):
    assert por_titulo(gerar_cronograma(SERVIR, [CORTES["picanha"]]))[titulo].hora == hora


@pytest.mark.parametrize("titulo, chave", [
    ("Comprar tudo", "compras"), ("Colocar as bebidas no gelo", "bebidas"),
    ("Preparar vinagrete, farofa e arroz", "guarnicoes"), ("Acender o carvão", "carvao"),
    ("Tirar a carne da geladeira", "geladeira"), ("Temperar: Picanha", "temperar"),
    ("Na grelha: Picanha", "grelha"), ("Tirar e descansar: Picanha", "descansar"),
    ("Servir!", "servir"), ("Apagar e limpar", "limpar"),
])
def test_cada_etapa_diz_qual_etapa_e(titulo, chave):
    assert por_titulo(gerar_cronograma(SERVIR, [CORTES["picanha"]]))[titulo].chave == chave


def test_etapas_de_um_corte_levam_a_categoria_dele():
    etapa = por_titulo(gerar_cronograma(SERVIR, [CORTES["coxa_sobrecoxa"]]))
    assert etapa["Na grelha: Coxa e sobrecoxa de frango"].categoria == "frango"


def test_etapas_vem_em_ordem_de_hora():
    cortes = [CORTES[i] for i in ("picanha", "costelinha_suina", "linguica_toscana")]
    horas = [e.hora for e in gerar_cronograma(SERVIR, cortes)]
    assert horas == sorted(horas)


def test_carvao_acende_a_tempo_do_corte_mais_demorado():
    etapas = por_titulo(gerar_cronograma(SERVIR, [CORTES["picanha"], CORTES["costelinha_suina"]]))
    inicio_costelinha = inicio_do_corte(SERVIR, CORTES["costelinha_suina"])
    assert etapas["Acender o carvão"].hora == \
        inicio_costelinha - timedelta(minutes=MINUTOS_PARA_BRASA)


def test_corte_mais_demorado_vai_primeiro_para_a_grelha():
    etapas = por_titulo(gerar_cronograma(SERVIR, [CORTES["picanha"], CORTES["costelinha_suina"]]))
    assert etapas["Na grelha: Costelinha suína"].hora < etapas["Na grelha: Picanha"].hora


def test_vegetariano_vai_para_a_grelha():
    assert "Na grelha: Queijo coalho no espeto" in titulos([CORTES["queijo_coalho"]])


@pytest.mark.parametrize("etapa", ["Temperar", "Tirar e descansar"])
def test_vegetariano_nao_tem_etapa_de_carne(etapa):
    assert f"{etapa}: Queijo coalho no espeto" not in titulos([CORTES["queijo_coalho"]])


def test_sem_cortes_ainda_tem_a_hora_de_servir():
    assert "Servir!" in titulos([])


def test_sem_cortes_nao_acende_o_carvao():
    assert "Acender o carvão" not in titulos([])


def test_formatar_hora():
    assert formatar_hora(SERVIR) == "14:00"
