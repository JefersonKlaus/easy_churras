"""Modo offline: assistente local e reserva automática quando o Groq falha."""
import asyncio

import pytest

from churrasco_facil.assistente import Assistente
from churrasco_facil.calculadora import Convidados
from churrasco_facil.modo_offline import AssistenteComReserva, AssistenteLocal
from dados import plano_para
from dubles import cliente_falso, resposta_ok

JSON_QUEBRADO = resposta_ok("isso não é json")


def com_reserva(*respostas):
    """Assistente do Groq (sem novas tentativas) com a reserva local."""
    cliente, _ = cliente_falso(*respostas, tentativas=1)
    return AssistenteComReserva(Assistente(cliente))


def test_assistente_local_exige_texto():
    with pytest.raises(ValueError):
        asyncio.run(AssistenteLocal().interpretar_pedido("  "))


def test_reserva_nao_e_usada_quando_o_groq_responde():
    assistente = com_reserva(resposta_ok('{"adultos": 7}'))
    assert asyncio.run(assistente.interpretar_pedido("10 adultos")).adultos == 7
    assert (assistente.offline, assistente.aviso) == (False, "")


@pytest.mark.parametrize("falha", [(401, {}, ""), (429, {}, ""), (500, {}, ""),
                                   OSError("sem rede")])
def test_reserva_responde_quando_o_groq_falha(falha):
    assistente = com_reserva(falha)
    assert asyncio.run(assistente.interpretar_pedido("10 adultos")).adultos == 10


def test_reserva_avisa_que_usou_o_modo_offline():
    assistente = com_reserva((401, {}, ""))
    asyncio.run(assistente.interpretar_pedido("10 adultos"))
    assert assistente.offline is True
    assert "recusou a chave" in assistente.aviso and "modo offline" in assistente.aviso


def test_reserva_entra_quando_o_json_vem_quebrado_duas_vezes():
    assistente = com_reserva(JSON_QUEBRADO, JSON_QUEBRADO)
    assert asyncio.run(assistente.interpretar_pedido("8 adultos")).adultos == 8
    assert assistente.offline


def test_reserva_tambem_sugere_cortes():
    assistente = com_reserva(OSError("sem rede"))
    assert asyncio.run(assistente.sugerir_cortes(Convidados(adultos=8), None))


def test_reserva_tambem_explica_o_plano():
    assistente = com_reserva(OSError("sem rede"))
    assert asyncio.run(assistente.explicar(plano_para())).startswith("Para 13 pessoas")


def test_aviso_some_na_chamada_seguinte_que_funciona():
    assistente = com_reserva((500, {}, ""), resposta_ok('{"adultos": 3}'))
    asyncio.run(assistente.interpretar_pedido("8 adultos"))
    asyncio.run(assistente.interpretar_pedido("8 adultos"))
    assert (assistente.offline, assistente.aviso) == (False, "")


def test_erro_de_programa_nao_e_escondido_pela_reserva():
    class Quebrado:
        async def explicar(self, plano):
            raise KeyError("bug")
    with pytest.raises(KeyError):
        asyncio.run(AssistenteComReserva(Quebrado()).explicar(plano_para()))
