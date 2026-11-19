"""Quem vem ao churrasco: adultos, crianças, vegetarianos, quem bebe e quanto tempo dura."""
from __future__ import annotations

from dataclasses import dataclass

MAX_PESSOAS = 200


@dataclass(frozen=True)
class Convidados:
    """Quem vem ao churrasco."""

    adultos: int
    criancas: int = 0
    vegetarianos: int = 0       # fazem parte dos adultos
    bebem_alcool: int = 0       # fazem parte dos adultos
    duracao_horas: float = 4.0

    def __post_init__(self) -> None:
        if self.adultos < 0 or self.criancas < 0:
            raise ValueError("o número de pessoas não pode ser negativo")
        if self.pessoas < 1:
            raise ValueError("precisa vir pelo menos uma pessoa")
        if self.pessoas > MAX_PESSOAS:
            raise ValueError(f"o máximo é {MAX_PESSOAS} pessoas")
        if not 0 <= self.vegetarianos <= self.adultos:
            raise ValueError("vegetarianos precisam estar entre os adultos")
        if not 0 <= self.bebem_alcool <= self.adultos:
            raise ValueError("quem bebe álcool precisa estar entre os adultos")
        if not 1 <= self.duracao_horas <= 12:
            raise ValueError("a duração deve ficar entre 1 e 12 horas")

    @property
    def pessoas(self) -> int:
        return self.adultos + self.criancas

    @property
    def comem_carne(self) -> int:
        return self.adultos - self.vegetarianos
