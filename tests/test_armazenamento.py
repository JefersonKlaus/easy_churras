import json
import sqlite3
from datetime import datetime

import pytest

from churrasco_facil.armazenamento import Armazenamento, pedido_de_dict, pedido_para_dict
from churrasco_facil.calculadora import Convidados
from churrasco_facil.planejador import Pedido
from dados import SERVIR

ONTEM, HOJE = datetime(2026, 11, 1, 9, 0), datetime(2026, 11, 2, 9, 0)


@pytest.fixture
def banco():
    return Armazenamento(":memory:")


# ---------------------------------------------------------------- pedido <-> dicionário

def test_pedido_volta_igual_pelo_dicionario(pedido):
    assert pedido_de_dict(pedido_para_dict(pedido)) == pedido


def test_pedido_com_cortes_preferidos_volta_igual_pelo_json(pedido):
    pedido = Pedido(pedido.convidados, pedido.hora_servir, 55000, {"alcatra": 2}, "Festa")
    assert pedido_de_dict(json.loads(json.dumps(pedido_para_dict(pedido)))) == pedido


def test_secoes_fora_voltam_iguais(pedido):
    pedido = Pedido(pedido.convidados, pedido.hora_servir, secoes_fora=("Hortifruti",))
    assert pedido_de_dict(pedido_para_dict(pedido)).secoes_fora == ("Hortifruti",)


def test_plano_antigo_sem_secoes_fora_conta_tudo(pedido):
    dados = pedido_para_dict(pedido)
    del dados["secoes_fora"]
    assert pedido_de_dict(dados).secoes_fora == ()


def test_secao_que_nao_e_opcional_e_ignorada_ao_ler(pedido):
    dados = pedido_para_dict(pedido)
    dados["secoes_fora"] = ["Açougue", "Mercearia", "Hortifruti"]
    assert pedido_de_dict(dados).secoes_fora == ("Hortifruti",)


def test_pedido_sem_orcamento_volta_sem_orcamento():
    dados = pedido_para_dict(Pedido(Convidados(adultos=3), SERVIR))
    assert pedido_de_dict(dados).orcamento is None


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


# ---------------------------------------------------------------- banco

def test_banco_novo_esta_vazio(banco):
    assert banco.listar() == []


def test_carregar_devolve_o_pedido_e_a_explicacao(banco, pedido):
    id = banco.salvar(pedido, "explicação")
    assert banco.carregar(id) == (pedido, "explicação")


def test_plano_salvo_sem_explicacao(banco, pedido):
    assert banco.carregar(banco.salvar(pedido))[1] is None


def test_listar_mostra_o_mais_novo_primeiro(banco, pedido):
    primeiro = banco.salvar(pedido, agora=ONTEM)
    segundo = banco.salvar(pedido, agora=HOJE)
    assert [p.id for p in banco.listar()] == [segundo, primeiro]


def test_listar_traz_o_resumo_do_plano(banco, pedido):
    banco.salvar(pedido, agora=ONTEM)
    salvo = banco.listar()[0]
    assert (salvo.nome, salvo.hora_servir, salvo.criado_em) == ("Teste", SERVIR, ONTEM)


def test_excluir_tira_o_plano_do_banco(banco, pedido):
    id = banco.salvar(pedido)
    assert banco.excluir(id) is True
    assert banco.listar() == []


def test_excluir_de_novo_devolve_false(banco, pedido):
    id = banco.salvar(pedido)
    banco.excluir(id)
    assert banco.excluir(id) is False


def test_carregar_plano_que_nao_existe_levanta_keyerror(banco):
    with pytest.raises(KeyError):
        banco.carregar(999)


def test_atualizar_explicacao(banco, pedido):
    id = banco.salvar(pedido)
    assert banco.atualizar_explicacao(id, "novo texto") is True
    assert banco.carregar(id)[1] == "novo texto"


def test_atualizar_explicacao_de_plano_que_nao_existe_devolve_false(banco):
    assert banco.atualizar_explicacao(999, "x") is False


def test_banco_em_arquivo_sobrevive_a_reabrir(tmp_path, pedido):
    caminho = tmp_path / "dados" / "planos.sqlite3"
    id = Armazenamento(caminho).salvar(pedido)
    assert Armazenamento(caminho).carregar(id)[0] == pedido


def test_registro_com_json_quebrado_levanta_valueerror(tmp_path, pedido):
    caminho = tmp_path / "p.sqlite3"
    banco = Armazenamento(caminho)
    id = banco.salvar(pedido)
    with sqlite3.connect(caminho) as con:
        con.execute("UPDATE planos SET dados = '{quebrado' WHERE id = ?", (id,))
    with pytest.raises(ValueError):
        banco.carregar(id)
