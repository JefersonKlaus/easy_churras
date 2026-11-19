"""Fixtures usadas por vários arquivos de teste: os dados de exemplo do domínio e o app
rodando sobre o Flet de mentira (para as telas)."""
import importlib
import sys

import pytest
from dados import SERVIR
from dubles import cliente_falso
from flet_falso import FletFalso, PaginaFalsa

from churrasco_facil.armazenamento import Armazenamento
from churrasco_facil.configuracao import Configuracao
from churrasco_facil.convidados import Convidados
from churrasco_facil.planejador import Pedido, montar_plano

# ---------------------------------------------------------------- domínio


@pytest.fixture
def convidados():
    return Convidados(adultos=10, criancas=3, vegetarianos=1, bebem_alcool=6, duracao_horas=5)


@pytest.fixture
def pedido(convidados):
    return Pedido(convidados, SERVIR, nome="Teste")


@pytest.fixture
def plano(pedido):
    return montar_plano(pedido)


# ---------------------------------------------------------------- telas (Flet de mentira)

def _modulos_da_interface():
    return [n for n in sys.modules
            if n.startswith("churrasco_facil.telas") or n == "churrasco_facil.app"]


@pytest.fixture
def modulo_app(monkeypatch):
    """`churrasco_facil.app` importado com o Flet de mentira no lugar do verdadeiro."""
    monkeypatch.setitem(sys.modules, "flet", FletFalso("flet"))
    for nome in _modulos_da_interface():
        monkeypatch.delitem(sys.modules, nome)
    yield importlib.import_module("churrasco_facil.app")
    for nome in _modulos_da_interface():
        sys.modules.pop(nome, None)


@pytest.fixture
def pasta_de_dados(monkeypatch, tmp_path):
    """Dados do app numa pasta temporária e nenhuma chave do Groq no ambiente."""
    monkeypatch.setenv("CHURRASCO_DADOS", str(tmp_path))
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    return tmp_path


@pytest.fixture
def pagina():
    return PaginaFalsa()


@pytest.fixture
def app(modulo_app, pagina, pasta_de_dados):
    return modulo_app.AppChurrasco(pagina, Armazenamento(":memory:"), Configuracao())


@pytest.fixture
def ligar_groq(app):
    """Liga ao app um Groq falso com as respostas dadas. Devolve o transporte."""
    def ligar(*respostas):
        cliente, transporte = cliente_falso(*respostas, tentativas=1)
        app.config.chave_groq = cliente.chave
        app.cliente = lambda: cliente
        return transporte
    return ligar


@pytest.fixture
def plano_aberto(app, plano):
    """O plano do `pedido` aberto na aba Carnes."""
    app.novo_plano(plano)
    return plano


@pytest.fixture
def rascunho_pronto(app):
    """Um rascunho válido, com data no futuro."""
    r = app.rascunho
    r.adultos, r.criancas, r.vegetarianos, r.bebem_alcool, r.duracao_horas = 8, 2, 1, 4, 4
    r.data_texto, r.hora_texto = "21/11/2099", "14:00"
    return r
