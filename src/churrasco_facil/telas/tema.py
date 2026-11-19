"""Tema visual do app (Material 3): cores, tamanhos e cantos. Mude aqui, muda o app todo."""
from __future__ import annotations

import flet as ft

# Cores: uma cor de destaque (laranja brasa) sobre neutros claros. O laranja é escuro o
# bastante para texto pequeno (contraste 5,2:1 com o branco, acima do mínimo de 4,5:1).
PRIMARIA = "#C2410C"
PRIMARIA_CLARA = "#FFEDD5"
FUNDO = "#FAFAF9"
SUPERFICIE = "#FFFFFF"
BORDA = "#E7E5E4"
TEXTO = "#1C1917"
SECUNDARIO = "#78716C"
APAGADO = "#D6D3D1"
SUCESSO = "#16A34A"
# Alertas: texto escuro sobre fundo claro (contraste acima de 4,5:1 nos três).
PERIGO = "#B91C1C"              # vermelho: falta (e cuidados graves)
PERIGO_CLARO = "#FEF2F2"
PERIGO_BORDA = "#FECACA"
CERTO = "#166534"               # verde: na medida
CERTO_CLARO = "#DCFCE7"
CERTO_BORDA = "#BBF7D0"
ATENCAO = "#854D0E"             # amarelo: demais
ATENCAO_CLARO = "#FEF9C3"
ATENCAO_BORDA = "#FDE68A"

# Tamanhos: botões grandes (alvo de toque bem maior que o mínimo de 48) e cantos arredondados.
ALTURA_BOTAO = 56
RAIO = 16
RAIO_BOTAO = 14
ESPACO = 16
LARGURA_MAXIMA = 600   # em telas largas (tablet, computador) o conteúdo fica no meio


def aplicar(page: ft.Page) -> None:
    """Aplica o tema na página. As cores principais são fixadas: só a semente faria o
    Material 3 gerar um marrom no lugar do laranja."""
    page.theme = ft.Theme(
        color_scheme_seed=PRIMARIA, use_material3=True,
        color_scheme=ft.ColorScheme(primary=PRIMARIA, on_primary=SUPERFICIE,
                                    primary_container=PRIMARIA_CLARA,
                                    on_primary_container=TEXTO,
                                    secondary_container=PRIMARIA_CLARA,
                                    on_secondary_container=TEXTO))
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = FUNDO
    # Topo e rodapé ocupam a largura toda: assim os textos centralizados ficam no meio.
    page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
    ajustar_margens(page)

    def mudou_o_tamanho(_evento) -> None:
        ajustar_margens(page)
        page.update()

    page.on_resize = mudou_o_tamanho


def ajustar_margens(page: ft.Page) -> None:
    """Margem de ESPACO no celular; numa tela larga, margens maiores dos lados, para o
    conteúdo não passar de LARGURA_MAXIMA e ficar no meio."""
    largura = getattr(page, "width", None) or 0
    lados = max(ESPACO, (largura - LARGURA_MAXIMA) / 2)
    page.padding = ft.Padding.symmetric(horizontal=lados, vertical=ESPACO)
