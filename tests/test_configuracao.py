import json

import pytest

from churrasco_facil.calculadora import Parametros
from churrasco_facil.cliente_groq import MODELO_PADRAO
from churrasco_facil.configuracao import (Configuracao, carregar_configuracao, chave_efetiva,
                                          cliente_da_configuracao, juntar_precos,
                                          parametros_da_configuracao, pasta_de_dados,
                                          salvar_configuracao)


@pytest.fixture
def arquivo(tmp_path):
    return tmp_path / "c.json"


@pytest.fixture
def sem_variaveis(monkeypatch):
    for variavel in ("GROQ_API_KEY", "CHURRASCO_DADOS", "FLET_APP_STORAGE_DATA"):
        monkeypatch.delenv(variavel, raising=False)
    return monkeypatch


def carregar(arquivo, dados):
    arquivo.write_text(json.dumps(dados))
    return carregar_configuracao(arquivo)


# ---------------------------------------------------------------- arquivo

def test_configuracao_salva_volta_igual(tmp_path):
    caminho = tmp_path / "pasta" / "c.json"
    config = Configuracao(chave_groq="abc", modelo="outro-modelo", precos={"picanha": 9500},
                          parametros={"carne_adulto_g": 500})
    assert salvar_configuracao(config, caminho) is True
    assert carregar_configuracao(caminho) == config


def test_arquivo_da_configuracao_fica_restrito_ao_dono(arquivo):
    salvar_configuracao(Configuracao(chave_groq="segredo"), arquivo)
    assert (arquivo.stat().st_mode & 0o777) == 0o600


def test_salvar_em_lugar_impossivel_devolve_false(tmp_path):
    assert salvar_configuracao(Configuracao(), tmp_path) is False   # o destino é uma pasta


def test_arquivo_ausente_devolve_o_padrao(tmp_path):
    assert carregar_configuracao(tmp_path / "nao-existe.json") == Configuracao()


@pytest.mark.parametrize("conteudo", ["{lixo", "[1]", "5"])
def test_arquivo_corrompido_devolve_o_padrao(arquivo, conteudo):
    arquivo.write_text(conteudo)
    assert carregar_configuracao(arquivo) == Configuracao()


# ---------------------------------------------------------------- valores lidos

def test_chave_que_nao_e_texto_e_descartada(arquivo):
    assert carregar(arquivo, {"chave_groq": 5}).chave_groq == ""


def test_modelo_em_branco_vira_o_padrao(arquivo):
    assert carregar(arquivo, {"modelo": "  "}).modelo == MODELO_PADRAO


def test_precos_invalidos_sao_descartados(arquivo):
    precos = {"picanha": 9000, "zebra": 1, "alcatra": -1, "maminha": True, "pao_alho": 450}
    assert carregar(arquivo, {"precos": precos}).precos == {"picanha": 9000, "pao_alho": 450}


def test_parametros_invalidos_sao_descartados(arquivo):
    parametros = {"carne_adulto_g": 450, "carne_crianca_g": "x", "lixo": 1}
    assert carregar(arquivo, {"parametros": parametros}).parametros == {"carne_adulto_g": 450}


# ---------------------------------------------------------------- preços digitados

def test_juntar_precos_guarda_o_preco_digitado_em_centavos():
    assert juntar_precos({}, {"picanha": "95,00"}) == {"picanha": 9500}


def test_juntar_precos_mantem_os_outros_precos_salvos():
    assert juntar_precos({"pao_alho": 450}, {"picanha": "95,00"}) == \
        {"pao_alho": 450, "picanha": 9500}


def test_preco_igual_ao_do_catalogo_nao_e_guardado():
    assert juntar_precos({}, {"picanha": "90,00"}) == {}


def test_voltar_ao_preco_do_catalogo_apaga_o_personalizado():
    assert juntar_precos({"picanha": 9500}, {"picanha": "90,00"}) == {}


@pytest.mark.parametrize("texto", ["caro", "-3", "99999999"])
def test_preco_invalido_levanta_valueerror_com_o_nome_do_produto(texto):
    with pytest.raises(ValueError, match="Picanha"):
        juntar_precos({}, {"picanha": texto})


# ---------------------------------------------------------------- o que o app usa

def test_parametros_padrao_quando_nada_foi_alterado():
    assert parametros_da_configuracao(Configuracao()) == Parametros()


def test_parametros_alterados_valem_nas_contas():
    config = Configuracao(parametros={"carne_adulto_g": 450})
    assert parametros_da_configuracao(config).carne_adulto_g == 450


def test_sem_variavel_de_ambiente_vale_a_chave_salva(sem_variaveis):
    assert chave_efetiva(Configuracao(chave_groq="salva")) == "salva"


def test_variavel_de_ambiente_vale_mais_que_a_chave_salva(sem_variaveis):
    sem_variaveis.setenv("GROQ_API_KEY", " do-ambiente ")
    assert chave_efetiva(Configuracao(chave_groq="salva")) == "do-ambiente"


def test_cliente_usa_a_chave_efetiva(sem_variaveis):
    sem_variaveis.setenv("GROQ_API_KEY", "do-ambiente")
    assert cliente_da_configuracao(Configuracao()).chave == "do-ambiente"


def test_cliente_sem_chave_nao_fica_configurado(sem_variaveis):
    assert not cliente_da_configuracao(Configuracao()).configurado


def test_pasta_de_dados_do_app_vale_primeiro(sem_variaveis, tmp_path):
    sem_variaveis.setenv("CHURRASCO_DADOS", str(tmp_path))
    sem_variaveis.setenv("FLET_APP_STORAGE_DATA", str(tmp_path / "flet"))
    assert pasta_de_dados() == tmp_path


def test_pasta_de_dados_do_flet_vale_em_seguida(sem_variaveis, tmp_path):
    sem_variaveis.setenv("FLET_APP_STORAGE_DATA", str(tmp_path / "flet"))
    assert pasta_de_dados() == tmp_path / "flet"


def test_pasta_de_dados_padrao_fica_na_pasta_do_usuario(sem_variaveis):
    assert pasta_de_dados().name == ".churrasco_facil"
