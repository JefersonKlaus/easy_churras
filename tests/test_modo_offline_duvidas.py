"""Modo offline: achar a resposta pronta para uma dúvida."""
import re

import pytest

from churrasco_facil.modo_offline import ASSUNTOS, achar_assunto, normalizar, resposta_do_plano
from dados import plano_para

CITAM_INFLAMAVEL = [a for a in ASSUNTOS
                    if re.search("alcool|gasolina", normalizar(a.resposta))]


@pytest.mark.parametrize("pergunta, id_esperado", [
    ("Como sei que a carne está no ponto?", "ponto"),
    ("E se começar a chover?", "chuva"),
    ("O carvão está acabando, e agora?", "carvao_acabando"),
    ("a chama está muito alta e queimando tudo", "queimando"),
    ("o frango está cru por dentro", "frango"),
    ("quanto tempo deixo descansar antes de cortar", "descanso"),
    ("posso guardar a sobra na geladeira?", "sobra"),
    ("como apagar as cinzas depois", "cinzas"),
    ("COMO ACENDER O FOGO", "acender"),
])
def test_pergunta_comum_acha_o_assunto(pergunta, id_esperado):
    assert achar_assunto(pergunta).id == id_esperado


@pytest.mark.parametrize("pergunta", ["qual a capital da França", "está", "o que é isso?",
                                      "como faço agora", "saber"])
def test_pergunta_sem_assunto_nao_chuta(pergunta):
    assert achar_assunto(pergunta) is None


def test_ids_dos_assuntos_sao_unicos():
    assert len({a.id for a in ASSUNTOS}) == len(ASSUNTOS)


@pytest.mark.parametrize("assunto", ASSUNTOS, ids=lambda a: a.id)
def test_assunto_tem_palavras_e_resposta_completa(assunto):
    assert assunto.palavras and len(assunto.resposta) > 60


@pytest.mark.parametrize("assunto", CITAM_INFLAMAVEL, ids=lambda a: a.id)
def test_resposta_so_cita_alcool_ou_gasolina_para_proibir(assunto):
    texto = normalizar(assunto.resposta)
    assert "nunca" in texto or "nada de" in texto


def test_resposta_sobre_o_ponto_traz_as_temperaturas_do_app():
    ponto = next(a for a in ASSUNTOS if a.id == "ponto").resposta
    assert "63" in ponto and "74" in ponto


@pytest.mark.parametrize("pergunta, trecho", [
    ("quanto vai custar?", "R$"),
    ("quantos kg de carne preciso", "kg de carne"),
    ("que horas devo acender o carvão?", ":"),
])
def test_pergunta_sobre_o_plano_usa_os_numeros_dele(pergunta, trecho):
    assert trecho in resposta_do_plano(pergunta, plano_para())


def test_pergunta_geral_nao_e_sobre_o_plano():
    assert resposta_do_plano("e a chuva?", plano_para()) is None
