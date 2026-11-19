"""A tabela de quantidades por pessoa (carne, bebida, carvão...). Vem da configuração."""
from __future__ import annotations

from dataclasses import dataclass, fields, replace
from typing import Any, Mapping, Optional


@dataclass(frozen=True)
class Parametros:
    """Tabela de quantidades por pessoa. O usuário pode editar tudo nas configurações."""

    carne_adulto_g: int = 400
    carne_crianca_g: int = 200
    vegetariano_g: int = 350
    cerveja_ml_por_bebedor: int = 1500
    refri_ml_por_pessoa_sem_alcool: int = 800
    agua_ml_por_pessoa: int = 500
    gelo_g_por_pessoa: int = 400
    pao_alho_por_pessoa: float = 1.0
    farofa_g_por_pessoa: int = 40
    carvao_kg_por_kg_de_carne: float = 1.0
    copos_por_pessoa: int = 3
    guardanapos_por_pessoa: int = 4
    pratos_por_pessoa: int = 2

    def fator_duracao(self, horas: float) -> float:
        """Quanto mais longo o churrasco, mais se come e se bebe."""
        if horas <= 3:
            return 1.0
        if horas <= 5:
            return 1.15
        return 1.3

    @classmethod
    def de_dicionario(cls, dados: Optional[Mapping[str, Any]]) -> "Parametros":
        """Cria a tabela a partir de um dicionário salvo, ignorando o que não for válido."""
        padrao = cls()
        if not dados:
            return padrao
        valores = {}
        for campo in fields(cls):
            if campo.name in dados:
                novo = dados[campo.name]
                antigo = getattr(padrao, campo.name)
                ok = isinstance(novo, (int, float)) and not isinstance(novo, bool) and novo >= 0
                if ok:
                    valores[campo.name] = type(antigo)(novo)
        return replace(padrao, **valores)
