import asyncio

import pytest

from churrasco_facil.assistente import Assistente, pesos_das_sugestoes
from churrasco_facil.cliente_groq import ClienteGroq, ErroGroq, ErroResposta
from churrasco_facil.conversa import MAX_PERGUNTA, MAX_TURNOS, Conversa
from churrasco_facil.esquemas import Sugestao
from churrasco_facil.planejador import montar_plano, resumo_plano
from conftest import TransporteFalso, resposta_groq, sem_espera

PEDIDO_OK = '{"adultos": 12, "criancas": 3, "orcamento_reais": 400}'
CORTES_OK = '{"cortes": [{"id": "alcatra", "motivo": "fácil"}, {"id": "zebra"}]}'


def assistente(*textos):
    t = TransporteFalso(*[(200, {}, resposta_groq(x)) for x in textos])
    return Assistente(ClienteGroq("k", transporte=t, dormir=sem_espera)), t


def test_interpretar_pedido_usa_json_e_baixa_temperatura():
    a, t = assistente(PEDIDO_OK)
    pedido = asyncio.run(a.interpretar_pedido("churrasco para 12 adultos e 3 crianças, 400 reais"))
    assert pedido.adultos == 12 and pedido.orcamento_centavos == 40000
    corpo = t.chamadas[0]["corpo"]
    assert corpo["response_format"] == {"type": "json_object"} and corpo["temperature"] <= 0.2
    assert "400 reais" in corpo["messages"][-1]["content"]
    assert "JSON" in corpo["messages"][0]["content"]


def test_pedido_vazio_nao_chama_a_ia():
    a, t = assistente(PEDIDO_OK)
    with pytest.raises(ValueError):
        asyncio.run(a.interpretar_pedido("   "))
    assert t.chamadas == []


def test_json_invalido_tenta_uma_segunda_vez():
    a, t = assistente("isso não é json", PEDIDO_OK)
    assert asyncio.run(a.interpretar_pedido("12 adultos")).adultos == 12
    assert len(t.chamadas) == 2


def test_duas_respostas_invalidas_viram_erro_de_resposta():
    a, t = assistente("lixo", "mais lixo")
    with pytest.raises(ErroResposta):
        asyncio.run(a.interpretar_pedido("12 adultos"))
    assert len(t.chamadas) == 2


def test_erros_de_rede_passam_direto_para_a_tela():
    t = TransporteFalso(OSError("x"))
    a = Assistente(ClienteGroq("k", transporte=t, tentativas=1))
    with pytest.raises(ErroGroq):
        asyncio.run(a.interpretar_pedido("12 adultos"))


def test_sugerir_cortes_so_aceita_ids_do_catalogo(convidados):
    a, t = assistente(CORTES_OK)
    sugestoes = asyncio.run(a.sugerir_cortes(convidados, 40000))
    assert [s.id for s in sugestoes] == ["alcatra"]
    pergunta = t.chamadas[0]["corpo"]["messages"][-1]["content"]
    assert "10 adultos" in pergunta and "R$ 400,00" in pergunta
    sistema = t.chamadas[0]["corpo"]["messages"][0]["content"]
    assert "picanha" in sistema and "queijo_coalho" not in sistema


def test_sem_orcamento_o_prompt_diz_isso(convidados):
    a, t = assistente(CORTES_OK)
    asyncio.run(a.sugerir_cortes(convidados, None))
    assert "sem orçamento" in t.chamadas[0]["corpo"]["messages"][-1]["content"]


def test_pesos_das_sugestoes_usam_o_peso_padrao():
    assert pesos_das_sugestoes([Sugestao("picanha", ""), Sugestao("zebra", "")]) == {"picanha": 20}


def test_explicar_limpa_o_texto(pedido):
    a, t = assistente("Ótima escolha! ```ignorar``` Boa festa.")
    texto = asyncio.run(a.explicar(montar_plano(pedido)))
    assert texto == "Ótima escolha!  Boa festa."
    enviado = t.chamadas[0]["corpo"]["messages"][-1]["content"]
    assert "Custo estimado" in enviado


def test_explicar_resposta_so_com_codigo_e_erro(pedido):
    a, _ = assistente("```só código```")
    with pytest.raises(ErroResposta):
        asyncio.run(a.explicar(montar_plano(pedido)))


# ---------------------------------------------------------------- conversa

def conversa(*textos):
    t = TransporteFalso(*[(200, {}, resposta_groq(x)) for x in textos])
    return Conversa(ClienteGroq("k", transporte=t, dormir=sem_espera), "Plano: 10 pessoas"), t


def test_pergunta_e_resposta_entram_no_historico():
    c, t = conversa("Espere a brasa ficar branca.")
    assert asyncio.run(c.perguntar(" Quando acender? ")) == "Espere a brasa ficar branca."
    assert c.historico == [{"role": "user", "content": "Quando acender?"},
                           {"role": "assistant", "content": "Espere a brasa ficar branca."}]
    mensagens = t.chamadas[0]["corpo"]["messages"]
    assert mensagens[0]["role"] == "system" and "Plano: 10 pessoas" in mensagens[0]["content"]
    assert mensagens[-1] == {"role": "user", "content": "Quando acender?"}


def test_segunda_pergunta_leva_o_historico():
    c, t = conversa("um", "dois")
    asyncio.run(c.perguntar("a"))
    asyncio.run(c.perguntar("b"))
    roles = [m["role"] for m in t.chamadas[1]["corpo"]["messages"]]
    assert roles == ["system", "user", "assistant", "user"]


def test_historico_tem_tamanho_maximo():
    c, _ = conversa("r")
    for i in range(MAX_TURNOS + 4):
        asyncio.run(c.perguntar(f"pergunta {i}"))
    assert len(c.historico) == 2 * MAX_TURNOS
    assert c.historico[-2]["content"] == f"pergunta {MAX_TURNOS + 3}"


def test_pergunta_muito_longa_e_cortada_e_vazia_e_recusada():
    c, t = conversa("r")
    asyncio.run(c.perguntar("x" * 5000))
    assert len(t.chamadas[0]["corpo"]["messages"][-1]["content"]) == MAX_PERGUNTA
    with pytest.raises(ValueError):
        asyncio.run(c.perguntar("   "))


def test_pergunta_com_erro_nao_entra_no_historico():
    c = Conversa(ClienteGroq("k", transporte=TransporteFalso(OSError("x")), tentativas=1), "p")
    with pytest.raises(ErroGroq):
        asyncio.run(c.perguntar("oi"))
    assert c.historico == []


def test_limpar():
    c, _ = conversa("r")
    asyncio.run(c.perguntar("a"))
    c.limpar()
    assert c.historico == []
