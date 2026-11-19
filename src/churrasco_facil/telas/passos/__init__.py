"""Assistente em 4 passos, um assunto por tela: preços, quem vem, quando e a escolha.

Em cima, ícones mostram em que passo a pessoa está; embaixo, Voltar e Próximo ficam fixos.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from .. import widgets as w
from . import escolha, precos, quando, quem_vem

if TYPE_CHECKING:
    from ...app import AppChurrasco


def montar(app: AppChurrasco, passo: int) -> w.Tela:
    passos = (precos.montar, quem_vem.montar, quando.montar, escolha.montar)
    return passos[max(0, min(passo, len(passos) - 1))](app)
