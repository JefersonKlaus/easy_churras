"""Modo offline: um assistente local que funciona sem internet e sem chave do Groq.

Ele tem a mesma "cara" do assistente com IA (`interpretar_pedido`, `sugerir_cortes`, `explicar`
e a conversa), mas usa só regras e textos prontos. Serve de reserva quando a internet cai ou
a chave não existe. Tudo que ele devolve passa pelas mesmas validações do app.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Optional

from .calculadora import MAX_PESSOAS, Convidados
from .catalogo_carnes import CORTES, MISTURAS, VEGETARIANO
from .cliente_groq import ErroGroq
from .dinheiro import formatar_reais, reais_para_centavos
from .esquemas import PedidoInterpretado, Sugestao
from .orcamento import custo_por_pessoa, maiores_gastos
from .planejador import Plano
from .cronograma import formatar_hora

MAX_PERGUNTA = 500
MAX_TURNOS = 6


def normalizar(texto: str) -> str:
    """Minúsculas e sem acento, para comparar texto digitado de qualquer jeito."""
    base = unicodedata.normalize("NFD", (texto or "").lower())
    return "".join(c for c in base if unicodedata.category(c) != "Mn")


# ---------------------------------------------------------------- ler um pedido em texto livre

NUMEROS_POR_EXTENSO = {
    "um": 1, "uma": 1, "dois": 2, "duas": 2, "tres": 3, "quatro": 4, "cinco": 5, "seis": 6,
    "sete": 7, "oito": 8, "nove": 9, "dez": 10, "onze": 11, "doze": 12, "treze": 13,
    "quatorze": 14, "quinze": 15, "vinte": 20,
}
_NUMERO = r"(\d{1,3}|" + "|".join(NUMEROS_POR_EXTENSO) + r")"


def _como_inteiro(texto: str) -> Optional[int]:
    if texto.isdigit():
        valor = int(texto)
    else:
        valor = NUMEROS_POR_EXTENSO.get(texto)
    if valor is None or not 0 <= valor <= MAX_PESSOAS:
        return None
    return valor


def _achar_inteiro(texto: str, palavras: str) -> Optional[int]:
    achado = re.search(_NUMERO + r"\s+(?:" + palavras + r")\b", texto)
    return _como_inteiro(achado.group(1)) if achado else None


def _achar_orcamento(texto: str) -> Optional[int]:
    """Procura 'R$ 400', '400 reais', '1 mil reais' ou 'orçamento de 400'. Devolve centavos."""
    padroes = (
        r"r\$\s*(\d[\d.,]*)(\s*mil)?",
        r"(\d[\d.,]*)(\s*mil)?\s*(?:reais|conto|contos|pila|pilas)\b",
        r"(?:orcamento|verba|gastar|gasto)\s*(?:de|ate|maximo|:)?\s*(?:uns\s*)?(\d[\d.,]*)(\s*mil)?",
    )
    for padrao in padroes:
        achado = re.search(padrao, texto)
        if not achado:
            continue
        numero = achado.group(1).rstrip(".,")
        try:
            centavos = reais_para_centavos(numero)
        except ValueError:
            continue
        if achado.group(2):
            centavos *= 1000
        if 0 < centavos <= 1_000_000 * 100:
            return centavos
    return None


def _achar_duracao(texto: str) -> Optional[float]:
    """'4 horas' de duração; ignora horário como 'às 14 horas'."""
    for achado in re.finditer(r"(\d{1,2}(?:[.,]\d)?)\s*horas?\b", texto):
        antes = texto[:achado.start()].rstrip()
        if re.search(r"\b(as|a|ate|apos|depois das|por volta das)$", antes):
            continue
        horas = float(achado.group(1).replace(",", "."))
        if 1 <= horas <= 12:
            return horas
    return None


def interpretar_pedido_local(texto: str) -> PedidoInterpretado:
    """Lê "12 pessoas, 3 crianças, 1 vegetariano, uns 400 reais" sem usar IA."""
    t = normalizar(texto)
    criancas = _achar_inteiro(t, r"criancas?|crianca|pequenos|kids|filhos")
    vegetarianos = _achar_inteiro(t, r"vegetarian[oa]s?|veggies?")
    adultos = _achar_inteiro(t, r"adultos?|marmanjos?")
    total = _achar_inteiro(t, r"pessoas?|convidados?|amigos?|gente")
    bebem = _achar_inteiro(t, r"bebem|bebe|tomam|toma cerveja|bebedores?")
    if bebem is None and re.search(
            r"(ninguem bebe|sem alcool|nao bebem|ninguem toma|nao tem alcool)", t):
        bebem = 0

    faltando: list[str] = []
    observacoes = ""
    if adultos is None and total is not None:
        adultos = max(1, total - (criancas or 0))
        if criancas:
            faltando.append(f"se as {total} pessoas já incluem as crianças")
            observacoes = f"Contei as crianças dentro das {total} pessoas."
    elif adultos is None:
        faltando.append("quantos adultos")
    if adultos is not None and not 1 <= adultos <= MAX_PESSOAS:
        adultos = None
    return PedidoInterpretado(
        adultos=adultos, criancas=criancas, vegetarianos=vegetarianos, bebem_alcool=bebem,
        duracao_horas=_achar_duracao(t), orcamento_centavos=_achar_orcamento(t),
        observacoes=observacoes, faltando=tuple(faltando))


# ---------------------------------------------------------------- escolher cortes

def _faixa_de_preco(conv: Convidados, orcamento: Optional[int]) -> str:
    """premium, tradicional ou economica, olhando quanto sobra por pessoa."""
    if orcamento is None:
        return "tradicional"
    por_pessoa = orcamento / max(1.0, conv.adultos + conv.criancas / 2)
    if por_pessoa < 3500:
        return "economica"
    if por_pessoa < 6500:
        return "tradicional"
    return "premium"


def sugerir_cortes_local(conv: Convidados, orcamento: Optional[int]) -> list[Sugestao]:
    """Escolhe de 3 a 6 cortes fáceis de acertar. Cada um vem com o motivo."""
    faixa = _faixa_de_preco(conv, orcamento)
    ids = [i for i in MISTURAS[faixa] if CORTES[i].dificuldade <= 2]
    if conv.criancas and "linguica_frango" not in ids:
        ids.append("linguica_frango")
    if conv.pessoas >= 20 and "maminha" not in ids and faixa != "economica":
        ids.append("maminha")      # peça grande, rende bem e perdoa erro
    sugestoes: list[Sugestao] = []
    for id in ids[:6]:
        corte = CORTES[id]
        if corte.categoria == VEGETARIANO:
            continue
        sugestoes.append(Sugestao(id, _motivo(id, faixa, conv)))
    return sugestoes


def _motivo(id: str, faixa: str, conv: Convidados) -> str:
    corte = CORTES[id]
    if id == "linguica_frango" and conv.criancas:
        return "as crianças costumam gostar e é difícil errar"
    if corte.dificuldade == 1:
        base = "fácil de acertar para quem está começando"
    else:
        base = "dá certo com um pouco de atenção"
    if faixa == "economica" and corte.preco <= 5500:
        return base + " e cabe no orçamento"
    if faixa == "premium" and corte.preco >= 7000:
        return base + "; é o destaque do churrasco"
    return base


# ---------------------------------------------------------------- explicar o plano

def explicar_local(plano: Plano) -> str:
    """Texto curto sobre o plano, escrito só com números que o código já calculou."""
    conv = plano.pedido.convidados
    carnes = [i for i in plano.compras.itens
              if i.produto.id in CORTES and CORTES[i.produto.id].categoria != VEGETARIANO]
    gramas = sum(i.quantidade for i in carnes)
    partes = [
        f"Para {conv.pessoas} pessoas, o plano compra cerca de {gramas / 1000:.1f} kg de carne "
        f"em {len(carnes)} tipos. Ficou em {formatar_reais(plano.custo_total)}, uns "
        f"{formatar_reais(custo_por_pessoa(plano.custo_total, conv.pessoas))} por pessoa."
    ]
    if plano.compras.estourou:
        partes.append(f"Passou {formatar_reais(plano.compras.excedente)} do orçamento: "
                      "troque cortes caros por mais baratos ou reduza a bebida.")
    elif plano.pedido.orcamento:
        partes.append("Ficou dentro do orçamento.")
    gastos = maiores_gastos(plano.compras.itens, 2)
    if gastos:
        partes.append("O que mais pesa no bolso: " + " e ".join(
            g.produto.nome.lower() for g in gastos) + ".")
    macios = [CORTES[i.produto.id].nome for i in carnes if CORTES[i.produto.id].dificuldade == 1]
    if macios:
        partes.append("Para o primeiro churrasco, comece pelos cortes mais fáceis: "
                      + ", ".join(macios[:3]) + ".")
    partes.append("Siga os horários da tela Horários e use sempre o termômetro nas aves "
                  "e no porco.")
    return " ".join(partes)


# ---------------------------------------------------------------- dúvidas do dia

@dataclass(frozen=True)
class Assunto:
    """Uma dúvida comum: palavras que a identificam e a resposta pronta."""

    id: str
    palavras: tuple[str, ...]
    resposta: str


ASSUNTOS: tuple[Assunto, ...] = (
    # aves e porco primeiro: em empate, o assunto específico vence o genérico "ponto"
    Assunto("frango", ("frango", "coxa", "sobrecoxa", "ave", "aves", "galinha", "sangue"),
            "Frango e outras aves precisam ficar bem passados: 74 °C no centro e nada de "
            "carne rosada ou líquido avermelhado. Use fogo mais fraco para cozinhar por "
            "dentro sem queimar por fora e não use a mesma tábua e faca da carne crua."),
    Assunto("porco", ("porco", "suina", "suino", "costelinha", "bisteca", "lombo"),
            "Carne de porco: 63 °C no centro, com descanso de 3 minutos. Linguiça: 71 °C. "
            "Fogo médio e paciência, porque a gordura pinga e levanta chama."),
    Assunto("ponto", ("ponto", "pronta", "pronto", "cozida", "crua", "cru", "cozido", "passada", "passado"),
            "Aperte a carne com uma pinça: mole é crua, firme com leve maciez é ao ponto, dura "
            "passou. Para bovina o ideal é 63 °C no centro; para frango, 74 °C; para porco, "
            "63 °C. Na dúvida, use um termômetro de cozinha e deixe descansar 5 a 10 minutos "
            "antes de cortar."),
    Assunto("chuva", ("chuva", "chover", "chovendo", "temporal", "molhar"),
            "Chuva fina: cubra a churrasqueira com uma tenda ou toldo alto e firme. Nunca leve "
            "a churrasqueira para dentro de casa nem para garagem: a fumaça tem monóxido de "
            "carbono e pode matar. Se for forte, passe a carne para forno ou frigideira e "
            "volte à brasa quando abrir o tempo."),
    Assunto("carvao_acabando", ("carvao", "acabando", "acabou", "brasa", "fraca"),
            "Acrescente carvão aos poucos, em pilhas, e espere ficar coberto de cinza branca "
            "antes de colocar carne por cima. Nunca jogue álcool ou gasolina na brasa. Use "
            "acendedor sólido ou papel e, se for preciso, mantenha a carne coberta com papel "
            "alumínio enquanto a brasa volta."),
    Assunto("acender", ("acender", "acendo", "acendedor"),
            "Monte o carvão em pirâmide, acenda com acendedor sólido (nunca álcool) e espere "
            "uns 40 a 50 minutos, até ficar coberto de cinza clara. Só então espalhe a brasa e "
            "coloque a carne. O app mostra a hora certa na tela Horários."),
    Assunto("queimando", ("queimando", "queimou", "queimar", "preta", "fumaca", "chama",
                           "labareda", "alto", "alta", "demais"),
            "Chama alta queima por fora e deixa cru por dentro. Afaste a carne do calor, "
            "levante a grelha ou espalhe a brasa. Pingos de gordura que viram labareda: "
            "mova a carne e borrife um pouco de água na brasa, nunca na carne."),
    Assunto("dura", ("dura", "seca", "borracha", "mastigar", "macia", "macio"),
            "Carne dura costuma ser fogo alto demais, tempo demais ou corte contra o sentido "
            "errado. Descanse a carne e corte sempre contra a fibra, em fatias finas. "
            "Fraldinha e maminha pedem esse cuidado."),
    Assunto("tempero", ("tempero", "temperar", "sal", "grosso", "marinada", "alho"),
            "Para quem está começando: só sal grosso, uns 15 minutos antes de ir à grelha. "
            "Tempero demais esconde o sabor e sal muito cedo tira o caldo da carne."),
    Assunto("termometro", ("termometro", "temperatura", "graus"),
            "Espete o termômetro no centro do corte, sem encostar no osso nem na grelha. "
            "Bovina 63 °C, porco 63 °C, linguiça 71 °C e aves 74 °C. É a forma mais segura "
            "de acertar, em especial no primeiro churrasco."),
    Assunto("descanso", ("descanso", "descansar", "cortar", "fatiar", "fatia"),
            "Deixe a carne descansar de 5 a 10 minutos antes de cortar para o caldo não "
            "escorrer. Corte contra a fibra e sirva em porções pequenas, assim a carne "
            "continua quente."),
    Assunto("sobra", ("sobra", "sobrou", "guardar", "geladeira", "conservar", "restante"),
            "Guarde as sobras em até 2 horas depois de servir, em potes fechados na geladeira. "
            "Consuma em até 3 dias, ou congele. Aqueça até ficar bem quente antes de comer."),
    Assunto("descongelar", ("descongelar", "congelada", "congelado", "freezer"),
            "Descongele na geladeira, de um dia para o outro. Não deixe a carne ao sol nem "
            "na pia por horas, e nunca recongele carne que já descongelou por completo."),
    Assunto("bebida", ("bebida", "cerveja", "gelo", "gelada", "refrigerante", "agua"),
            "Calcule uma lata de cerveja por hora por quem bebe, mais água para todos, e "
            "gelo para manter as bebidas frias. Água e refrigerante também para crianças e "
            "para quem dirige."),
    Assunto("vegetariano", ("vegetariano", "vegetariana", "vegano", "legumes", "queijo",
                             "cogumelo"),
            "Asse queijo coalho, espetinhos de legumes e cogumelos em uma parte separada da "
            "grelha ou em papel alumínio para não pegar gordura de carne. Coloque primeiro, "
            "porque levam menos tempo."),
    Assunto("crianca", ("crianca", "criancas", "filho", "filhos", "pequenos", "bebes"),
            "Mantenha crianças longe da churrasqueira e do carvão quente, que continua "
            "queimando por horas. Ofereça carne bem passada, cortada em pedaços pequenos, e "
            "tenha água à mão."),
    Assunto("vizinho", ("vizinho", "vizinhos", "fumaca", "barulho", "incomodar"),
            "Avise os vizinhos com antecedência, evite acender com vento forte e deixe a "
            "churrasqueira longe de janelas. Carvão bem aceso solta menos fumaça."),
    Assunto("cinzas", ("cinza", "cinzas", "apagar", "limpar", "limpeza"),
            "Deixe as cinzas esfriarem por mais de 24 horas antes de jogar fora, ou apague "
            "com bastante água. Só depois jogue em saco de lixo. Brasas escondidas ainda "
            "queimam."),
)


def _palavras(texto: str) -> set[str]:
    return {p for p in re.findall(r"[a-z0-9]+", normalizar(texto)) if len(p) > 2}


def _pontos(pergunta: set[str], assunto: Assunto) -> int:
    """Quantas palavras da pergunta aparecem (ou começam igual) nas palavras do assunto."""
    pontos = 0
    for palavra in assunto.palavras:
        if any(p == palavra or (len(p) >= 5 and len(palavra) >= 5 and p[:5] == palavra[:5])
               for p in pergunta):
            pontos += 1
    return pontos


def achar_assunto(pergunta: str) -> Optional[Assunto]:
    """O assunto mais parecido com a pergunta, ou None se nenhum combinar."""
    palavras = _palavras(pergunta)
    melhor: Optional[Assunto] = None
    melhor_pontos = 0
    for assunto in ASSUNTOS:
        pontos = _pontos(palavras, assunto)
        if pontos > melhor_pontos:
            melhor, melhor_pontos = assunto, pontos
    return melhor


def resposta_do_plano(pergunta: str, plano: Plano) -> Optional[str]:
    """Perguntas sobre o próprio plano: custo, horários e quantidades."""
    t = normalizar(pergunta)
    conv = plano.pedido.convidados
    if re.search(r"\b(cust\w*|preco|gasto|gastar|dinheiro|total)\b", t):
        return (f"O plano custa {formatar_reais(plano.custo_total)}, cerca de "
                f"{formatar_reais(custo_por_pessoa(plano.custo_total, conv.pessoas))} por "
                "pessoa.")
    if re.search(r"\b(hora|horas|horario|horarios|quando|cedo)\b", t) and re.search(
            r"(acend|carvao|fogo|colocar|servir|comec|chegar)", t):
        etapas = [e for e in plano.cronograma if e.tipo in ("fogo", "servir")]
        if etapas:
            return " ".join(f"{formatar_hora(e.hora)}: {e.titulo}." for e in etapas[:3])
    if re.search(r"\b(quanto|quantos|quantidade|kg|quilos?)\b", t) and "carne" in t:
        gramas = sum(i.quantidade for i in plano.compras.itens
                     if i.produto.id in CORTES and CORTES[i.produto.id].categoria != VEGETARIANO)
        return f"O plano compra cerca de {gramas / 1000:.1f} kg de carne no total."
    return None


MENSAGEM_NAO_ENTENDI = (
    "Não achei uma dica pronta para essa pergunta, e sem internet não consigo pensar em "
    "algo novo. Tente falar de: ponto da carne, chuva, carvão, fogo alto, frango, porco, "
    "tempero, sobras, bebidas ou crianças. Ou veja o custo e os horários nas telas do plano."
)


class ConversaLocal:
    """Responde dúvidas de churrasco com dicas prontas, sem internet."""

    offline = True

    def __init__(self, plano: Optional[Plano] = None) -> None:
        self.plano = plano
        self.historico: list[dict[str, str]] = []

    async def perguntar(self, pergunta: str) -> str:
        pergunta = pergunta.strip()[:MAX_PERGUNTA]
        if not pergunta:
            raise ValueError("escreva a sua dúvida")
        resposta = self.plano and resposta_do_plano(pergunta, self.plano)
        if not resposta:
            assunto = achar_assunto(pergunta)
            resposta = assunto.resposta if assunto else MENSAGEM_NAO_ENTENDI
        self.historico.append({"role": "user", "content": pergunta})
        self.historico.append({"role": "assistant", "content": resposta})
        del self.historico[:-2 * MAX_TURNOS]
        return resposta

    def limpar(self) -> None:
        self.historico.clear()


# ---------------------------------------------------------------- mesma interface do Assistente

class AssistenteLocal:
    """Tem os mesmos métodos de `Assistente`, sem rede."""

    offline = True
    aviso = ""

    async def interpretar_pedido(self, texto: str) -> PedidoInterpretado:
        if not texto.strip():
            raise ValueError("escreva alguma coisa para eu entender")
        return interpretar_pedido_local(texto)

    async def sugerir_cortes(self, conv: Convidados, orcamento: Optional[int]) -> list[Sugestao]:
        return sugerir_cortes_local(conv, orcamento)

    async def explicar(self, plano: Plano) -> str:
        return explicar_local(plano)


class AssistenteComReserva:
    """Tenta o Groq; se a internet ou a chave falharem, usa o assistente local.

    Depois de cada chamada, `aviso` diz se foi preciso usar a reserva.
    """

    def __init__(self, principal, reserva: Optional[AssistenteLocal] = None) -> None:
        self.principal = principal
        self.reserva = reserva or AssistenteLocal()
        self.aviso = ""
        self.offline = False

    async def _com_reserva(self, nome: str, *args):
        self.aviso, self.offline = "", False
        try:
            return await getattr(self.principal, nome)(*args)
        except ErroGroq as erro:
            self.aviso = f"{erro.mensagem_usuario} Usei o modo offline."
            self.offline = True
            return await getattr(self.reserva, nome)(*args)

    async def interpretar_pedido(self, texto: str) -> PedidoInterpretado:
        return await self._com_reserva("interpretar_pedido", texto)

    async def sugerir_cortes(self, conv: Convidados, orcamento: Optional[int]) -> list[Sugestao]:
        return await self._com_reserva("sugerir_cortes", conv, orcamento)

    async def explicar(self, plano: Plano) -> str:
        return await self._com_reserva("explicar", plano)
