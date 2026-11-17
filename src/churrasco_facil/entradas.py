"""Leitura e validação do que o usuário digita (datas, horas, valores)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Optional

from .calculadora import Convidados
from .dinheiro import formatar_reais, reais_para_centavos


def ler_data(texto: str, hoje: Optional[date] = None) -> date:
    """Aceita 'dd/mm/aaaa' ou 'dd/mm' (assume este ano, ou o próximo se já passou)."""
    hoje = hoje or date.today()
    partes = texto.strip().replace("-", "/").replace(".", "/").split("/")
    try:
        numeros = [int(p) for p in partes]
    except ValueError:
        raise ValueError("escreva a data assim: 21/11/2026") from None
    if len(numeros) == 2:
        dia, mes = numeros
        try:
            data = date(hoje.year, mes, dia)
        except ValueError:
            raise ValueError("essa data não existe") from None
        return data if data >= hoje else date(hoje.year + 1, mes, dia)
    if len(numeros) == 3:
        dia, mes, ano = numeros
        if ano < 100:
            ano += 2000
        try:
            return date(ano, mes, dia)
        except ValueError:
            raise ValueError("essa data não existe") from None
    raise ValueError("escreva a data assim: 21/11/2026")


def ler_hora(texto: str) -> time:
    """Aceita '14:00', '14h', '14h30' ou '14'."""
    limpo = texto.strip().lower().replace("h", ":").replace(".", ":")
    if limpo.endswith(":"):
        limpo += "00"
    partes = limpo.split(":")
    try:
        horas = int(partes[0])
        minutos = int(partes[1]) if len(partes) > 1 and partes[1] else 0
        if len(partes) > 2:
            raise ValueError
        return time(horas, minutos)
    except (ValueError, IndexError):
        raise ValueError("escreva a hora assim: 14:00") from None


def ler_orcamento(texto: str) -> Optional[int]:
    """Campo vazio = sem limite. Devolve centavos."""
    if not texto.strip():
        return None
    valor = reais_para_centavos(texto)
    return valor if valor > 0 else None


def combinar(data: date, hora: time) -> datetime:
    return datetime.combine(data, hora)


def proximo_sabado(hoje: Optional[date] = None) -> date:
    """O próximo sábado (hoje, se hoje for sábado)."""
    hoje = hoje or date.today()
    return hoje + timedelta(days=(5 - hoje.weekday()) % 7)


def formatar_data(data: date) -> str:
    return data.strftime("%d/%m/%Y")


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
    orcamento_texto: str = ""
    nome: str = "Meu churrasco"
    usar_ia: bool = True
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
                              duracao_horas: Optional[float],
                              orcamento_centavos: Optional[int]) -> list[str]:
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
            mudou.append(f"{self.duracao_horas} horas")
        if orcamento_centavos:
            self.orcamento_texto = f"{orcamento_centavos / 100:.2f}".replace(".", ",")
            mudou.append(f"orçamento {formatar_reais(orcamento_centavos)}")
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
