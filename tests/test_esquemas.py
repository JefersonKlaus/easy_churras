import json

import pytest

from churrasco_facil.esquemas import (ErroEsquema, extrair_json, interpretar_pedido,
                                      interpretar_sugestoes, limpar_texto_livre)


def sugestoes_de(*cortes):
    return json.dumps({"cortes": list(cortes)})


# ---------------------------------------------------------------- extrair_json

@pytest.mark.parametrize("texto", ['```json\n{"a": 1}\n```', 'Claro! {"a": 1} Espero ter ajudado.'])
def test_extrair_json_aceita_cercas_e_texto_em_volta(texto):
    assert extrair_json(texto) == {"a": 1}


@pytest.mark.parametrize("texto", ["", "sem json", "{quebrado", "} {", None])
def test_extrair_json_rejeita_lixo(texto):
    with pytest.raises(ErroEsquema):
        extrair_json(texto)


# ---------------------------------------------------------------- interpretar_pedido

def test_interpretar_pedido_completo():
    p = interpretar_pedido('{"adultos": 12, "criancas": "3", "vegetarianos": 1, '
                           '"bebem_alcool": 6, "duracao_horas": 4.5, "orcamento_reais": 400, '
                           '"observacoes": " só uma grelha ", "faltando": ["horario"]}')
    assert (p.adultos, p.criancas, p.vegetarianos, p.bebem_alcool) == (12, 3, 1, 6)
    assert p.duracao_horas == 4.5 and p.orcamento_centavos == 40000
    assert p.observacoes == "só uma grelha" and p.faltando == ("horario",)


@pytest.mark.parametrize("campo, valor, atributo", [
    ("adultos", -3, "adultos"), ("criancas", 99999, "criancas"),
    ("vegetarianos", True, "vegetarianos"), ("bebem_alcool", "muitos", "bebem_alcool"),
    ("duracao_horas", 40, "duracao_horas"), ("orcamento_reais", -10, "orcamento_centavos"),
])
def test_valor_absurdo_vira_none(campo, valor, atributo):
    assert getattr(interpretar_pedido(json.dumps({campo: valor})), atributo) is None


def test_faltando_que_nao_e_lista_e_ignorado():
    assert interpretar_pedido('{"faltando": "tudo"}').faltando == ()


def test_resposta_que_nao_e_objeto_levanta_erro():
    with pytest.raises(ErroEsquema):
        interpretar_pedido("[1, 2, 3]")


# ---------------------------------------------------------------- interpretar_sugestoes

def test_sugestoes_descartam_ids_inventados_repetidos_e_vegetarianos():
    texto = sugestoes_de({"id": "picanha", "motivo": "fácil"}, {"id": "zebra"},
                         {"id": "picanha"}, {"id": "queijo_coalho"}, "texto solto",
                         {"id": "alcatra", "motivo": 7})
    assert [(s.id, s.motivo) for s in interpretar_sugestoes(texto)] == \
        [("picanha", "fácil"), ("alcatra", "")]


def test_sugestoes_respeitam_o_maximo():
    ids = ["picanha", "maminha", "alcatra", "fraldinha", "contrafile", "linguica_toscana"]
    assert len(interpretar_sugestoes(sugestoes_de(*({"id": i} for i in ids)), maximo=3)) == 3


@pytest.mark.parametrize("texto", ['{"cortes": []}', '{"cortes": [{"id": "zebra"}]}',
                                   '{"outra": 1}', '{"cortes": "picanha"}'])
def test_sugestoes_sem_nenhum_corte_valido_dao_erro(texto):
    with pytest.raises(ErroEsquema):
        interpretar_sugestoes(texto)


# ---------------------------------------------------------------- limpar_texto_livre

def test_limpar_texto_livre_tira_blocos_de_codigo():
    assert limpar_texto_livre("Oi ```código``` tchau") == "Oi  tchau"


def test_limpar_texto_livre_limita_o_tamanho():
    assert len(limpar_texto_livre("a" * 5000)) == 800


def test_limpar_texto_livre_sem_texto():
    assert limpar_texto_livre(None) == ""
