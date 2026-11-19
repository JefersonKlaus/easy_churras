"""Meus churrascos: os planos salvos no banco."""
import sqlite3
from dataclasses import replace
from datetime import datetime

import pytest
from dados import SERVIR

from churrasco_facil.armazenamento import Armazenamento

ONTEM, HOJE = datetime(2026, 11, 1, 9, 0), datetime(2026, 11, 2, 9, 0)


@pytest.fixture
def banco():
    return Armazenamento(":memory:")


def test_carregar_devolve_o_pedido(banco, pedido):
    assert banco.carregar(banco.salvar(pedido)) == pedido


def test_atualizar_grava_por_cima_do_mesmo_plano(banco, pedido):
    id = banco.salvar(pedido)
    trocado = replace(pedido, pecas_escolhidas={"alcatra": 3})
    assert banco.atualizar(id, trocado) is True
    assert banco.carregar(id) == trocado and len(banco.listar()) == 1


def test_listar_mostra_o_mais_novo_primeiro(banco, pedido):
    primeiro = banco.salvar(pedido, agora=ONTEM)
    segundo = banco.salvar(pedido, agora=HOJE)
    assert [p.id for p in banco.listar()] == [segundo, primeiro]


def test_listar_traz_o_resumo_do_plano(banco, pedido):
    banco.salvar(pedido, agora=ONTEM)
    salvo = banco.listar()[0]
    assert (salvo.nome, salvo.hora_servir) == ("Teste", SERVIR)


def test_excluir_tira_o_plano_do_banco(banco, pedido):
    id = banco.salvar(pedido)
    assert banco.excluir(id) is True
    assert banco.listar() == []


def test_carregar_plano_que_nao_existe_levanta_keyerror(banco):
    with pytest.raises(KeyError):
        banco.carregar(999)


def test_banco_em_arquivo_sobrevive_a_reabrir(tmp_path, pedido):
    caminho = tmp_path / "dados" / "planos.sqlite3"
    id = Armazenamento(caminho).salvar(pedido)
    assert Armazenamento(caminho).carregar(id) == pedido


def test_registro_com_json_quebrado_levanta_valueerror(tmp_path, pedido):
    caminho = tmp_path / "p.sqlite3"
    banco = Armazenamento(caminho)
    id = banco.salvar(pedido)
    with sqlite3.connect(caminho) as con:
        con.execute("UPDATE planos SET dados = '{quebrado' WHERE id = ?", (id,))
    with pytest.raises(ValueError):
        banco.carregar(id)
