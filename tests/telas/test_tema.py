"""Tema visual: um lugar só para cores e medidas, botões grandes e sem barra de cima."""
import re
from pathlib import Path

import pytest

from flet_falso import PaginaFalsa

TELAS = Path(__file__).resolve().parents[2] / "src" / "churrasco_facil" / "telas"
COR = re.compile(r"#[0-9A-Fa-f]{6}\b")


@pytest.fixture
def tema(modulo_app):
    from churrasco_facil.telas import tema
    return tema


@pytest.fixture
def pagina_com_tema(tema):
    pagina = PaginaFalsa()
    tema.aplicar(pagina)
    return pagina


def test_tema_usa_a_cor_de_destaque_como_semente(tema, pagina_com_tema):
    assert pagina_com_tema.theme.color_scheme_seed == tema.PRIMARIA


def test_tema_usa_material_3(pagina_com_tema):
    assert pagina_com_tema.theme.use_material3 is True


def test_tema_define_o_fundo_e_a_margem(tema, pagina_com_tema):
    assert (pagina_com_tema.bgcolor, pagina_com_tema.padding) == (tema.FUNDO, tema.ESPACO)


def test_botao_grande_e_maior_que_o_alvo_minimo_de_toque(tema):
    assert tema.ALTURA_BOTAO >= 48


@pytest.mark.parametrize("arquivo", sorted(p.name for p in TELAS.glob("*.py")
                                           if p.name != "tema.py"))
def test_so_o_tema_define_cores(arquivo):
    assert COR.findall((TELAS / arquivo).read_text(encoding="utf-8")) == []
