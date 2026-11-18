"""Lista de compras agrupada por seção do mercado."""
from __future__ import annotations

from .dinheiro import formatar_reais
from .produtos import SECOES, ItemPlano


def formatar_quantidade(item: ItemPlano) -> str:
    """950 g -> '950 g'; 1200 g -> '1,2 kg'; 3 un -> '3 un'."""
    unidade, q = item.produto.unidade, item.quantidade
    if unidade == "g" and q >= 1000:
        kg = q / 1000
        texto = f"{kg:.2f}".rstrip("0").rstrip(".").replace(".", ",")
        return f"{texto} kg"
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


def texto_dos_lembretes(lembretes: list[ItemPlano]) -> str:
    """O que não entra na conta, mas não pode ser esquecido. Vazio se não houver nada."""
    if not lembretes:
        return ""
    return "\n".join(["NÃO ESQUEÇA (fora da conta)"]
                     + [f"- {linha_do_item(i, com_preco=False)}" for i in lembretes])


def texto_da_lista(itens: list[ItemPlano], com_preco: bool = True) -> str:
    """A lista inteira em texto simples, uma seção por bloco."""
    blocos = []
    for secao, grupo in agrupar_por_secao(itens).items():
        linhas = [f"{secao.upper()}"] + [f"- {linha_do_item(i, com_preco)}" for i in grupo]
        blocos.append("\n".join(linhas))
    return "\n\n".join(blocos)
