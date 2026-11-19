from datetime import datetime, timedelta

import pytest
from dados import SERVIR

from churrasco_facil.catalogo_carnes import CORTES
from churrasco_facil.cronograma import (MINUTOS_PARA_BRASA, MINUTOS_PORCO_ANTES, gerar_cronograma,
                                        inicio_do_corte)


def por_titulo(etapas):
    return {e.titulo: e for e in etapas}


def titulos(cortes):
    return [e.titulo for e in gerar_cronograma(SERVIR, cortes)]


PICANHA_NA_GRELHA = SERVIR - timedelta(minutes=25 + 8)     # 25 min de grelha + 8 de descanso


@pytest.mark.parametrize("titulo, hora", [
    ("Comprar tudo da lista", datetime(2026, 11, 20, 17, 0)),
    ("Passar a carne do congelador para a geladeira", datetime(2026, 11, 20, 18, 0)),
    ("Colocar a cerveja na geladeira", datetime(2026, 11, 20, 18, 0)),
    ("Acender o carvão", PICANHA_NA_GRELHA - timedelta(minutes=MINUTOS_PARA_BRASA)),
    ("Tirar a carne da geladeira", PICANHA_NA_GRELHA - timedelta(minutes=30)),
    ("Na grelha: Picanha", PICANHA_NA_GRELHA),
    ("Tirar e esperar 8 min: Picanha", SERVIR - timedelta(minutes=8)),
    ("Servir!", SERVIR),
    ("Apagar e limpar", SERVIR + timedelta(hours=3)),
])
def test_etapas_sao_contadas_de_tras_para_frente(titulo, hora):
    assert por_titulo(gerar_cronograma(SERVIR, [CORTES["picanha"]]))[titulo].hora == hora


def test_etapas_vem_em_ordem_de_hora():
    cortes = [CORTES[i] for i in ("picanha", "costelinha_suina", "linguica_toscana")]
    horas = [e.hora for e in gerar_cronograma(SERVIR, cortes)]
    assert horas == sorted(horas)


def test_sem_quem_beba_gela_os_refrigerantes_na_vespera():
    etapas = por_titulo(gerar_cronograma(SERVIR, [CORTES["picanha"]], com_cerveja=False))
    assert "Colocar os refrigerantes na geladeira" in etapas
    assert "Colocar a cerveja na geladeira" not in etapas


def test_porco_vai_primeiro_20_min_antes_das_outras_carnes():
    # a coxa (48 min) começaria antes da linguiça (33 min): o porco passa na frente
    inicio = {e.titulo: e.hora for e in gerar_cronograma(
        SERVIR, [CORTES["coxa_sobrecoxa"], CORTES["linguica_toscana"]])}
    assert inicio["Na grelha: Linguiça toscana"] == \
        inicio["Na grelha: Coxa e sobrecoxa de frango"] - timedelta(minutes=MINUTOS_PORCO_ANTES)


def test_porco_que_ja_comeca_antes_nao_muda():
    costelinha = CORTES["costelinha_suina"]          # 2 h de grelha: já é o primeiro
    inicio = por_titulo(gerar_cronograma(SERVIR, [costelinha, CORTES["picanha"]]))
    assert inicio["Na grelha: Costelinha suína"].hora == inicio_do_corte(SERVIR, costelinha)


def test_porco_pronto_antes_vira_petisco():
    etapas = por_titulo(gerar_cronograma(SERVIR, [CORTES["coxa_sobrecoxa"],
                                                  CORTES["linguica_toscana"]]))
    assert "petisco" in etapas["Tirar e esperar 3 min: Linguiça toscana"].detalhe


def test_carvao_acende_a_tempo_do_corte_mais_demorado():
    etapas = por_titulo(gerar_cronograma(SERVIR, [CORTES["picanha"], CORTES["costelinha_suina"]]))
    inicio_costelinha = inicio_do_corte(SERVIR, CORTES["costelinha_suina"])
    assert etapas["Acender o carvão"].hora == \
        inicio_costelinha - timedelta(minutes=MINUTOS_PARA_BRASA)


def test_na_hora_de_grelhar_vem_a_dica_de_preparo():
    grelha = por_titulo(gerar_cronograma(SERVIR, [CORTES["picanha"]]))["Na grelha: Picanha"]
    picanha = CORTES["picanha"]
    assert picanha.preparo in grelha.detalhe and picanha.ponto in grelha.detalhe
    assert "sal grosso" in grelha.detalhe


def test_vegetariano_vai_para_a_grelha():
    assert "Na grelha: Queijo coalho no espeto" in titulos([CORTES["queijo_coalho"]])


def test_vegetariano_nao_tem_descanso_nem_sal_grosso():
    etapas = gerar_cronograma(SERVIR, [CORTES["queijo_coalho"]])
    assert not any(e.chave == "descansar" for e in etapas)
    assert "sal grosso" not in por_titulo(etapas)["Na grelha: Queijo coalho no espeto"].detalhe


def test_sem_cortes_nao_acende_o_carvao():
    assert "Acender o carvão" not in titulos([])
