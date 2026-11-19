"""Dinheiro sempre em centavos inteiros: nunca usamos float para valores."""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation


def reais_para_centavos(texto: str) -> int:
    """Converte "12,50", "R$ 1.234,56" ou "12.5" em centavos. Levanta ValueError se não der."""
    limpo = texto.strip().replace("R$", "").replace(" ", "")
    if not limpo:
        raise ValueError("valor vazio")
    if "," in limpo:
        limpo = limpo.replace(".", "").replace(",", ".")
    elif limpo.count(".") > 1:
        limpo = limpo.replace(".", "")
    try:
        valor = Decimal(limpo)
    except InvalidOperation:
        raise ValueError(f"valor inválido: {texto!r}") from None
    if not valor.is_finite():
        raise ValueError(f"valor inválido: {texto!r}")
    if valor < 0:
        raise ValueError("o valor não pode ser negativo")
    return int((valor * 100).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def formatar_reais(centavos: int) -> str:
    """12345 -> 'R$ 123,45' (com ponto nos milhares)."""
    sinal = "-" if centavos < 0 else ""
    reais, resto = divmod(abs(centavos), 100)
    return f"{sinal}R$ {reais:,}".replace(",", ".") + f",{resto:02d}"


def valor_para_campo(centavos: int) -> str:
    """12345 -> '123,45': o valor como a pessoa digitaria num campo de texto."""
    return f"{centavos / 100:.2f}".replace(".", ",")


def custo_proporcional(preco: int, por_quantidade: int, quantidade: int) -> int:
    """Custo em centavos de `quantidade` quando `por_quantidade` custa `preco` (arredonda
    para cima na metade). Ex.: R$ 40,00 o kg e 250 g -> custo_proporcional(4000, 1000, 250)."""
    if por_quantidade < 1:
        raise ValueError("por_quantidade deve ser pelo menos 1")
    return (preco * quantidade * 2 + por_quantidade) // (2 * por_quantidade)
