import pytest

from churrasco_facil.esquemas import (ErroEsquema, extrair_json, interpretar_pedido,
                                      interpretar_sugestoes, limpar_texto_livre)


def test_extrair_json_aceita_cercas_e_texto_em_volta():
    assert extrair_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert extrair_json('Claro! {"a": 1} Espero ter ajudado.') == {"a": 1}


@pytest.mark.parametrize("texto", ["", "sem json", "{quebrado", "} {", None])
def test_extrair_json_rejeita_lixo(texto):
    with pytest.raises(ErroEsquema):
        extrair_json(texto)


def test_interpretar_pedido_completo():
    p = interpretar_pedido('{"adultos": 12, "criancas": "3", "vegetarianos": 1, '
                           '"bebem_alcool": 6, "duracao_horas": 4.5, "orcamento_reais": 400, '
                           '"observacoes": " só uma grelha ", "faltando": ["horario"]}')
    assert (p.adultos, p.criancas, p.vegetarianos, p.bebem_alcool) == (12, 3, 1, 6)
    assert p.duracao_horas == 4.5 and p.orcamento_centavos == 40000
    assert p.observacoes == "só uma grelha" and p.faltando == ("horario",)


def test_valores_ausentes_ou_absurdos_viram_none():
    p = interpretar_pedido('{"adultos": -3, "criancas": 99999, "vegetarianos": true, '
                           '"bebem_alcool": "muitos", "duracao_horas": 40, '
                           '"orcamento_reais": -10, "faltando": "tudo"}')
    assert p.adultos is None and p.criancas is None and p.vegetarianos is None
    assert p.bebem_alcool is None and p.duracao_horas is None
    assert p.orcamento_centavos is None and p.faltando == ()


def test_resposta_que_nao_e_objeto_levanta_erro():
    with pytest.raises(ErroEsquema):
        interpretar_pedido("[1, 2, 3]")


def test_sugestoes_descartam_ids_inventados_repetidos_e_vegetarianos():
    s = interpretar_sugestoes('{"cortes": [{"id": "picanha", "motivo": "fácil"}, '
                              '{"id": "zebra"}, {"id": "picanha"}, {"id": "queijo_coalho"}, '
                              '"texto solto", {"id": "alcatra", "motivo": 7}]}')
    assert [(x.id, x.motivo) for x in s] == [("picanha", "fácil"), ("alcatra", "")]


def test_sugestoes_respeitam_o_maximo():
    ids = ["picanha", "maminha", "alcatra", "fraldinha", "contrafile", "linguica_toscana"]
    texto = '{"cortes": [' + ",".join(f'{{"id": "{i}"}}' for i in ids) + "]}"
    assert len(interpretar_sugestoes(texto, maximo=3)) == 3


@pytest.mark.parametrize("texto", ['{"cortes": []}', '{"cortes": [{"id": "zebra"}]}',
                                   '{"outra": 1}', '{"cortes": "picanha"}'])
def test_sugestoes_sem_nenhum_corte_valido_dao_erro(texto):
    with pytest.raises(ErroEsquema):
        interpretar_sugestoes(texto)


def test_limpar_texto_livre():
    assert limpar_texto_livre("Oi ```código``` tchau") == "Oi  tchau"
    assert len(limpar_texto_livre("a" * 5000)) == 800
    assert limpar_texto_livre(None) == ""
