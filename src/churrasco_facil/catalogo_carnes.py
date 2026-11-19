"""Catálogo de cortes para quem está começando.

Os preços são estimativas de referência (centavos por kg) e podem ser trocados pelo
usuário nas configurações. Tempos e temperaturas são pontos de partida, não regras
absolutas: o tamanho do corte e o calor da brasa mudam tudo.

Carne de churrasco não se compra em gramas: se compra a peça, o pacote ou a bandeja. Cada
corte diz como é vendido e quanto pesa cada unidade (um peso médio, fixo). O preço continua
por kg, como no açougue.

Cada dica aparece num lugar só, na hora em que serve:
- na aba Carnes (ao escolher): o que combina com o corte e como escolher na hora de comprar;
- na aba Compras (no cartão do açougue): como pedir ao açougueiro;
- na aba Horários (na hora de grelhar): o ponto e como preparar.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .produtos import ACOUGUE, Produto

BOVINA, SUINA, FRANGO, LINGUICA = "bovina", "suina", "frango", "linguica"
VEGETARIANO = "vegetariano"


@dataclass(frozen=True)
class Corte(Produto):
    """Um corte (ou item vegetariano) que vai para a grelha."""

    categoria: str = BOVINA
    tempo_minutos: int = 20         # tempo total na grelha
    descanso_minutos: int = 5       # descanso depois de sair da grelha
    ponto: str = ""                 # como saber que está pronto (Horários)
    preparo: str = ""               # como preparar na grelha (Horários)
    peca_g: int = 1000              # quanto pesa cada unidade que se compra (em gramas)
    embalagem: str = "peça"         # como se compra: peça, pacote, bandeja, bife...
    combina_com: str = ""           # o que vai bem junto (Carnes)
    como_escolher: str = ""         # o que olhar na hora de comprar (Carnes)
    como_pedir: str = ""            # o que pedir ao açougueiro (Compras, no açougue)

    def __post_init__(self) -> None:
        if self.peca_g < 1:
            raise ValueError(f"{self.id}: o peso da peça precisa ser positivo")


# Como cada corte é vendido: (gramas de cada unidade, nome da unidade). Pesos médios do
# mercado: uma picanha inteira tem perto de 1,2 kg; linguiça vem em pacote de 1 kg.
COMO_SE_COMPRA: dict[str, tuple[int, str]] = {
    "picanha": (1200, "peça"),
    "maminha": (1000, "peça"),
    "fraldinha": (1000, "peça"),
    "vazio": (2000, "peça"),                  # peça grande, do churrasco gaúcho
    "alcatra": (1000, "peça"),
    "contrafile": (400, "bife"),              # bife grosso, próprio para churrasco
    "costela_bovina": (2000, "peça"),
    "linguica_toscana": (1000, "pacote"),
    "linguica_frango": (500, "pacote"),
    "coxa_sobrecoxa": (1000, "bandeja"),
    "asa_frango": (1000, "bandeja"),
    "coracao_frango": (500, "bandeja"),
    "costelinha_suina": (1200, "peça"),
    "bisteca_suina": (1000, "bandeja"),
    "lombo_suino": (1000, "peça"),
    "queijo_coalho": (400, "pacote"),         # pacote com uns 7 espetos
    "espetinho_legumes": (100, "espetinho"),
    "cogumelo": (200, "bandeja"),
}

# O que vai bem junto: aparece na aba Carnes, ao escolher.
COMBINA_COM: dict[str, str] = {
    "picanha": "Farofa, pão de alho e vinagrete.",
    "maminha": "Farofa e vinagrete. Vai bem com molho de alho ou chimichurri.",
    "fraldinha": "Pão de alho e farofa. Fica ótima com chimichurri.",
    "vazio": "Chimichurri e pão de alho, como no churrasco gaúcho. Farofa também.",
    "alcatra": "Farofa, vinagrete e pão de alho: agrada todo mundo.",
    "contrafile": "Farofa e pão de alho. Vai bem com vinagrete.",
    "costela_bovina": "Farofa e vinagrete: sozinha já é o prato principal.",
    "linguica_toscana": "Pão francês (o clássico pão com linguiça) e farofa.",
    "linguica_frango": "Pão e vinagrete. As crianças costumam gostar.",
    "coxa_sobrecoxa": "Farofa e vinagrete, com limão para espremer na hora.",
    "asa_frango": "Limão e molho de pimenta: é petisco.",
    "coracao_frango": "Farofa e limão, de petisco antes da carne.",
    "costelinha_suina": "Molho barbecue, farofa e vinagrete.",
    "bisteca_suina": "Farofa, vinagrete e limão.",
    "lombo_suino": "Farofa e vinagrete. Vai bem com molho de mostarda.",
    "queijo_coalho": "Orégano ou melaço por cima: é o petisco que abre o churrasco.",
    "espetinho_legumes": "Um fio de azeite e sal na hora de servir. Vai bem com queijo coalho.",
    "cogumelo": "Azeite, alho e sal. Vai bem junto com o queijo coalho.",
}

# Como escolher na hora de comprar: aparece na aba Carnes, ao escolher.
COMO_ESCOLHER: dict[str, str] = {
    "picanha": "Peça de até 1,2 kg, com capa de gordura branca de uns 2 dedos. Mais pesada "
               "que isso costuma vir com parte da alcatra, que é mais dura.",
    "maminha": "Peça de cerca de 1 kg, vermelho-vivo, com uma camada fina de gordura de um "
               "lado.",
    "fraldinha": "Peça achatada, de cerca de 1 kg, com as fibras longas bem à vista e um "
                 "pouco de gordura entremeada.",
    "vazio": "Peça grande e achatada, de uns 2 kg, com capa de gordura e uma pele fina de um "
             "lado. Em alguns lugares a fraldinha também é chamada de vazio: confira o peso.",
    "alcatra": "Peça de cerca de 1 kg, vermelho-vivo e com pouca gordura. O miolo da alcatra "
               "é a parte mais macia.",
    "contrafile": "Bife alto, de uns 3 dedos, com a faixa de gordura branca na borda e um "
                  "pouco de gordura entremeada.",
    "costela_bovina": "Só vale se for acender a churrasqueira bem cedo: leva umas 4 horas. "
                      "Escolha a peça com bastante carne entre os ossos.",
    "linguica_toscana": "Pacote de 1 kg bem gelado, gomos firmes e rosados, sem líquido "
                        "acumulado. Confira a validade.",
    "linguica_frango": "Pacote de 500 g bem gelado, sem líquido acumulado. Confira a "
                       "validade.",
    "coxa_sobrecoxa": "Bandeja de 1 kg bem gelada, pele clara e carne rosada, sem cheiro "
                      "forte.",
    "asa_frango": "Bandeja de 1 kg bem gelada, pele clara e sem cheiro forte.",
    "coracao_frango": "Bandeja de 500 g bem gelada, corações firmes e vermelho-escuros, sem "
                      "cheiro forte.",
    "costelinha_suina": "Peça de uns 1,2 kg, com bastante carne sobre os ossos.",
    "bisteca_suina": "Bandeja de 1 kg, bistecas de uns 2 dedos de altura, carne rosada e "
                     "gordura branca.",
    "lombo_suino": "Peça de cerca de 1 kg, carne rosada e firme, com uma camada fina de "
                   "gordura.",
    "queijo_coalho": "Pacote já no espeto (uns 7 espetos), queijo firme e sem líquido no "
                     "pacote.",
    "espetinho_legumes": "Espetinho pronto, com legumes firmes e de cor viva.",
    "cogumelo": "Bandeja de 200 g, cogumelos firmes e branquinhos, sem manchas escuras.",
}

# O que pedir ao açougueiro: aparece na aba Compras, no cartão do açougue (os vegetarianos
# não passam pelo açougue).
COMO_PEDIR: dict[str, str] = {
    "picanha": "Leve inteira, com a capa de gordura, e peça para não limpar a gordura.",
    "maminha": "Leve inteira, com a gordura: fica mais suculenta que em bifes.",
    "fraldinha": "Leve inteira e peça para tirar só a pele grossa, deixando a gordura.",
    "vazio": "Peça o vazio inteiro, com a gordura e a pele: elas protegem a carne na grelha.",
    "alcatra": "Peça o miolo da alcatra inteiro, ou em bifes de 3 dedos para o espeto.",
    "contrafile": "Peça bifes de 3 dedos de altura, com a gordura da borda. Bife fino "
                  "resseca.",
    "costela_bovina": "Uns 2 kg, com a gordura. Se não couber na grelha, peça para serrar "
                      "ao meio.",
    "linguica_toscana": "Se o açougue faz a própria linguiça, peça a feita no dia.",
    "linguica_frango": "Se o açougue faz a própria linguiça, peça a feita no dia.",
    "coxa_sobrecoxa": "Peça coxa e sobrecoxa separadas: assam mais por igual.",
    "asa_frango": "Peça a asa já separada em coxinha e meio da asa: assa por igual.",
    "coracao_frango": "Peça os corações limpos (sem a gordura de cima) e, se tiver, já no "
                      "espeto.",
    "costelinha_suina": "Peça a costelinha em peça inteira, sem cortar entre os ossos, e para "
                        "tirar a pele fina de trás.",
    "bisteca_suina": "Peça bistecas grossas, de 2 dedos: as finas ressecam na grelha.",
    "lombo_suino": "Peça para cortar o lombo em medalhões de 3 dedos: poupa trabalho em casa.",
}

# Dica geral do cartão do açougue, na aba Compras.
DICA_DO_ACOUGUE = ("Peça cada carne embalada à parte e o frango num saco separado. Leve uma "
                   "bolsa térmica e volte direto para a geladeira.")


def _c(id: str, nome: str, preco_kg: int, categoria: str, tempo: int, descanso: int,
       ponto: str, preparo: str, secao: str = ACOUGUE) -> Corte:
    peca_g, embalagem = COMO_SE_COMPRA[id]   # todo corte precisa dizer como é vendido,
    return Corte(id=id, nome=nome, secao=secao, unidade="g", preco=preco_kg,
                 por_quantidade=1000, categoria=categoria, tempo_minutos=tempo,
                 descanso_minutos=descanso, ponto=ponto, preparo=preparo,
                 peca_g=peca_g, embalagem=embalagem,
                 combina_com=COMBINA_COM[id],          # o que combina,
                 como_escolher=COMO_ESCOLHER[id],      # como escolher
                 como_pedir=COMO_PEDIR.get(id, ""))    # e (no açougue) como pedir


CORTES: dict[str, Corte] = {c.id: c for c in (
    _c("picanha", "Picanha", 9000, BOVINA, 25, 8,
       "Ao ponto quando a gordura está dourada e o centro firme com um pouco de maciez.",
       "Capa de gordura para baixo no início e só sal grosso. Se a gordura pingar e levantar "
       "chama, afaste a peça um instante. Fatie contra a fibra."),
    _c("maminha", "Maminha", 5500, BOVINA, 40, 10,
       "Pronta quando está firme ao toque e sai um caldo claro rosado.",
       "Peça grossa: fogo médio e paciência, senão queima por fora e fica crua no meio. "
       "Vire poucas vezes."),
    _c("fraldinha", "Fraldinha", 4800, BOVINA, 25, 8,
       "Tem fibras longas: tire quando estiver macia ao apertar.",
       "Corte sempre contra a fibra depois de descansar, senão fica dura."),
    _c("vazio", "Vazio", 4200, BOVINA, 50, 10,
       "Pronto quando a gordura está dourada e a carne cede um pouco ao apertar.",
       "Comece com o lado da pele para baixo, em fogo médio, e vire uma vez só. Fatie contra "
       "a fibra."),
    _c("alcatra", "Alcatra", 5000, BOVINA, 30, 8,
       "Firme ao toque e suculenta no corte.",
       "Uma das mais fáceis de acertar. Tem pouca gordura: não passe do ponto, senão "
       "resseca."),
    _c("contrafile", "Contrafilé", 5500, BOVINA, 25, 8,
       "Sai da grelha quando a gordura da borda está dourada.",
       "Faça cortes na gordura da borda para o bife não enrolar. Sirva em tiras."),
    _c("costela_bovina", "Costela bovina", 3800, BOVINA, 240, 15,
       "Só fica boa depois de horas em fogo baixo: a carne solta do osso.",
       "Fogo baixo, longe da brasa, com o osso para baixo. Vire poucas vezes."),
    _c("linguica_toscana", "Linguiça toscana", 2500, LINGUICA, 30, 3,
       "Dourada por fora e sem parte rosada ao abrir uma.",
       "Fogo baixo e não fure: perde o caldo e a gordura pinga na brasa. Vire de lado a cada "
       "5 minutos."),
    _c("linguica_frango", "Linguiça de frango", 2300, LINGUICA, 30, 3,
       "Sem parte rosada ao abrir uma.",
       "Mais leve que a toscana. Fogo baixo: é frango, tem que passar bem."),
    _c("coxa_sobrecoxa", "Coxa e sobrecoxa de frango", 1400, FRANGO, 45, 3,
       "Caldo claro ao espetar perto do osso e carne sem parte rosada.",
       "Um pouco de limão no tempero. Comece longe do fogo forte e termine perto para dourar "
       "a pele. Tábua e faca separadas da carne crua."),
    _c("asa_frango", "Asinha de frango", 1800, FRANGO, 35, 3,
       "Dourada e crocante, sem rosa junto ao osso.",
       "Peça pequena: cuidado para não queimar por fora."),
    _c("coracao_frango", "Coração de frango", 3000, FRANGO, 20, 2,
       "Firme e dourado por todos os lados.",
       "Marine rápido com sal e limão e monte os espetos. Lave as mãos depois de montar."),
    _c("costelinha_suina", "Costelinha suína", 2800, SUINA, 120, 8,
       "A carne recua do osso e fica macia.",
       "Demora. Embrulhe em papel-alumínio no meio do tempo para ficar macia."),
    _c("bisteca_suina", "Bisteca suína", 2200, SUINA, 25, 3,
       "Sem parte rosada ao cortar junto ao osso.",
       "Carne de porco precisa ficar bem passada, mas não seca: fogo médio."),
    _c("lombo_suino", "Lombo suíno", 2600, SUINA, 40, 5,
       "Firme e levemente rosado só no centro, sem líquido vermelho.",
       "Em medalhões grossos não resseca. Sirva em fatias finas."),
    _c("queijo_coalho", "Queijo coalho no espeto", 4200, VEGETARIANO, 10, 0,
       "Dourado dos dois lados e macio por dentro.",
       "Derrete e pinga: coloque perto do fim, longe do fogo forte.",
       "Frios e laticínios"),
    _c("espetinho_legumes", "Espetinho de legumes", 1800, VEGETARIANO, 15, 0,
       "Macios e com marcas douradas.",
       "Grelhe longe da carne crua (ou no papel-alumínio), para não pegar a gordura da carne.",
       "Hortifruti"),
    _c("cogumelo", "Cogumelo-de-paris", 5000, VEGETARIANO, 12, 0,
       "Dourados e murchos.",
       "Pincele com azeite e coloque com a abertura para cima. Use espeto ou papel-alumínio: "
       "pedaço pequeno cai na brasa.", "Hortifruti"),
)}

# Misturas prontas: id do corte -> importância relativa. Servem de ponto de partida.
# Como a carne é comprada em peças inteiras, um grupo pequeno leva só as primeiras: por isso
# o corte que dá a cara da mistura tem o maior peso (picanha no Caprichado e no Tradicional).
MISTURAS: dict[str, dict[str, int]] = {
    "premium": {"picanha": 35, "fraldinha": 15, "contrafile": 15, "linguica_toscana": 15,
                "coxa_sobrecoxa": 10, "costelinha_suina": 10},
    "tradicional": {"picanha": 30, "linguica_toscana": 25, "coxa_sobrecoxa": 20,
                    "maminha": 15, "alcatra": 10},
    "economica": {"linguica_toscana": 30, "coxa_sobrecoxa": 30, "bisteca_suina": 20,
                  "alcatra": 20},
}
# O que é porco (inclusive a linguiça toscana): no dia, vai primeiro para a grelha.
CORTES_DE_PORCO = ("linguica_toscana", "costelinha_suina", "bisteca_suina", "lombo_suino")
MISTURA_VEGETARIANA = {"queijo_coalho": 40, "espetinho_legumes": 35, "cogumelo": 25}


def obter_corte(id: str) -> Corte:
    try:
        return CORTES[id]
    except KeyError:
        raise KeyError(f"corte desconhecido: {id!r}") from None


def cortes_de_carne() -> list[Corte]:
    """Cortes de carne (exclui os vegetarianos)."""
    return [c for c in CORTES.values() if c.categoria != VEGETARIANO]


def pesos_validos(ids_e_pesos: Mapping[str, int]) -> dict[str, int]:
    """Mantém só ids que existem no catálogo e pesos positivos."""
    return {i: p for i, p in ids_e_pesos.items() if i in CORTES and p > 0}
