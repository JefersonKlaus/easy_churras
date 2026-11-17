"""Catálogo de cortes para quem está começando: o Groq só pode escolher daqui.

Os preços são estimativas de referência (centavos por kg) e podem ser trocados pelo
usuário nas configurações. Tempos e temperaturas são pontos de partida, não regras
absolutas: o tamanho do corte e o calor da brasa mudam tudo.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Mapping, Optional

from .produtos import Produto

BOVINA, SUINA, FRANGO, LINGUICA, VEGETARIANO = "bovina", "suina", "frango", "linguica", "vegetariano"


@dataclass(frozen=True)
class Corte(Produto):
    """Um corte (ou item vegetariano) que vai para a grelha."""

    categoria: str = BOVINA
    dificuldade: int = 1            # 1 = fácil para iniciante, 3 = difícil
    tempo_minutos: int = 20         # tempo total na grelha
    descanso_minutos: int = 5       # descanso depois de sair da grelha
    temperatura_segura_c: int = 63  # temperatura mínima no centro (referência)
    ponto: str = ""                 # como saber que está pronto
    dica: str = ""                  # conselho para iniciante
    substitutos: tuple[str, ...] = ()
    peso_padrao: int = 10           # importância relativa quando entra numa mistura

    def com_preco(self, precos: Optional[Mapping[str, int]]) -> "Corte":
        if precos and self.id in precos:
            return replace(self, preco=precos[self.id])
        return self


def _c(id: str, nome: str, preco_kg: int, categoria: str, dificuldade: int, tempo: int,
       descanso: int, temp: int, ponto: str, dica: str, substitutos: tuple[str, ...],
       peso: int = 10, secao: str = "Açougue") -> Corte:
    return Corte(id=id, nome=nome, secao=secao, unidade="g", preco=preco_kg,
                 por_quantidade=1000, categoria=categoria, dificuldade=dificuldade,
                 tempo_minutos=tempo, descanso_minutos=descanso, temperatura_segura_c=temp,
                 ponto=ponto, dica=dica, substitutos=substitutos, peso_padrao=peso)


CORTES: dict[str, Corte] = {c.id: c for c in (
    _c("picanha", "Picanha", 9000, BOVINA, 1, 25, 8, 63,
       "Ao ponto quando a gordura está dourada e o centro firme com um pouco de maciez.",
       "Deixe a capa de gordura para baixo no início e use só sal grosso. Corte em fatias "
       "contra a fibra.", ("maminha", "alcatra"), 20),
    _c("maminha", "Maminha", 5500, BOVINA, 1, 40, 10, 63,
       "Pronta quando está firme ao toque e sai um caldo claro rosado.",
       "Peça inteira, fogo médio e paciência. Vire poucas vezes.", ("alcatra", "fraldinha"), 15),
    _c("fraldinha", "Fraldinha", 4800, BOVINA, 2, 25, 8, 63,
       "Tem fibras longas: tire quando estiver macia ao apertar.",
       "Corte sempre contra a fibra depois de descansar, senão fica dura.",
       ("alcatra", "maminha"), 10),
    _c("alcatra", "Alcatra", 5000, BOVINA, 1, 30, 8, 63,
       "Firme ao toque e suculenta no corte.", "Uma das mais fáceis de acertar para quem "
       "está começando.", ("maminha", "contrafile"), 15),
    _c("contrafile", "Contrafilé", 5500, BOVINA, 2, 25, 8, 63,
       "Sai da grelha quando a gordura da borda está dourada.",
       "Faça cortes na gordura da borda para a peça não enrolar.", ("alcatra", "maminha"), 15),
    _c("costela_bovina", "Costela bovina", 3800, BOVINA, 3, 240, 15, 63,
       "Só fica boa depois de horas em fogo baixo: a carne solta do osso.",
       "Não é para iniciante nem para churrasco rápido. Escolha só se tiver a tarde toda.",
       ("maminha", "alcatra"), 5),
    _c("linguica_toscana", "Linguiça toscana", 2500, LINGUICA, 1, 30, 3, 71,
       "Dourada por fora e sem parte rosada ao abrir uma.",
       "Fogo baixo e não fure: fura-se só para testar no fim. Vira de lado a cada 5 minutos.",
       ("linguica_frango",), 25),
    _c("linguica_frango", "Linguiça de frango", 2300, LINGUICA, 1, 30, 3, 74,
       "Sem parte rosada ao abrir uma.", "Mais leve que a toscana. Fogo baixo.",
       ("linguica_toscana",), 5),
    _c("coxa_sobrecoxa", "Coxa e sobrecoxa de frango", 1400, FRANGO, 2, 45, 3, 74,
       "Caldo claro ao espetar perto do osso e carne sem parte rosada.",
       "Comece longe do fogo forte e termine perto para dourar a pele. Frango cru nunca "
       "pode ficar rosado por dentro.", ("asa_frango", "linguica_frango"), 25),
    _c("asa_frango", "Asinha de frango", 1800, FRANGO, 2, 35, 3, 74,
       "Dourada e crocante, sem rosa junto ao osso.", "Peça pequena: cuidado para não "
       "queimar por fora.", ("coxa_sobrecoxa",), 5),
    _c("coracao_frango", "Coração de frango", 3000, FRANGO, 2, 20, 2, 74,
       "Firme e dourado por todos os lados.", "Espetinho clássico: marinar rápido com sal e "
       "limão.", ("asa_frango",), 5),
    _c("costelinha_suina", "Costelinha suína", 2800, SUINA, 3, 120, 8, 63,
       "A carne recua do osso e fica macia.", "Demora. Embrulhe em papel-alumínio no meio "
       "do tempo para ficar macia.", ("bisteca_suina",), 10),
    _c("bisteca_suina", "Bisteca suína", 2200, SUINA, 1, 25, 3, 63,
       "Sem parte rosada ao cortar junto ao osso.",
       "Carne de porco precisa ficar bem passada, mas não seca: fogo médio.",
       ("lombo_suino",), 20),
    _c("lombo_suino", "Lombo suíno", 2600, SUINA, 2, 40, 5, 63,
       "Firme e levemente rosado só no centro, sem líquido vermelho.",
       "Corte em medalhões grossos para não ressecar.", ("bisteca_suina",), 10),
    _c("queijo_coalho", "Queijo coalho no espeto", 4200, VEGETARIANO, 1, 10, 0, 0,
       "Dourado dos dois lados e macio por dentro.",
       "Cuidado: derrete e pinga. Coloque perto do fim, longe do fogo forte.", (), 40,
       "Frios e laticínios"),
    _c("espetinho_legumes", "Espetinho de legumes", 1800, VEGETARIANO, 1, 15, 0, 0,
       "Macios e com marcas douradas.", "Corte tudo em pedaços do mesmo tamanho para "
       "assarem juntos.", (), 35, "Hortifruti"),
    _c("cogumelo", "Cogumelo-de-paris", 5000, VEGETARIANO, 1, 12, 0, 0,
       "Dourados e murchos.", "Pincele com azeite e coloque com a abertura para cima.",
       (), 25, "Hortifruti"),
)}

# Misturas prontas: id do corte -> importância relativa. Servem de ponto de partida.
MISTURAS: dict[str, dict[str, int]] = {
    "premium": {"picanha": 35, "fraldinha": 15, "contrafile": 15, "linguica_toscana": 15,
                "coxa_sobrecoxa": 10, "costelinha_suina": 10},
    "tradicional": {"picanha": 20, "maminha": 15, "alcatra": 15, "linguica_toscana": 25,
                    "coxa_sobrecoxa": 25},
    "economica": {"linguica_toscana": 30, "coxa_sobrecoxa": 30, "bisteca_suina": 20,
                  "alcatra": 20},
}
ORDEM_MISTURAS = ("premium", "tradicional", "economica")
MISTURA_VEGETARIANA = {"queijo_coalho": 40, "espetinho_legumes": 35, "cogumelo": 25}


def obter_corte(id: str) -> Corte:
    try:
        return CORTES[id]
    except KeyError:
        raise KeyError(f"corte desconhecido: {id!r}") from None


def cortes_de_carne() -> list[Corte]:
    """Cortes de carne (exclui os vegetarianos)."""
    return [c for c in CORTES.values() if c.categoria != VEGETARIANO]


def cortes_para_iniciante() -> list[Corte]:
    """Os de dificuldade 1 e 2, os que o Groq deve preferir para quem está começando."""
    return [c for c in cortes_de_carne() if c.dificuldade <= 2]


def pesos_validos(ids_e_pesos: Mapping[str, int]) -> dict[str, int]:
    """Mantém só ids que existem no catálogo e pesos positivos."""
    return {i: p for i, p in ids_e_pesos.items() if i in CORTES and p > 0}


def resumo_para_prompt() -> str:
    """Catálogo em texto curto, para mostrar ao Groq quais ids ele pode escolher."""
    linhas = []
    for c in cortes_de_carne():
        linhas.append(f"- {c.id}: {c.nome} (dificuldade {c.dificuldade}/3, "
                      f"{c.tempo_minutos} min, categoria {c.categoria})")
    return "\n".join(linhas)
