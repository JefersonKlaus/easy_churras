import asyncio

import pytest
from dubles import cliente_falso, resposta_ok

from churrasco_facil.assistente import Assistente
from churrasco_facil.cliente_groq import ErroGroq, ErroResposta
from churrasco_facil.prompts import mensagens_pedido

PEDIDO = '{"adultos": 12, "criancas": 3}'
CORTES_OK = '{"cortes": [{"id": "alcatra", "motivo": "fácil"}, {"id": "zebra"}]}'


def assistente(*textos):
    """Assistente cujo Groq responde os textos, na ordem. Devolve também o transporte."""
    cliente, transporte = cliente_falso(*(resposta_ok(t) for t in textos))
    return Assistente(cliente), transporte


# ---------------------------------------------------------------- interpretar_pedido

def test_interpretar_pedido_devolve_o_pedido_validado():
    a, _ = assistente(PEDIDO)
    pedido = asyncio.run(a.interpretar_pedido("12 adultos"))
    assert (pedido.adultos, pedido.criancas) == (12, 3)


def test_interpretar_pedido_envia_as_mensagens_de_pedido():
    a, t = assistente(PEDIDO)
    asyncio.run(a.interpretar_pedido("12 adultos, 400 reais"))
    assert t.mensagens == mensagens_pedido("12 adultos, 400 reais")


def test_interpretar_pedido_pede_json_com_temperatura_baixa():
    a, t = assistente(PEDIDO)
    asyncio.run(a.interpretar_pedido("12 adultos"))
    corpo = t.chamadas[0]["corpo"]
    assert corpo["response_format"] == {"type": "json_object"} and corpo["temperature"] <= 0.2


def test_pedido_vazio_nao_chama_a_ia():
    a, t = assistente(PEDIDO)
    with pytest.raises(ValueError):
        asyncio.run(a.interpretar_pedido("   "))
    assert t.chamadas == []


def test_json_invalido_tenta_uma_segunda_vez():
    a, t = assistente("isso não é json", PEDIDO)
    assert asyncio.run(a.interpretar_pedido("12 adultos")).adultos == 12
    assert len(t.chamadas) == 2


def test_duas_respostas_invalidas_viram_erro_de_resposta():
    a, t = assistente("lixo", "mais lixo")
    with pytest.raises(ErroResposta):
        asyncio.run(a.interpretar_pedido("12 adultos"))
    assert len(t.chamadas) == 2


def test_erro_do_groq_passa_direto_para_quem_chamou():
    cliente, _ = cliente_falso(OSError("x"), tentativas=1)
    with pytest.raises(ErroGroq):
        asyncio.run(Assistente(cliente).interpretar_pedido("12 adultos"))


# ---------------------------------------------------------------- sugerir_cortes


# ---------------------------------------------------------------- explicar
