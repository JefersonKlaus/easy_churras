import asyncio

import pytest

from churrasco_facil.cliente_groq import ErroGroq
from churrasco_facil.conversa import MAX_PERGUNTA, MAX_TURNOS, Conversa
from churrasco_facil.modo_offline import ConversaLocal
from churrasco_facil.prompts import mensagens_conversa
from dados import plano_para
from dubles import cliente_falso, resposta_ok

RESUMO = "Plano: 10 pessoas"
FALHA = (503, {}, "")


def conversa(*respostas, reserva=None):
    """Conversa cujo Groq devolve as respostas, na ordem. Devolve também o transporte."""
    cliente, transporte = cliente_falso(*respostas, tentativas=1)
    return Conversa(cliente, RESUMO, reserva), transporte


def perguntar(c, pergunta):
    return asyncio.run(c.perguntar(pergunta))


# ---------------------------------------------------------------- com o Groq

def test_devolve_a_resposta_do_groq():
    c, _ = conversa(resposta_ok("Espere a brasa ficar branca."))
    assert perguntar(c, "Quando acender?") == "Espere a brasa ficar branca."


def test_envia_o_plano_e_a_pergunta_sem_espacos():
    c, t = conversa(resposta_ok("r"))
    perguntar(c, " Quando acender? ")
    assert t.mensagens == mensagens_conversa(RESUMO, [], "Quando acender?")


def test_pergunta_e_resposta_entram_no_historico():
    c, _ = conversa(resposta_ok("r"))
    perguntar(c, "Quando acender?")
    assert c.historico == [{"role": "user", "content": "Quando acender?"},
                           {"role": "assistant", "content": "r"}]


def test_segunda_pergunta_leva_o_historico():
    c, t = conversa(resposta_ok("um"), resposta_ok("dois"))
    perguntar(c, "a")
    perguntar(c, "b")
    assert [m["role"] for m in t.chamadas[1]["corpo"]["messages"]] == \
        ["system", "user", "assistant", "user"]


def test_historico_guarda_so_os_ultimos_turnos():
    c, _ = conversa(resposta_ok("r"))
    for i in range(MAX_TURNOS + 4):
        perguntar(c, f"pergunta {i}")
    assert len(c.historico) == 2 * MAX_TURNOS
    assert c.historico[-2]["content"] == f"pergunta {MAX_TURNOS + 3}"


def test_pergunta_muito_longa_e_cortada():
    c, t = conversa(resposta_ok("r"))
    perguntar(c, "x" * 5000)
    assert len(t.mensagens[-1]["content"]) == MAX_PERGUNTA


def test_pergunta_vazia_e_recusada():
    c, t = conversa(resposta_ok("r"))
    with pytest.raises(ValueError):
        perguntar(c, "   ")
    assert t.chamadas == []


def test_limpar_apaga_o_historico():
    c, _ = conversa(resposta_ok("r"))
    perguntar(c, "a")
    c.limpar()
    assert c.historico == []


# ---------------------------------------------------------------- falhas e reserva

def test_sem_reserva_o_erro_sobe_e_nao_entra_no_historico():
    c, _ = conversa(OSError("x"))
    with pytest.raises(ErroGroq):
        perguntar(c, "oi")
    assert c.historico == []


def test_com_reserva_usa_o_groq_quando_ele_responde():
    c, _ = conversa(resposta_ok("Resposta da IA."), reserva=ConversaLocal(plano_para()))
    assert perguntar(c, "e se chover?") == "Resposta da IA."
    assert c.offline is False


def test_com_reserva_responde_offline_quando_o_groq_falha():
    c, _ = conversa(FALHA, reserva=ConversaLocal(plano_para()))
    assert perguntar(c, "e se chover?").startswith("Chuva fina")
    assert c.offline is True


def test_resposta_da_reserva_entra_no_historico():
    c, _ = conversa(resposta_ok("Resposta da IA."), FALHA, reserva=ConversaLocal(plano_para()))
    perguntar(c, "e se chover?")
    perguntar(c, "e se chover?")
    assert len(c.historico) == 4
