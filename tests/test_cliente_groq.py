import asyncio

import pytest

from churrasco_facil.cliente_groq import (ClienteGroq, ErroAutenticacao, ErroGroq,
                                          ErroLimiteUso, ErroModelo, ErroRede, ErroResposta,
                                          ErroSemChave, MODELO_PADRAO, URL_PADRAO)
from conftest import TransporteFalso, resposta_groq, sem_espera

MSG = [{"role": "user", "content": "oi"}]


def cliente(*respostas, tentativas=3, esperas=None):
    transporte = TransporteFalso(*respostas)

    async def dormir(segundos):
        if esperas is not None:
            esperas.append(segundos)

    return ClienteGroq("chave-secreta", transporte=transporte, tentativas=tentativas,
                       dormir=dormir), transporte


def conversar(c, **kw):
    return asyncio.run(c.conversar(MSG, **kw))


def test_resposta_normal_e_o_que_foi_enviado():
    c, t = cliente((200, {}, resposta_groq("olá")))
    assert conversar(c, temperatura=0.2, max_tokens=50) == "olá"
    chamada = t.chamadas[0]
    assert chamada["url"] == URL_PADRAO
    assert chamada["cabecalhos"]["Authorization"] == "Bearer chave-secreta"
    assert chamada["corpo"]["model"] == MODELO_PADRAO
    assert chamada["corpo"]["messages"] == MSG
    assert chamada["corpo"]["temperature"] == 0.2
    assert chamada["corpo"]["max_completion_tokens"] == 50
    assert "response_format" not in chamada["corpo"]


def test_modo_json_pede_response_format():
    c, t = cliente((200, {}, resposta_groq("{}")))
    conversar(c, json_obrigatorio=True)
    assert t.chamadas[0]["corpo"]["response_format"] == {"type": "json_object"}


def test_sem_chave_nem_chega_a_chamar_a_rede():
    t = TransporteFalso((200, {}, resposta_groq("x")))
    for chave in (None, "", "   "):
        with pytest.raises(ErroSemChave):
            asyncio.run(ClienteGroq(chave, transporte=t).conversar(MSG))
    assert t.chamadas == []


def test_limite_de_uso_espera_o_que_o_groq_pediu_e_tenta_de_novo():
    esperas = []
    c, t = cliente((429, {"retry-after": "2"}, ""), (429, {"retry-after": "3"}, ""),
                   (200, {}, resposta_groq("ok")), esperas=esperas)
    assert conversar(c) == "ok"
    assert esperas == [2.0, 3.0] and len(t.chamadas) == 3


def test_espera_exponencial_sem_retry_after_e_limite_maximo():
    esperas = []
    c, _ = cliente((503, {}, ""), (503, {}, ""), (200, {}, resposta_groq("ok")),
                   esperas=esperas)
    assert conversar(c) == "ok" and esperas == [1.0, 2.0]
    esperas.clear()
    c, _ = cliente((429, {"retry-after": "999"}, ""), (200, {}, resposta_groq("ok")),
                   esperas=esperas)
    assert conversar(c) == "ok" and esperas == [20.0]


def test_limite_de_uso_persistente_vira_erro_de_limite():
    c, t = cliente((429, {}, ""), tentativas=2)
    with pytest.raises(ErroLimiteUso):
        conversar(c)
    assert len(t.chamadas) == 2


def test_erro_de_servidor_persistente_vira_erro_groq():
    c, _ = cliente((500, {}, ""), tentativas=2)
    with pytest.raises(ErroGroq) as excecao:
        conversar(c)
    assert "500" in str(excecao.value)


def test_falha_de_rede_tenta_de_novo_e_depois_desiste():
    c, t = cliente(OSError("sem rede"), tentativas=3)
    with pytest.raises(ErroRede):
        conversar(c)
    assert len(t.chamadas) == 3
    c, _ = cliente(OSError("sem rede"), (200, {}, resposta_groq("voltou")))
    assert conversar(c) == "voltou"


@pytest.mark.parametrize("codigo", [401, 403])
def test_chave_recusada_nao_repete(codigo):
    c, t = cliente((codigo, {}, "no"))
    with pytest.raises(ErroAutenticacao):
        conversar(c)
    assert len(t.chamadas) == 1


def test_modelo_inexistente():
    for resposta in ((404, {}, ""), (400, {}, '{"error": "The model `x` does not exist"}')):
        c, t = cliente(resposta)
        with pytest.raises(ErroModelo):
            conversar(c)
        assert len(t.chamadas) == 1


def test_outros_erros_do_cliente_nao_repetem():
    c, t = cliente((422, {}, "invalido"))
    with pytest.raises(ErroResposta):
        conversar(c)
    assert len(t.chamadas) == 1


@pytest.mark.parametrize("corpo", ["não é json", "{}", '{"choices": []}',
                                   resposta_groq(""), resposta_groq("   "),
                                   '{"choices": [{"message": {"content": 5}}]}'])
def test_respostas_mal_formadas(corpo):
    c, _ = cliente((200, {}, corpo))
    with pytest.raises(ErroResposta):
        conversar(c)


def test_chave_nunca_aparece_nas_mensagens_de_erro():
    for resposta in ((401, {}, "chave-secreta"), (500, {}, "chave-secreta"),
                     (404, {}, "chave-secreta"), OSError("chave-secreta")):
        c, _ = cliente(resposta, tentativas=1)
        with pytest.raises(ErroGroq) as excecao:
            conversar(c)
        assert "chave-secreta" not in str(excecao.value)
        assert "chave-secreta" not in excecao.value.mensagem_usuario


def test_cada_erro_tem_mensagem_para_o_usuario_em_portugues():
    for tipo in (ErroSemChave, ErroAutenticacao, ErroLimiteUso, ErroModelo, ErroRede,
                 ErroResposta, ErroGroq):
        assert tipo().mensagem_usuario and tipo().mensagem_usuario[0].isupper()


def test_tentativas_minimas():
    assert ClienteGroq("k", tentativas=0).tentativas == 1
    assert ClienteGroq(" k ").chave == "k" and ClienteGroq(" k ").configurado
