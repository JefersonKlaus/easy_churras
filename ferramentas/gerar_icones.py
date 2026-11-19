"""Gera o ícone do app e as imagens das lojas a partir do símbolo de churrasqueira.

    python ferramentas/gerar_icones.py

Precisa de `pip install "flet[all]" pillow fonttools brotli` (o símbolo e a fonte vêm do
Flet). Grava:

- src/assets/icon.png: o símbolo branco sobre fundo transparente. O `flet build` gera daqui
  todos os tamanhos de cada plataforma, com a margem certa e o fundo laranja
  (`icon_background` no pyproject.toml).
- src/assets/icon_android.png: o ícone pronto do Android, já com o fundo laranja (sem ele,
  o ícone dos Androids antigos sairia branco sobre transparente).
- src/assets/splash.png: o símbolo laranja, para a tela de abertura (fundo claro).
- docs/icones/: o que se envia às lojas à mão (ícone da App Store, ícone e imagem de destaque
  do Google Play) e uma prévia dos ícones.
"""
from __future__ import annotations

import io
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

RAIZ = Path(__file__).resolve().parents[1]
ASSETS = RAIZ / "src" / "assets"
DOCS = RAIZ / "docs" / "icones"

LARANJA = "#C2410C"        # a cor de destaque do app (telas/tema.py: PRIMARIA)
LARANJA_CLARO = "#EA580C"
BRANCO = "#FFFFFF"
FUNDO = "#FAFAF9"          # o fundo das telas (telas/tema.py: FUNDO)
CHURRASQUEIRA = 0xF003A    # "outdoor_grill" (arredondado) na fonte Material Icons do Flet


def _fontes() -> tuple[Path, Path]:
    """A fonte de ícones e a Roboto (convertida de woff2) que vêm com o Flet."""
    import flet_web
    from fontTools.ttLib import TTFont

    pasta = Path(flet_web.__file__).parent / "web" / "assets" / "fonts"
    roboto = io.BytesIO()
    fonte = TTFont(pasta / "roboto.woff2")
    fonte.flavor = None
    fonte.save(roboto)
    destino = Path("/tmp/churrasco_roboto.ttf")
    destino.write_bytes(roboto.getvalue())
    return pasta / "MaterialIcons-Regular.otf", destino


ICONES, ROBOTO = _fontes()


def simbolo(lado: int, cor: str) -> Image.Image:
    """A churrasqueira numa imagem transparente, com `lado` px no maior lado."""
    grande = 4096
    fonte = ImageFont.truetype(str(ICONES), grande)
    tela = Image.new("RGBA", (grande * 2, grande * 2), (0, 0, 0, 0))
    ImageDraw.Draw(tela).text((grande // 2, grande // 2), chr(CHURRASQUEIRA), font=fonte,
                              fill=cor)
    tela = tela.crop(tela.getbbox())
    escala = lado / max(tela.size)
    return tela.resize((round(tela.width * escala), round(tela.height * escala)),
                       Image.LANCZOS)


def no_centro(fundo: Image.Image, figura: Image.Image, dy: int = 0) -> Image.Image:
    fundo.alpha_composite(figura, ((fundo.width - figura.width) // 2,
                                   (fundo.height - figura.height) // 2 + dy))
    return fundo


def icone_quadrado(lado: int, ocupa: float = 0.60) -> Image.Image:
    """Ícone pronto: fundo laranja cheio (sem transparência) e a churrasqueira no meio."""
    fundo = Image.new("RGBA", (lado, lado), LARANJA)
    return no_centro(fundo, simbolo(round(lado * ocupa), BRANCO)).convert("RGB")


def icone_android(lado: int = 1024) -> Image.Image:
    """O ícone do Android, pronto e sem transparência (os ícones antigos, de antes do
    Android 8, não têm fundo próprio). A churrasqueira fica dentro do círculo que os
    lançadores nunca cortam: o mesmo enquadramento que o Flet usa (56,7% do meio lado)."""
    from flet_platform_assets._imaging import radial_extent

    teste = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    cheio = radial_extent(no_centro(teste, simbolo(lado, BRANCO)))
    return icone_quadrado(lado, ocupa=0.567 / cheio)


def texto(desenho: ImageDraw.ImageDraw, xy: tuple[int, int], conteudo: str, tamanho: int,
          cor: str, grosso: int = 0) -> None:
    fonte = ImageFont.truetype(str(ROBOTO), tamanho)
    desenho.text(xy, conteudo, font=fonte, fill=cor, stroke_width=grosso, stroke_fill=cor)


def destaque_google_play() -> Image.Image:
    """Imagem de destaque do Google Play (1024 x 500): o ícone, o nome e a frase do app."""
    img = Image.new("RGBA", (1024, 500), LARANJA)
    desenho = ImageDraw.Draw(img)
    for y in range(500):                      # degradê suave, mais claro em cima
        mistura = y / 499
        cor = tuple(round(a + (b - a) * mistura) for a, b in
                    zip((234, 88, 12), (194, 65, 12)))
        desenho.line([(0, y), (1024, y)], fill=cor)
    img.alpha_composite(simbolo(250, BRANCO), (90, 125))
    texto(desenho, (400, 150), "Churrasco Fácil", 76, BRANCO, grosso=2)
    texto(desenho, (402, 260), "Quanto comprar, quanto custa", 34, BRANCO)
    texto(desenho, (402, 305), "e a que horas fazer cada coisa.", 34, BRANCO)
    return img.convert("RGB")


def previa(icone: Image.Image) -> Image.Image:
    """Como o ícone aparece: quadrado (iOS), redondo (Android) e pequeno, em fundo claro."""
    folha = Image.new("RGB", (900, 320), FUNDO)
    quadrado = icone.resize((220, 220), Image.LANCZOS)
    mascara = Image.new("L", (220, 220), 0)
    ImageDraw.Draw(mascara).rounded_rectangle((0, 0, 219, 219), radius=50, fill=255)
    folha.paste(quadrado, (40, 50), mascara)
    redondo = Image.new("L", (220, 220), 0)
    ImageDraw.Draw(redondo).ellipse((0, 0, 219, 219), fill=255)
    folha.paste(quadrado, (330, 50), redondo)
    for i, lado in enumerate((96, 48)):
        pequeno = icone.resize((lado, lado), Image.LANCZOS)
        m = Image.new("L", (lado, lado), 0)
        ImageDraw.Draw(m).rounded_rectangle((0, 0, lado - 1, lado - 1), radius=lado // 4,
                                            fill=255)
        folha.paste(pequeno, (620 + i * 140, 110 + (96 - lado) // 2), m)
    return folha


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)
    # para o `flet build`: o símbolo ocupa quase todo o quadro; o Flet põe a margem de cada
    # plataforma e o fundo laranja
    base = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    no_centro(base, simbolo(1000, BRANCO)).save(ASSETS / "icon.png")
    icone_android().save(ASSETS / "icon_android.png")
    abertura = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    no_centro(abertura, simbolo(560, LARANJA)).save(ASSETS / "splash.png")
    # para as lojas
    app_store = icone_quadrado(1024)
    app_store.save(DOCS / "app-store-1024.png")               # sem transparência
    icone_quadrado(512).save(DOCS / "google-play-512.png")
    destaque_google_play().save(DOCS / "google-play-destaque-1024x500.png")
    previa(app_store).save(DOCS / "previa.png")
    print("ícones gerados em", ASSETS.relative_to(RAIZ), "e", DOCS.relative_to(RAIZ))


if __name__ == "__main__":
    main()
