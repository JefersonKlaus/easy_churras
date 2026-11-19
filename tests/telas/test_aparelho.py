"""O que o app usa do aparelho: copiar, compartilhar e a tela em pé."""
import asyncio
import importlib
from types import SimpleNamespace

import pytest
from flet_falso import PaginaFalsa


@pytest.fixture
def aparelho_mod(modulo_app):
    """O módulo `aparelho`, carregado com o Flet de mentira."""
    return importlib.import_module("churrasco_facil.telas.aparelho")


class Celular(PaginaFalsa):
    """Página que diz ser de um celular e anota as orientações pedidas."""

    def __init__(self, mobile):
        super().__init__()
        self.platform = SimpleNamespace(is_mobile=lambda: mobile)
        self.orientacoes = None

    async def set_allowed_device_orientations(self, orientacoes):
        self.orientacoes = orientacoes


class ServicosFalsos:
    """Os serviços do Flet 1.0 (ft.Clipboard e ft.Share), anotando o que receberam."""

    def __init__(self, compartilhar_funciona=True):
        self.copiado, self.compartilhado = [], []
        self.compartilhar_funciona = compartilhar_funciona

    async def set(self, texto):                       # ft.Clipboard
        self.copiado.append(texto)

    async def share_text(self, texto, **_opcoes):     # ft.Share
        if not self.compartilhar_funciona:
            raise RuntimeError("sem compartilhar neste aparelho")
        self.compartilhado.append(texto)


def com_servicos(aparelho_mod, servicos):
    aparelho = aparelho_mod.Aparelho(PaginaFalsa())
    aparelho._servico = lambda _nome, _fabrica: servicos
    return aparelho


# ---------------------------------------------------------------- tela em pé

def test_no_celular_o_app_fica_em_pe(aparelho_mod):
    celular = Celular(mobile=True)
    asyncio.run(aparelho_mod.Aparelho(celular).travar_em_retrato())
    assert celular.orientacoes == ["PORTRAIT_UP"]


def test_no_computador_nao_tenta_travar_a_tela(aparelho_mod):
    computador = Celular(mobile=False)
    asyncio.run(aparelho_mod.Aparelho(computador).travar_em_retrato())
    assert computador.orientacoes is None


def test_celular_que_nao_deixa_travar_segue_sem_travar(aparelho_mod):
    class Teimoso(Celular):
        async def set_allowed_device_orientations(self, orientacoes):
            raise RuntimeError("não suportado")
    asyncio.run(aparelho_mod.Aparelho(Teimoso(mobile=True)).travar_em_retrato())


# ---------------------------------------------------------------- copiar e compartilhar

def test_copiar_usa_a_area_de_transferencia_do_flet_1(aparelho_mod):
    # no Flet 1.0 a página não copia: quem copia é o serviço ft.Clipboard
    servicos = ServicosFalsos()
    assert asyncio.run(com_servicos(aparelho_mod, servicos).copiar("lista")) is True
    assert servicos.copiado == ["lista"]


def test_sem_area_de_transferencia_nao_copia(aparelho_mod):
    assert asyncio.run(aparelho_mod.Aparelho(PaginaFalsa()).copiar("lista")) is False


def test_compartilhar_abre_o_compartilhar_do_aparelho(aparelho_mod):
    servicos = ServicosFalsos()
    resultado = asyncio.run(com_servicos(aparelho_mod, servicos).compartilhar("lista", "Lista"))
    assert resultado == aparelho_mod.COMPARTILHADO
    assert servicos.compartilhado == ["lista"] and servicos.copiado == []


def test_sem_compartilhar_no_aparelho_copia(aparelho_mod):
    servicos = ServicosFalsos(compartilhar_funciona=False)
    resultado = asyncio.run(com_servicos(aparelho_mod, servicos).compartilhar("lista", "Lista"))
    assert resultado == aparelho_mod.COPIADO and servicos.copiado == ["lista"]
