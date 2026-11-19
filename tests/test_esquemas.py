import json

import pytest

from churrasco_facil.esquemas import ErroEsquema, extrair_json, interpretar_pedido


def sugestoes_de(*cortes):
    return json.dumps({"cortes": list(cortes)})


# ---------------------------------------------------------------- extrair_json

@pytest.mark.parametrize("texto", ['```json\n{"a": 1}\n```',
                                   'Claro! {"a": 1} Espero ter ajudado.'])
def test_extrair_json_aceita_cercas_e_texto_em_volta(texto):
    assert extrair_json(texto) == {"a": 1}


@pytest.mark.parametrize("texto", ["", "sem json", "{quebrado", "} {", None])
def test_extrair_json_rejeita_lixo(texto):
    with pytest.raises(ErroEsquema):
        extrair_json(texto)


# ---------------------------------------------------------------- interpretar_pedido

def test_interpretar_pedido_completo():
    p = interpretar_pedido('{"adultos": 12, "criancas": "3", "vegetarianos": 1, '
                           '"bebem_alcool": 6, "duracao_horas": 4.5, "faltando": ["horario"]}')
    assert (p.adultos, p.criancas, p.vegetarianos, p.bebem_alcool) == (12, 3, 1, 6)
    assert p.duracao_horas == 4.5 and p.faltando == ("horario",)


@pytest.mark.parametrize("campo, valor, atributo", [
    ("adultos", -3, "adultos"), ("criancas", 99999, "criancas"),
    ("vegetarianos", True, "vegetarianos"), ("bebem_alcool", "muitos", "bebem_alcool"),
    ("duracao_horas", 40, "duracao_horas"),
])
def test_valor_absurdo_vira_none(campo, valor, atributo):
    assert getattr(interpretar_pedido(json.dumps({campo: valor})), atributo) is None


def test_faltando_que_nao_e_lista_e_ignorado():
    assert interpretar_pedido('{"faltando": "tudo"}').faltando == ()


def test_resposta_que_nao_e_objeto_levanta_erro():
    with pytest.raises(ErroEsquema):
        interpretar_pedido("[1, 2, 3]")


# ---------------------------------------------------------------- interpretar_sugestoes


# ---------------------------------------------------------------- limpar_texto_livre
