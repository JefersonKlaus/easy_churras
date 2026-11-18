import asyncio

import pytest

from churrasco_facil.assistente import Assistente, pesos_das_sugestoes
from churrasco_facil.catalogo_carnes import CORTES
from churrasco_facil.cliente_groq import ErroGroq, ErroResposta
from churrasco_facil.esquemas import Sugestao
from churrasco_facil.planejador import resumo_pedido, resumo_plano
from churrasco_facil.prompts import mensagens_cortes, mensagens_explicacao, mensagens_pedido
from dubles import cliente_falso, resposta_ok

PEDIDO = '{"adultos": 12, "criancas": 3, "orcamento_reais": 400}'
CORTES_OK = '{"cortes": [{"id": "alcatra", "motivo": "fácil"}, {"id": "zebra"}]}'


def assistente(*textos):
    """Assistente cujo Groq responde os textos, na ordem. Devolve também o transporte."""
    cliente, transporte = cliente_falso(*(resposta_ok(t) for t in textos))
    return Assistente(cliente), transporte


# ---------------------------------------------------------------- interpretar_pedido

def test_interpretar_pedido_devolve_o_pedido_validado():
    a, _ = assistente(PEDIDO)
    pedido = asyncio.run(a.interpretar_pedido("12 adultos"))
    assert (pedido.adultos, pedido.orcamento_centavos) == (12, 40000)


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

def test_sugerir_cortes_so_aceita_ids_do_catalogo(convidados):
    a, _ = assistente(CORTES_OK)
    assert [s.id for s in asyncio.run(a.sugerir_cortes(convidados, 40000))] == ["alcatra"]


def test_sugerir_cortes_envia_o_resumo_do_grupo(convidados):
    a, t = assistente(CORTES_OK)
    asyncio.run(a.sugerir_cortes(convidados, 40000))
    assert t.mensagens == mensagens_cortes(resumo_pedido(convidados, 40000))


def test_pesos_das_sugestoes_usam_o_peso_padrao_e_ignoram_ids_desconhecidos():
    sugestoes = [Sugestao("picanha", ""), Sugestao("zebra", "")]
    assert pesos_das_sugestoes(sugestoes) == {"picanha": CORTES["picanha"].peso_padrao}


# ---------------------------------------------------------------- explicar

def test_explicar_devolve_o_texto_limpo(plano):
    a, _ = assistente("Ótima escolha! ```ignorar``` Boa festa.")
    assert asyncio.run(a.explicar(plano)) == "Ótima escolha!  Boa festa."


def test_explicar_envia_o_resumo_do_plano(plano):
    a, t = assistente("Boa festa.")
    asyncio.run(a.explicar(plano))
    assert t.mensagens == mensagens_explicacao(resumo_plano(plano))


def test_explicacao_so_com_codigo_e_erro(plano):
    a, _ = assistente("```só código```")
    with pytest.raises(ErroResposta):
        asyncio.run(a.explicar(plano))
