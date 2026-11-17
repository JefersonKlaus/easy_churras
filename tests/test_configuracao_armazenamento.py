import json
from datetime import datetime

import pytest

from churrasco_facil.armazenamento import (Armazenamento, pedido_de_dict, pedido_para_dict)
from churrasco_facil.calculadora import Convidados, Parametros
from churrasco_facil.cliente_groq import MODELO_PADRAO
from churrasco_facil.configuracao import (Configuracao, carregar_configuracao, chave_efetiva,
                                          cliente_da_configuracao, parametros_da_configuracao,
                                          pasta_de_dados, salvar_configuracao)
from churrasco_facil.planejador import Pedido


# ---------------------------------------------------------------- configuração

def test_configuracao_vai_e_volta(tmp_path):
    caminho = tmp_path / "pasta" / "c.json"
    config = Configuracao(chave_groq="abc", modelo="outro-modelo", precos={"picanha": 9500},
                          parametros={"carne_adulto_g": 500})
    assert salvar_configuracao(config, caminho) is True
    assert carregar_configuracao(caminho) == config


def test_arquivo_da_configuracao_fica_restrito_ao_dono(tmp_path):
    caminho = tmp_path / "c.json"
    salvar_configuracao(Configuracao(chave_groq="segredo"), caminho)
    assert (caminho.stat().st_mode & 0o777) == 0o600


def test_arquivo_ausente_ou_corrompido_devolve_o_padrao(tmp_path):
    assert carregar_configuracao(tmp_path / "nao-existe.json") == Configuracao()
    for conteudo in ("{lixo", "[1]", "5"):
        caminho = tmp_path / "c.json"
        caminho.write_text(conteudo)
        assert carregar_configuracao(caminho) == Configuracao()


def test_valores_invalidos_sao_descartados(tmp_path):
    caminho = tmp_path / "c.json"
    caminho.write_text(json.dumps({
        "chave_groq": 5, "modelo": "  ", "precos": {"picanha": 9000, "zebra": 1, "alcatra": -1,
                                                    "maminha": True, "pao_alho": 450},
        "parametros": {"carne_adulto_g": 450, "carne_crianca_g": "x", "lixo": 1}}))
    config = carregar_configuracao(caminho)
    assert config.chave_groq == "" and config.modelo == MODELO_PADRAO
    assert config.precos == {"picanha": 9000, "pao_alho": 450}
    assert config.parametros == {"carne_adulto_g": 450}
    assert parametros_da_configuracao(config).carne_adulto_g == 450


def test_salvar_em_lugar_impossivel_devolve_false(tmp_path):
    assert salvar_configuracao(Configuracao(), tmp_path) is False   # o destino é uma pasta


def test_variavel_de_ambiente_vale_mais_que_a_chave_salva(monkeypatch):
    config = Configuracao(chave_groq="salva")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    assert chave_efetiva(config) == "salva"
    monkeypatch.setenv("GROQ_API_KEY", " do-ambiente ")
    assert chave_efetiva(config) == "do-ambiente"
    assert cliente_da_configuracao(config).chave == "do-ambiente"
    monkeypatch.delenv("GROQ_API_KEY")
    assert not cliente_da_configuracao(Configuracao()).configurado


def test_pasta_de_dados_segue_as_variaveis(monkeypatch, tmp_path):
    monkeypatch.delenv("FLET_APP_STORAGE_DATA", raising=False)
    monkeypatch.setenv("CHURRASCO_DADOS", str(tmp_path))
    assert pasta_de_dados() == tmp_path
    monkeypatch.delenv("CHURRASCO_DADOS")
    monkeypatch.setenv("FLET_APP_STORAGE_DATA", str(tmp_path / "flet"))
    assert pasta_de_dados() == tmp_path / "flet"
    monkeypatch.delenv("FLET_APP_STORAGE_DATA")
    assert pasta_de_dados().name == ".churrasco_facil"


def test_parametros_padrao_quando_nada_foi_alterado():
    assert parametros_da_configuracao(Configuracao()) == Parametros()


# ---------------------------------------------------------------- armazenamento

def test_pedido_vai_e_volta_pelo_dicionario(pedido):
    pedido = Pedido(pedido.convidados, pedido.hora_servir, 55000, {"alcatra": 2}, "Festa")
    assert pedido_de_dict(pedido_para_dict(pedido)) == pedido
    assert pedido_de_dict(json.loads(json.dumps(pedido_para_dict(pedido)))) == pedido


def test_pedido_sem_orcamento_e_com_cortes_invalidos():
    dados = pedido_para_dict(Pedido(Convidados(adultos=3), datetime(2026, 11, 21, 14, 0)))
    dados["pesos_preferidos"] = {"alcatra": 2, "zebra": 5}
    lido = pedido_de_dict(dados)
    assert lido.orcamento is None and lido.pesos_preferidos == {"alcatra": 2}


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


def test_salvar_listar_carregar_excluir(pedido):
    banco = Armazenamento(":memory:")
    assert banco.listar() == []
    primeiro = banco.salvar(pedido, "explicação", agora=datetime(2026, 11, 1, 9, 0))
    segundo = banco.salvar(Pedido(pedido.convidados, pedido.hora_servir, None, {}, "Outro"),
                           agora=datetime(2026, 11, 2, 9, 0))
    lista = banco.listar()
    assert [p.id for p in lista] == [segundo, primeiro]          # o mais novo primeiro
    assert lista[1].nome == "Teste" and lista[1].hora_servir == pedido.hora_servir
    assert lista[1].criado_em == datetime(2026, 11, 1, 9, 0)
    assert banco.carregar(primeiro) == (pedido, "explicação")
    assert banco.carregar(segundo)[1] is None
    assert banco.excluir(primeiro) is True and banco.excluir(primeiro) is False
    assert [p.id for p in banco.listar()] == [segundo]
    with pytest.raises(KeyError):
        banco.carregar(primeiro)


def test_atualizar_explicacao(pedido):
    banco = Armazenamento(":memory:")
    id = banco.salvar(pedido)
    assert banco.atualizar_explicacao(id, "novo texto") is True
    assert banco.carregar(id)[1] == "novo texto"
    assert banco.atualizar_explicacao(999, "x") is False


def test_banco_em_arquivo_sobrevive_a_reabrir(tmp_path, pedido):
    caminho = tmp_path / "dados" / "planos.sqlite3"
    id = Armazenamento(caminho).salvar(pedido)
    assert Armazenamento(caminho).carregar(id)[0] == pedido


def test_registro_com_json_quebrado_levanta_valueerror(tmp_path, pedido):
    import sqlite3
    caminho = tmp_path / "p.sqlite3"
    banco = Armazenamento(caminho)
    id = banco.salvar(pedido)
    with sqlite3.connect(caminho) as con:
        con.execute("UPDATE planos SET dados = '{quebrado' WHERE id = ?", (id,))
    with pytest.raises(ValueError):
        banco.carregar(id)
