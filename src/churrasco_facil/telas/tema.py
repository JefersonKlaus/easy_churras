"""Tema visual do app (Material 3): cores, tamanhos e cantos. Mude aqui, muda o app todo."""
from __future__ import annotations

import flet as ft

# Cores: uma cor de destaque (laranja brasa) sobre neutros claros.
PRIMARIA = "#EA580C"
PRIMARIA_CLARA = "#FFEDD5"
FUNDO = "#FAFAF9"
SUPERFICIE = "#FFFFFF"
BORDA = "#E7E5E4"
TEXTO = "#1C1917"
SECUNDARIO = "#78716C"
APAGADO = "#D6D3D1"
SUCESSO = "#16A34A"
PERIGO = "#DC2626"
PERIGO_CLARO = "#FEF2F2"
PERIGO_BORDA = "#FECACA"

# Tamanhos: botões grandes (alvo de toque bem maior que o mínimo de 48) e cantos arredondados.
ALTURA_BOTAO = 56
RAIO = 16
RAIO_BOTAO = 14
ESPACO = 16


def aplicar(page: ft.Page) -> None:
    """Aplica o tema na página."""
    page.theme = ft.Theme(color_scheme_seed=PRIMARIA, use_material3=True)
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = FUNDO
    page.padding = ESPACO
