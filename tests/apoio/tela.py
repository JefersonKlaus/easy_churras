"""Ler e usar o que foi desenhado: numa PaginaFalsa inteira ou num controle só.

Controles escondidos (visible=False) ficam de fora, como para quem usa o app.
"""
import asyncio
from types import SimpleNamespace

from flet_falso import PaginaFalsa


def todos(onde):
    """Todos os controles visíveis da página (ou de um controle), percorrendo a árvore.
    Um diálogo aberto também conta: ele fica por cima da tela."""
    if isinstance(onde, PaginaFalsa):
        raizes = onde.adicionados + ([onde.dialogo] if onde.dialogo else [])
    else:
        raizes = [onde]
    for raiz in raizes:
        yield from _arvore(raiz)


def _arvore(controle):
    if getattr(controle, "visible", True) is False:
        return
    yield controle
    for filho in (getattr(controle, "controls", None) or []) + \
            (getattr(controle, "actions", None) or []):
        yield from _arvore(filho)
    for parte in ("title", "content"):
        filho = getattr(controle, parte, None)
        if filho is not None and not isinstance(filho, str):
            yield from _arvore(filho)


def textos(onde):
    """Os textos visíveis (valores de chaves liga/desliga não são texto)."""
    return [c.value for c in todos(onde) if isinstance(c.value, str) and c.value]


def tem_texto(onde, trecho):
    """Algum texto na tela contém `trecho`?"""
    return any(trecho in t for t in textos(onde))


def achar(onde, valor):
    """Primeiro controle cujo texto é exatamente `valor`."""
    for controle in todos(onde):
        if controle.value == valor:
            return controle
    raise AssertionError(f"não achei {valor!r} na tela")


def campos(onde):
    """Campos de texto, pelo rótulo."""
    return {c.label: c for c in todos(onde) if hasattr(c, "label")}


def pelo_rotulo_de_acessibilidade(onde, rotulo):
    """O controle que o leitor de tela anuncia como `rotulo` (ex.: a caixa "Levar Picanha")."""
    for controle in todos(onde):
        if getattr(controle, "semantics_label", None) == rotulo:
            return controle
    raise AssertionError(f"não achei {rotulo!r} na tela")


def clicar(controle):
    resultado = controle.on_click(None)
    if asyncio.iscoroutine(resultado):
        asyncio.run(resultado)


def cartao_de(onde, texto):
    """A área clicável mais próxima (um cartão, um botão) que mostra `texto`."""
    alvo = achar(onde, texto)
    clicaveis = [c for c in todos(onde)
                 if getattr(c, "on_click", None) and any(d is alvo for d in todos(c))]
    if not clicaveis:
        raise AssertionError(f"{texto!r} não está numa área clicável")
    return clicaveis[-1]       # na ordem da árvore, o último é o mais interno


def tocar(onde, texto):
    """Toca na área clicável que mostra `texto`."""
    clicar(cartao_de(onde, texto))


def parte_que_rola(pagina):
    """O conteúdo da tela. O que fica fora dele (topo e rodapé) está sempre à vista."""
    return next(c for c in pagina.adicionados if getattr(c, "scroll", None))


def fixos(pagina):
    """Textos do topo e do rodapé fixos da tela."""
    rola = parte_que_rola(pagina)
    return [t for raiz in pagina.adicionados if raiz is not rola for t in textos(raiz)]


def tocar_icone(onde, dica):
    """Toca no primeiro ícone com essa dica (tooltip)."""
    clicar(next(c for c in todos(onde) if getattr(c, "tooltip", None) == dica
                and getattr(c, "on_click", None)))


def estados_dos_passos(pagina):
    """Estado de cada ícone do indicador de passos: 'feito', 'atual' ou 'depois'."""
    return [c.data for c in todos(pagina) if getattr(c, "data", None) in
            ("feito", "atual", "depois")]


def abas(pagina):
    """Rótulos da barra de abas no rodapé ([] se a tela não tem barra)."""
    barra = pagina.navigation_bar
    return [d.label for d in barra.destinations] if barra else []


def aba_selecionada(pagina):
    return abas(pagina)[pagina.navigation_bar.selected_index]


def ir_para_aba(pagina, rotulo):
    """Toca numa aba da barra do rodapé, como o Flet faria."""
    barra = pagina.navigation_bar
    barra.selected_index = abas(pagina).index(rotulo)
    barra.on_change(SimpleNamespace(control=barra))


def digitar(campo, texto):
    """Escreve no campo e, se ele escuta mudanças, avisa como o Flet faria."""
    campo.value = texto
    if getattr(campo, "on_change", None):
        campo.on_change(SimpleNamespace(control=campo))
