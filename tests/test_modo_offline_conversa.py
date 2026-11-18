"""Modo offline: conversa de dúvidas sem internet."""
import asyncio

import pytest

from churrasco_facil.modo_offline import MENSAGEM_NAO_ENTENDI, ConversaLocal
from dados import plano_para


def perguntar(conversa, pergunta):
    return asyncio.run(conversa.perguntar(pergunta))


def test_responde_com_a_dica_pronta():
    assert perguntar(ConversaLocal(), "e se chover?").startswith("Chuva fina")


def test_com_plano_responde_com_os_numeros_dele():
    assert "kg de carne" in perguntar(ConversaLocal(plano_para()), "quantos kg de carne?")


def test_pergunta_sem_assunto_diz_que_nao_entendeu():
    assert perguntar(ConversaLocal(), "blá blá") == MENSAGEM_NAO_ENTENDI


def test_pergunta_vazia_e_recusada():
    with pytest.raises(ValueError):
        perguntar(ConversaLocal(), "   ")


def test_pergunta_enorme_e_cortada():
    conversa = ConversaLocal()
    perguntar(conversa, "chuva " + "x" * 5000)
    assert len(conversa.historico[0]["content"]) == 500


def test_historico_guarda_so_os_ultimos_turnos():
    conversa = ConversaLocal()
    for _ in range(10):
        perguntar(conversa, "e se chover?")
    assert len(conversa.historico) == 12


def test_limpar_apaga_o_historico():
    conversa = ConversaLocal()
    perguntar(conversa, "e se chover?")
    conversa.limpar()
    assert conversa.historico == []
