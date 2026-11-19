"""O rascunho do planejamento: o que a pessoa já contou nos passos do assistente."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .convidados import Convidados
from .entradas import combinar, formatar_data, ler_data, ler_hora, proximo_sabado


@dataclass
class Rascunho:
    """O que o assistente em passos já coletou."""

    adultos: int = 8
    criancas: int = 2
    vegetarianos: int = 0
    bebem_alcool: int = 4
    duracao_horas: int = 4
    data_texto: str = ""
    hora_texto: str = "14:00"
    texto_livre: str = ""

    def __post_init__(self) -> None:
        if not self.data_texto:
            self.data_texto = formatar_data(proximo_sabado())

    def ajustar_limites(self) -> None:
        """Mantém vegetarianos e quem bebe dentro do número de adultos."""
        self.vegetarianos = min(self.vegetarianos, self.adultos)
        self.bebem_alcool = min(self.bebem_alcool, self.adultos)

    def aplicar_interpretacao(self, adultos: Optional[int], criancas: Optional[int],
                              vegetarianos: Optional[int], bebem_alcool: Optional[int],
                              duracao_horas: Optional[float]) -> list[str]:
        """Copia o que o Groq entendeu. Devolve o que mudou, em texto simples."""
        mudou: list[str] = []
        if adultos is not None:
            self.adultos = adultos
            mudou.append(f"{adultos} adultos")
        if criancas is not None:
            self.criancas = criancas
            mudou.append(f"{criancas} crianças")
        if vegetarianos is not None:
            self.vegetarianos = vegetarianos
            mudou.append(f"{vegetarianos} vegetarianos")
        if bebem_alcool is not None:
            self.bebem_alcool = bebem_alcool
            mudou.append(f"{bebem_alcool} bebem álcool")
        if duracao_horas is not None:
            self.duracao_horas = max(1, min(12, round(duracao_horas)))
            mudou.append(f"festa de {self.duracao_horas} horas")
        self.ajustar_limites()
        return mudou

    def para_convidados(self) -> Convidados:
        return Convidados(adultos=self.adultos, criancas=self.criancas,
                          vegetarianos=self.vegetarianos, bebem_alcool=self.bebem_alcool,
                          duracao_horas=float(self.duracao_horas))

    def para_data_hora(self, agora: Optional[datetime] = None) -> datetime:
        """Data e hora de servir. Levanta ValueError se estiver no passado."""
        agora = agora or datetime.now()
        momento = combinar(ler_data(self.data_texto, agora.date()), ler_hora(self.hora_texto))
        if momento < agora:
            raise ValueError("essa data e hora já passaram")
        return momento
