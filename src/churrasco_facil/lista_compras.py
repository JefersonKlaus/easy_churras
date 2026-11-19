"""Lista de compras agrupada por seção do mercado."""
from __future__ import annotations

from .catalogo_carnes import Corte
from .dinheiro import formatar_reais
from .produtos import SECOES, ItemPlano


def formatar_peso(gramas: int) -> str:
    """950 -> '950 g'; 1200 -> '1,2 kg'; 4850 -> '4,85 kg'."""
    if gramas < 1000:
        return f"{gramas} g"
    return f"{gramas / 1000:.2f}".rstrip("0").rstrip(".").replace(".", ",") + " kg"


def formatar_unidades(quantas: int, embalagem: str) -> str:
    """1, 'peça' -> '1 peça'; 2, 'peça' -> '2 peças'."""
    return f"{quantas} {embalagem}" + ("s" if quantas != 1 else "")


def pecas(item: ItemPlano) -> int:
    """Quantas peças (pacotes, bandejas...) de um corte o item compra."""
    assert isinstance(item.produto, Corte)
    return -(-item.quantidade // item.produto.peca_g)


def formatar_quantidade(item: ItemPlano) -> str:
    """Corte: '2 peças · 2,4 kg'. Outros: 950 g -> '950 g'; 1200 ml -> '1,2 L';
    3 un -> '3 un'."""
    unidade, q = item.produto.unidade, item.quantidade
    if isinstance(item.produto, Corte):
        return (f"{formatar_unidades(pecas(item), item.produto.embalagem)} · "
                f"{formatar_peso(q)}")
    if unidade == "g":
        return formatar_peso(q)
    if unidade == "ml" and q >= 1000:
        litros = f"{q / 1000:.2f}".rstrip("0").rstrip(".").replace(".", ",")
        return f"{litros} L"
    return f"{q} {unidade}"


def agrupar_por_secao(itens: list[ItemPlano]) -> dict[str, list[ItemPlano]]:
    """Agrupa na ordem do mercado; seções fora da ordem conhecida vão para o final."""
    grupos: dict[str, list[ItemPlano]] = {}
    for item in itens:
        grupos.setdefault(item.produto.secao, []).append(item)
    ordem = [s for s in SECOES if s in grupos] + sorted(s for s in grupos if s not in SECOES)
    return {secao: sorted(grupos[secao], key=lambda i: i.produto.nome) for secao in ordem}


def linha_do_item(item: ItemPlano, com_preco: bool = True) -> str:
    texto = f"{item.produto.nome}: {formatar_quantidade(item)}"
    if item.observacao:
        texto += f" ({item.observacao.rstrip('.')})"
    if com_preco:
        texto += f" - {formatar_reais(item.custo)}"
    return texto
