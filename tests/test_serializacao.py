"""O pedido em dicionário (JSON) e de volta, inclusive registros antigos ou estragados."""
import json
from dataclasses import replace

import pytest

from churrasco_facil.planejador import Pedido
from churrasco_facil.serializacao import pedido_de_dict, pedido_para_dict


def test_pedido_com_cortes_preferidos_volta_igual_pelo_json(pedido):
    pedido = Pedido(pedido.convidados, pedido.hora_servir, pesos_preferidos={"alcatra": 2},
                    nome="Festa")
    assert pedido_de_dict(json.loads(json.dumps(pedido_para_dict(pedido)))) == pedido


def test_carnes_escolhidas_voltam_iguais_pelo_json(pedido):
    pedido = replace(pedido, pecas_escolhidas={"picanha": 2, "coracao_frango": 1})
    assert pedido_de_dict(json.loads(json.dumps(pedido_para_dict(pedido)))) == pedido


def test_carne_escolhida_invalida_e_ignorada_ao_ler(pedido):
    dados = {**pedido_para_dict(pedido), "pecas_escolhidas": {"picanha": 2, "zebra": 1,
                                                              "alcatra": 0}}
    assert pedido_de_dict(dados).pecas_escolhidas == {"picanha": 2}


def test_plano_salvo_quando_havia_secoes_fora_ainda_abre(pedido):
    # versões antigas guardavam as seções tiradas da conta (ex.: hortifruti)
    dados = {**pedido_para_dict(pedido), "secoes_fora": ["Hortifruti"]}
    assert pedido_de_dict(dados) == pedido


def test_cortes_invalidos_sao_descartados_ao_ler(pedido):
    dados = pedido_para_dict(pedido)
    dados["pesos_preferidos"] = {"alcatra": 2, "zebra": 5}
    assert pedido_de_dict(dados).pesos_preferidos == {"alcatra": 2}


@pytest.mark.parametrize("estragar", [
    lambda d: d.pop("convidados"), lambda d: d.pop("hora_servir"),
    lambda d: d["convidados"].pop("adultos"), lambda d: d.update(hora_servir="ontem"),
    lambda d: d["convidados"].update(adultos=-4),
])
def test_registro_corrompido_levanta_valueerror(pedido, estragar):
    dados = pedido_para_dict(pedido)
    estragar(dados)
    with pytest.raises(ValueError):
        pedido_de_dict(dados)
