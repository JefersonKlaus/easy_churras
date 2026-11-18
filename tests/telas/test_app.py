import asyncio
from types import SimpleNamespace

import pytest

from flet_falso import PaginaFalsa
from tela import textos


@pytest.fixture
def pagina_do_main(modulo_app, pasta_de_dados):
    pagina = PaginaFalsa()
    asyncio.run(modulo_app.main(pagina))
    return pagina


def test_main_configura_a_janela(pagina_do_main):
    assert (pagina_do_main.title, pagina_do_main.window.width) == ("Churrasco Fácil", 430)


def test_main_aplica_o_tema(pagina_do_main):
    from churrasco_facil.telas import tema
    assert pagina_do_main.bgcolor == tema.FUNDO
    assert pagina_do_main.theme.color_scheme_seed == tema.PRIMARIA


def test_main_abre_a_tela_inicial(pagina_do_main):
    assert "Planejar um churrasco" in textos(pagina_do_main)


# ---------------------------------------------------------------- celular em pé (retrato)

class Celular(PaginaFalsa):
    """Página que diz ser de um celular e anota as orientações pedidas."""

    def __init__(self, mobile):
        super().__init__()
        self.platform = SimpleNamespace(is_mobile=lambda: mobile)
        self.orientacoes = None

    async def set_allowed_device_orientations(self, orientacoes):
        self.orientacoes = orientacoes


def test_no_celular_o_app_fica_em_pe(modulo_app, pasta_de_dados):
    celular = Celular(mobile=True)
    asyncio.run(modulo_app.main(celular))
    assert celular.orientacoes == ["PORTRAIT_UP"]


def test_no_computador_nao_tenta_travar_a_tela(modulo_app, pasta_de_dados):
    computador = Celular(mobile=False)
    asyncio.run(modulo_app.main(computador))
    assert computador.orientacoes is None


def test_celular_que_nao_deixa_travar_nao_quebra_o_app(modulo_app, pasta_de_dados):
    class Teimoso(Celular):
        async def set_allowed_device_orientations(self, orientacoes):
            raise RuntimeError("não suportado")
    celular = Teimoso(mobile=True)
    asyncio.run(modulo_app.main(celular))
    assert "Planejar um churrasco" in textos(celular)


# ---------------------------------------------------------------- salvar sozinho

@pytest.mark.usefixtures("plano_aberto")
def test_salvar_plano_guarda_uma_vez_so(app):
    app.salvar_plano()
    app.salvar_plano()
    assert len(app.banco.listar()) == 1


def test_salvar_plano_sem_plano_nao_faz_nada(app):
    app.salvar_plano()
    assert app.banco.listar() == [] and app.aviso == ""


@pytest.mark.usefixtures("plano_aberto")
def test_plano_aberto_dos_salvos_nao_e_salvo_de_novo(app):
    app.salvar_plano()
    app.abrir_salvo(app.plano_id)
    app.ir_lista()
    assert len(app.banco.listar()) == 1


@pytest.mark.parametrize("ir", ["ir_plano", "ir_lista", "ir_cronograma", "ir_conversa"])
def test_aba_do_plano_sem_plano_avisa_e_oferece_o_inicio(app, pagina, ir):
    getattr(app, ir)()
    assert "Nenhum plano aberto" in textos(pagina) and "Início" in textos(pagina)
