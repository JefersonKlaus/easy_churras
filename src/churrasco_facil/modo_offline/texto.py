"""Texto digitado de qualquer jeito, pronto para comparar."""
from __future__ import annotations

import unicodedata


def normalizar(texto: str) -> str:
    """Minúsculas e sem acento, para comparar texto digitado de qualquer jeito."""
    base = unicodedata.normalize("NFD", (texto or "").lower())
    return "".join(c for c in base if unicodedata.category(c) != "Mn")
