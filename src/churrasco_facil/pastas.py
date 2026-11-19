"""Onde o app guarda os dados no aparelho (configuração e planos salvos)."""
from __future__ import annotations

import os
from pathlib import Path


def pasta_de_dados() -> Path:
    """CHURRASCO_DADOS (testes) > pasta de dados do Flet > pasta do usuário."""
    for variavel in ("CHURRASCO_DADOS", "FLET_APP_STORAGE_DATA"):
        valor = os.environ.get(variavel)
        if valor:
            return Path(valor)
    return Path.home() / ".churrasco_facil"
