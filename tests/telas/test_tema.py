"""O tema: as cores da marca no Material 3 e textos legíveis sobre os fundos do app."""
import importlib

import pytest
from flet_falso import PaginaFalsa


@pytest.fixture
def tema(modulo_app):
    return importlib.import_module("churrasco_facil.telas.tema")


def contraste(cor_a, cor_b):
    """Razão de contraste (WCAG) entre duas cores '#RRGGBB'."""
    def luz(cor):
        canais = [int(cor[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        canais = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in canais]
        return 0.2126 * canais[0] + 0.7152 * canais[1] + 0.0722 * canais[2]
    clara, escura = sorted((luz(cor_a), luz(cor_b)), reverse=True)
    return (clara + 0.05) / (escura + 0.05)


def test_aplicar_fixa_a_cor_da_marca_e_estica_o_conteudo(tema):
    # sem a cor fixa, o Material 3 gera um marrom; sem esticar, os títulos saem do centro
    pagina = PaginaFalsa()
    tema.aplicar(pagina)
    assert pagina.theme.color_scheme.primary == tema.PRIMARIA
    assert pagina.horizontal_alignment == "STRETCH"


@pytest.mark.parametrize("largura, lados", [(412, 16), (1024, 212)])
def test_em_tela_larga_o_conteudo_fica_no_meio(tema, largura, lados):
    # no tablet, o conteúdo não passa de LARGURA_MAXIMA (600): sobra margem dos lados
    pagina = PaginaFalsa()
    pagina.width = largura
    tema.aplicar(pagina)
    assert (pagina.padding.horizontal, pagina.padding.vertical) == (lados, tema.ESPACO)


@pytest.mark.parametrize("texto, fundo", [
    ("PRIMARIA", "SUPERFICIE"), ("PRIMARIA", "FUNDO"), ("PRIMARIA", "PRIMARIA_CLARA"),
    ("SUPERFICIE", "PRIMARIA"),                     # texto branco nos botões cheios
    ("SECUNDARIO", "SUPERFICIE"), ("PERIGO", "PERIGO_CLARO"), ("CERTO", "CERTO_CLARO"),
    ("ATENCAO", "ATENCAO_CLARO"),
])
def test_texto_e_legivel_sobre_o_fundo(tema, texto, fundo):
    # 4,5:1 é o mínimo de contraste para texto pequeno (WCAG AA)
    assert contraste(getattr(tema, texto), getattr(tema, fundo)) >= 4.5
