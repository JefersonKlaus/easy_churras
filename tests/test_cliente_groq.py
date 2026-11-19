import asyncio

import pytest
from dubles import CHAVE, DormirFalso, TransporteFalso, cliente_falso, resposta_groq, resposta_ok

from churrasco_facil.cliente_groq import (MODELO_PADRAO, URL_PADRAO, ClienteGroq,
                                          ErroAutenticacao, ErroGroq, ErroLimiteUso, ErroModelo,
                                          ErroRede, ErroResposta, ErroSemChave)

MSG = [{"role": "user", "content": "oi"}]


def conversar(cliente, **opcoes):
    return asyncio.run(cliente.conversar(MSG, **opcoes))


def erro_de(cliente):
    with pytest.raises(ErroGroq) as excecao:
        conversar(cliente)
    return excecao.value


# ---------------------------------------------------------------- pedido enviado

def test_devolve_o_texto_da_resposta():
    cliente, _ = cliente_falso(resposta_ok("olá"))
    assert conversar(cliente) == "olá"


def test_envia_para_a_url_do_groq_com_a_chave():
    cliente, transporte = cliente_falso(resposta_ok("olá"))
    conversar(cliente)
    assert transporte.chamadas[0]["url"] == URL_PADRAO
    assert transporte.chamadas[0]["cabecalhos"]["Authorization"] == f"Bearer {CHAVE}"


@pytest.mark.parametrize("campo, valor", [
    ("model", MODELO_PADRAO), ("messages", MSG), ("temperature", 0.2),
    ("max_completion_tokens", 50),
])
def test_corpo_leva_modelo_mensagens_e_opcoes(campo, valor):
    cliente, transporte = cliente_falso(resposta_ok("olá"))
    conversar(cliente, temperatura=0.2, max_tokens=50)
    assert transporte.chamadas[0]["corpo"][campo] == valor


def test_sem_modo_json_nao_pede_response_format():
    cliente, transporte = cliente_falso(resposta_ok("olá"))
    conversar(cliente)
    assert "response_format" not in transporte.chamadas[0]["corpo"]


def test_modo_json_pede_response_format():
    cliente, transporte = cliente_falso(resposta_ok("{}"))
    conversar(cliente, json_obrigatorio=True)
    assert transporte.chamadas[0]["corpo"]["response_format"] == {"type": "json_object"}


@pytest.mark.parametrize("chave", [None, "", "   "])
def test_sem_chave_nem_chega_a_chamar_a_rede(chave):
    transporte = TransporteFalso(resposta_ok("x"))
    with pytest.raises(ErroSemChave):
        conversar(ClienteGroq(chave, transporte=transporte))
    assert transporte.chamadas == []


# ---------------------------------------------------------------- novas tentativas

def test_limite_de_uso_espera_o_que_o_groq_pediu():
    dormir = DormirFalso()
    cliente, _ = cliente_falso((429, {"retry-after": "2"}, ""), (429, {"retry-after": "3"}, ""),
                               resposta_ok("ok"), dormir=dormir)
    assert conversar(cliente) == "ok"
    assert dormir.esperas == [2.0, 3.0]


def test_sem_retry_after_a_espera_dobra():
    dormir = DormirFalso()
    cliente, _ = cliente_falso((503, {}, ""), (503, {}, ""), resposta_ok("ok"), dormir=dormir)
    conversar(cliente)
    assert dormir.esperas == [1.0, 2.0]


def test_espera_tem_limite_maximo():
    dormir = DormirFalso()
    cliente, _ = cliente_falso((429, {"retry-after": "999"}, ""), resposta_ok("ok"),
                               dormir=dormir)
    conversar(cliente)
    assert dormir.esperas == [20.0]


def test_falha_de_rede_passageira_tenta_de_novo():
    cliente, _ = cliente_falso(OSError("sem rede"), resposta_ok("voltou"))
    assert conversar(cliente) == "voltou"


def test_falha_de_rede_persistente_desiste_depois_das_tentativas():
    cliente, transporte = cliente_falso(OSError("sem rede"), tentativas=3)
    assert isinstance(erro_de(cliente), ErroRede)
    assert len(transporte.chamadas) == 3


def test_limite_de_uso_persistente_vira_erro_de_limite():
    cliente, transporte = cliente_falso((429, {}, ""), tentativas=2)
    assert isinstance(erro_de(cliente), ErroLimiteUso)
    assert len(transporte.chamadas) == 2


def test_erro_de_servidor_persistente_cita_o_codigo():
    cliente, _ = cliente_falso((500, {}, ""), tentativas=2)
    assert "500" in str(erro_de(cliente))


def test_tentativas_minimas_sao_uma():
    assert ClienteGroq("k", tentativas=0).tentativas == 1


# ---------------------------------------------------------------- erros que não repetem

@pytest.mark.parametrize("resposta, tipo", [
    ((401, {}, "no"), ErroAutenticacao), ((403, {}, "no"), ErroAutenticacao),
    ((404, {}, ""), ErroModelo),
    ((400, {}, '{"error": "The model `x` does not exist"}'), ErroModelo),
    ((422, {}, "invalido"), ErroResposta),
])
def test_erro_do_cliente_nao_repete(resposta, tipo):
    cliente, transporte = cliente_falso(resposta)
    assert isinstance(erro_de(cliente), tipo)
    assert len(transporte.chamadas) == 1


@pytest.mark.parametrize("corpo", ["não é json", "{}", '{"choices": []}',
                                   resposta_groq(""), resposta_groq("   "),
                                   '{"choices": [{"message": {"content": 5}}]}'])
def test_resposta_mal_formada_vira_erro_de_resposta(corpo):
    cliente, _ = cliente_falso((200, {}, corpo))
    assert isinstance(erro_de(cliente), ErroResposta)


# ---------------------------------------------------------------- mensagens de erro

@pytest.mark.parametrize("resposta", [(401, {}, CHAVE), (500, {}, CHAVE), (404, {}, CHAVE),
                                      OSError(CHAVE)])
def test_chave_nunca_aparece_no_erro(resposta):
    erro = erro_de(cliente_falso(resposta, tentativas=1)[0])
    assert CHAVE not in str(erro) and CHAVE not in erro.mensagem_usuario
