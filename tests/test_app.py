"""O aplicativo: abrir, salvar o plano e as abas sem plano."""
import asyncio

import pytest
from flet_falso import PaginaFalsa
from tela import textos


@pytest.fixture
def pagina_do_main(modulo_app, pasta_de_dados):
    pagina = PaginaFalsa()
    asyncio.run(modulo_app.main(pagina))
    return pagina


def test_main_abre_a_tela_inicial(pagina_do_main):
    assert "Planejar um churrasco" in textos(pagina_do_main)


@pytest.mark.usefixtures("plano_aberto")
def test_salvar_plano_guarda_uma_vez_so(app):
    app.salvar_plano()
    app.salvar_plano()
    assert len(app.banco.listar()) == 1


def test_salvar_plano_sem_plano_nao_faz_nada(app):
    app.salvar_plano()
    assert app.banco.listar() == [] and app.aviso == ""


@pytest.mark.usefixtures("plano_aberto")
def test_plano_aberto_dos_salvos_ja_esta_salvo(app):
    app.salvar_plano()
    app.abrir_salvo(app.plano_id)
    assert app.salvo is True and len(app.banco.listar()) == 1


@pytest.mark.parametrize("ir", ["ir_carnes", "ir_compras", "ir_horarios"])
def test_aba_do_plano_sem_plano_avisa_e_oferece_o_inicio(app, pagina, ir):
    getattr(app, ir)()
    assert "Nenhum plano aberto" in textos(pagina) and "Início" in textos(pagina)
