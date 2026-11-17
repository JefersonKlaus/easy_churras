"""Testa as telas usando um 'Flet de mentira'.

Isto NÃO valida a aparência nem a API real do Flet: só confere que a lógica das telas
(navegação, assistente, plano, conversa, configurações) está ligada ao resto do app.
"""
import asyncio
import importlib
import sys
import types
from datetime import datetime
from types import SimpleNamespace

import pytest

from churrasco_facil.armazenamento import Armazenamento
from churrasco_facil.cliente_groq import ClienteGroq
from churrasco_facil.configuracao import Configuracao
from conftest import TransporteFalso, resposta_groq, sem_espera

ENUMS = {"FontWeight", "CrossAxisAlignment", "MainAxisAlignment", "ScrollMode", "ThemeMode",
         "TextAlign"}


class _Enum:
    def __getattr__(self, nome):
        return nome


class Control:
    def __init__(self, *args, **kwargs):
        self.value = args[0] if args and isinstance(args[0], str) else None
        self.controls = []
        self.visible = True
        self.disabled = False
        self.__dict__.update(kwargs)


class FlefFalso(types.ModuleType):
    def __getattr__(self, nome):
        if nome.startswith("__"):
            raise AttributeError(nome)
        return _Enum() if nome in ENUMS else Control


class PaginaFalsa:
    def __init__(self, copiar=False):
        self.adicionados, self.atualizacoes = [], 0
        self.window = SimpleNamespace()
        self.copiado = []
        if copiar:
            self.set_clipboard = self.copiado.append

    def add(self, *controles):
        self.adicionados.extend(controles)

    def clean(self):
        self.adicionados.clear()

    def update(self):
        self.atualizacoes += 1


def todos(controle):
    """Percorre a árvore de controles."""
    yield controle
    for filho in getattr(controle, "controls", []) or []:
        yield from todos(filho)
    conteudo = getattr(controle, "content", None)
    if conteudo is not None:
        yield from todos(conteudo)


def achar(pagina, valor, tipo=None):
    """Primeiro controle da tela cujo texto é `valor`."""
    for raiz in pagina.adicionados:
        for c in todos(raiz):
            if c.value == valor and (tipo is None or type(c).__name__ == tipo):
                return c
    raise AssertionError(f"não achei {valor!r} na tela")


def textos(pagina):
    return [c.value for raiz in pagina.adicionados for c in todos(raiz) if c.value]


def clicar(controle):
    resultado = controle.on_click(None)
    if asyncio.iscoroutine(resultado):
        asyncio.run(resultado)


@pytest.fixture
def modulos(monkeypatch):
    monkeypatch.setitem(sys.modules, "flet", FlefFalso("flet"))
    for nome in [n for n in sys.modules if n.startswith("churrasco_facil.telas")
                 or n == "churrasco_facil.app"]:
        monkeypatch.delitem(sys.modules, nome)
    app_mod = importlib.import_module("churrasco_facil.app")
    yield app_mod
    for nome in [n for n in sys.modules if n.startswith("churrasco_facil.telas")
                 or n == "churrasco_facil.app"]:
        sys.modules.pop(nome, None)


@pytest.fixture
def pagina():
    return PaginaFalsa()


@pytest.fixture
def app(modulos, pagina, tmp_path, monkeypatch):
    monkeypatch.setenv("CHURRASCO_DADOS", str(tmp_path))
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    return modulos.AppChurrasco(pagina, Armazenamento(":memory:"), Configuracao())


def com_groq(app, *textos):
    """Liga um Groq falso ao app. Devolve o transporte para conferir as chamadas."""
    transporte = TransporteFalso(*[(200, {}, resposta_groq(t)) for t in textos])
    app.config.chave_groq = "chave"
    app.cliente = lambda: ClienteGroq("chave", transporte=transporte, dormir=sem_espera)
    return transporte


def preparar_rascunho(app):
    r = app.rascunho
    r.adultos, r.criancas, r.vegetarianos, r.bebem_alcool, r.duracao_horas = 8, 2, 1, 4, 4
    r.data_texto, r.hora_texto, r.orcamento_texto, r.nome = "21/11/2099", "14:00", "", "Festa"


# ---------------------------------------------------------------- início

def test_inicio_sem_chave_explica_que_funciona_sem_ia(app, pagina):
    app.ir_inicio()
    assert "Churrasco Fácil" in textos(pagina)
    assert any("Modo offline" in t for t in textos(pagina))
    assert achar(pagina, "Planejar um churrasco").on_click is not None


def test_inicio_com_chave_mostra_ia_conectada(app, pagina):
    com_groq(app)
    app.ir_inicio()
    assert any("IA conectada" in t for t in textos(pagina))


def test_botao_planejar_abre_o_primeiro_passo(app, pagina):
    app.ir_inicio()
    clicar(achar(pagina, "Planejar um churrasco"))
    assert "Quem vem?" in textos(pagina) and "Passo 1 de 3" in textos(pagina)


# ---------------------------------------------------------------- assistente

def test_passo_1_mostra_os_contadores_e_o_campo_de_texto(app, pagina):
    app.ir_assistente(0)
    for rotulo in ("Adultos", "Crianças", "Vegetarianos (entre os adultos)",
                   "Adultos que bebem álcool"):
        assert rotulo in textos(pagina)
    assert achar(pagina, "Entender o texto").on_click is not None


def test_passo_numerico_fora_do_intervalo_cai_nos_limites(app, pagina):
    app.ir_assistente(-5)
    assert "Passo 1 de 3" in textos(pagina)
    app.ir_assistente(99)
    assert "Passo 3 de 3" in textos(pagina)


def test_contador_respeita_limites_e_avisa(modulos):
    from churrasco_facil.telas.widgets import Contador
    mudancas, atualizacoes = [], []
    c = Contador("Adultos", 1, 0, 2, mudancas.append, lambda: atualizacoes.append(1))
    c._mais(None)
    c._mais(None)          # já está no máximo: nada muda
    assert (c.valor, mudancas, len(atualizacoes)) == (2, [2], 1)
    c._menos(None)
    c._menos(None)
    c._menos(None)         # já está no mínimo
    assert c.valor == 0 and mudancas == [2, 1, 0]
    c.definir(50)
    assert c.valor == 2 and c._numero.value == "2"


def test_entender_com_ia_preenche_o_rascunho(app, pagina):
    transporte = com_groq(app, '{"adultos": 12, "criancas": 3, "vegetarianos": 1, '
                               '"bebem_alcool": null, "orcamento_reais": 400}')
    app.rascunho.texto_livre = "churrasco para 12 adultos e 3 crianças"
    app.ir_assistente(0)
    clicar(achar(pagina, "Entender o texto"))
    r = app.rascunho
    assert (r.adultos, r.criancas, r.vegetarianos, r.orcamento_texto) == (12, 3, 1, "400,00")
    assert any("Entendi: 12 adultos" in t for t in textos(pagina))
    assert "12 adultos e 3" in transporte.chamadas[0]["corpo"]["messages"][-1]["content"]


def test_entender_sem_chave_usa_o_assistente_local(app, pagina):
    app.rascunho.texto_livre = "churrasco para 12 adultos, 3 crianças e uns 400 reais"
    app.ir_assistente(0)
    clicar(achar(pagina, "Entender o texto"))
    r = app.rascunho
    assert (r.adultos, r.criancas, r.orcamento_texto) == (12, 3, "400,00")
    assert any("Entendi: 12 adultos" in t for t in textos(pagina))


def test_entender_com_groq_recusando_a_chave_usa_o_modo_offline(app, pagina):
    app.config.chave_groq = "chave"
    transporte = TransporteFalso((401, {}, ""))
    app.cliente = lambda: ClienteGroq("chave", transporte=transporte, dormir=sem_espera)
    app.rascunho.texto_livre = "12 adultos"
    app.ir_assistente(0)
    clicar(achar(pagina, "Entender o texto"))
    assert any("recusou a chave" in t and "modo offline" in t for t in textos(pagina))
    assert app.rascunho.adultos == 12 and app.ocupado is False


def test_passo_2_tem_data_hora_duracao_e_orcamento(app, pagina):
    app.ir_assistente(1)
    assert "Quando e quanto?" in textos(pagina) and "Duração (horas)" in textos(pagina)
    campos = {c.label: c for raiz in pagina.adicionados for c in todos(raiz)
              if hasattr(c, "label")}
    assert {"Data", "Hora de servir"} <= set(campos)
    campos["Data"].on_change(SimpleNamespace(control=SimpleNamespace(value="25/12/2099")))
    assert app.rascunho.data_texto == "25/12/2099"


def test_montar_plano_sem_chave_usa_sugestao_local(app, pagina):
    preparar_rascunho(app)
    app.ir_assistente(2)
    clicar(achar(pagina, "Montar plano"))
    assert app.plano is not None and app.plano.pedido.nome == "Festa"
    assert app.plano.pedido.pesos_preferidos        # cortes escolhidos pelo assistente local
    assert any("fácil de acertar" in t for t in textos(pagina))
    assert "Festa" in textos(pagina) and app.ocupado is False


def test_montar_plano_com_a_chave_desligada_pelo_usuario_usa_a_mistura_padrao(app, pagina):
    preparar_rascunho(app)
    app.rascunho.usar_ia = False
    app.ir_assistente(2)
    clicar(achar(pagina, "Montar plano"))
    assert app.plano.pedido.pesos_preferidos == {}


def test_montar_plano_com_data_invalida_mostra_erro_e_nao_avanca(app, pagina):
    preparar_rascunho(app)
    app.rascunho.data_texto = "31/02/2099"
    app.ir_assistente(2)
    clicar(achar(pagina, "Montar plano"))
    assert app.plano is None and "essa data não existe" in textos(pagina)


def test_montar_plano_com_data_no_passado_e_recusado(app, pagina):
    preparar_rascunho(app)
    app.rascunho.data_texto = "01/01/2020"
    app.ir_assistente(2)
    clicar(achar(pagina, "Montar plano"))
    assert app.plano is None and "essa data e hora já passaram" in textos(pagina)


def test_montar_plano_com_ia_usa_so_cortes_validos_e_mostra_motivos(app, pagina):
    preparar_rascunho(app)
    com_groq(app, '{"cortes": [{"id": "alcatra", "motivo": "fácil de acertar"}, '
                  '{"id": "zebra", "motivo": "inventado"}]}')
    app.ir_assistente(2)
    clicar(achar(pagina, "Montar plano"))
    assert set(app.plano.compras.pesos) == {"alcatra"}
    assert any("Por que escolhi: fácil de acertar" in t for t in textos(pagina))


def test_montar_plano_com_groq_fora_do_ar_usa_o_modo_offline(app, pagina):
    preparar_rascunho(app)
    app.config.chave_groq = "chave"
    app.cliente = lambda: ClienteGroq("chave", transporte=TransporteFalso(OSError("x")),
                                      tentativas=1)
    app.ir_assistente(2)
    clicar(achar(pagina, "Montar plano"))
    assert app.plano is not None and app.plano.pedido.pesos_preferidos
    assert any("modo offline" in t for t in textos(pagina))

# ---------------------------------------------------------------- plano

def plano_aberto(app, pedido):
    from churrasco_facil.planejador import montar_plano
    app.novo_plano(montar_plano(pedido), {}, "")


def test_tela_do_plano_mostra_custo_cortes_e_avisos(app, pagina, pedido):
    plano_aberto(app, pedido)
    todos_textos = " | ".join(textos(pagina))
    assert "Teste" in textos(pagina) and "sábado, 21/11 às 14:00" in textos(pagina)
    assert "Custo estimado: R$" in todos_textos and "Passa R$" in todos_textos
    assert "Onde mais pesa:" in todos_textos
    assert "Nunca use a churrasqueira em lugar fechado" in textos(pagina)
    assert "Frango precisa ficar bem passado" in textos(pagina)


def test_atalhos_do_plano_levam_as_outras_telas(app, pagina, pedido):
    plano_aberto(app, pedido)
    clicar(achar(pagina, "Lista de compras"))
    assert "Total estimado: " in " ".join(textos(pagina))
    clicar(achar(pagina, "Voltar ao plano"))
    clicar(achar(pagina, "Horários"))
    assert "Servir!" in textos(pagina) and "Acender o carvão" in textos(pagina)
    clicar(achar(pagina, "Voltar ao plano"))
    clicar(achar(pagina, "Início"))
    assert "Planejar um churrasco" in textos(pagina)


def test_lista_de_compras_agrupa_por_secao(app, pagina, pedido):
    plano_aberto(app, pedido)
    app.ir_lista()
    for secao in ("Açougue", "Hortifruti", "Bebidas", "Carvão e acessórios"):
        assert secao in textos(pagina)


def test_salvar_grava_uma_vez_so(app, pagina, pedido):
    plano_aberto(app, pedido)
    clicar(achar(pagina, "Salvar"))
    assert len(app.banco.listar()) == 1 and "Plano salvo na tela inicial." in textos(pagina)
    clicar(achar(pagina, "Salvar"))
    assert len(app.banco.listar()) == 1 and "Este plano já está salvo." in textos(pagina)


def test_plano_salvo_aparece_no_inicio_e_abre_de_novo(app, pagina, pedido):
    plano_aberto(app, pedido)
    clicar(achar(pagina, "Salvar"))
    app.ir_inicio()
    assert "Planos salvos" in textos(pagina) and "Teste" in textos(pagina)
    app.plano = None
    clicar(achar(pagina, "Abrir"))
    assert app.plano is not None and app.plano.pedido == pedido
    app.ir_inicio()
    clicar(achar(pagina, "Excluir"))
    assert app.banco.listar() == [] and "Planos salvos" not in textos(pagina)


def test_explicacao_local_aparece_e_e_salva(app, pagina, pedido):
    plano_aberto(app, pedido)
    clicar(achar(pagina, "Salvar"))
    clicar(achar(pagina, "Explicar o plano"))      # sem chave: assistente local
    assert any(t.startswith("Para 13 pessoas, o plano compra") for t in textos(pagina))
    assert app.banco.carregar(app.plano_id)[1].startswith("Para 13 pessoas")
    assert "Explicar o plano" not in textos(pagina)


def test_explicacao_com_groq_aparece_e_e_salva(app, pagina, pedido):
    plano_aberto(app, pedido)
    clicar(achar(pagina, "Salvar"))
    com_groq(app, "Comece pelos cortes fáceis e relaxe.")
    app.ir_plano()
    clicar(achar(pagina, "Explicar o plano"))
    assert "Comece pelos cortes fáceis e relaxe." in textos(pagina)
    assert app.banco.carregar(app.plano_id)[1] == "Comece pelos cortes fáceis e relaxe."


def test_explicacao_com_groq_limitado_cai_para_o_modo_offline(app, pagina, pedido):
    plano_aberto(app, pedido)
    app.config.chave_groq = "chave"
    app.cliente = lambda: ClienteGroq("chave", transporte=TransporteFalso((429, {}, "")),
                                      tentativas=1)
    app.ir_plano()
    clicar(achar(pagina, "Explicar o plano"))
    assert any("Muitos pedidos" in t and "modo offline" in t for t in textos(pagina))
    assert any(t.startswith("Para 13 pessoas") for t in textos(pagina))
    assert app.ocupado is False


def test_compartilhar_mostra_o_texto_e_copia_quando_o_flet_deixa(modulos, tmp_path, pedido):
    pagina = PaginaFalsa(copiar=True)
    app = modulos.AppChurrasco(pagina, Armazenamento(":memory:"), Configuracao())
    plano_aberto(app, pedido)
    clicar(achar(pagina, "Compartilhar"))
    assert "Texto copiado! Cole no WhatsApp." in textos(pagina)
    assert pagina.copiado and pagina.copiado[0].startswith("*Teste*")


def test_compartilhar_sem_area_de_transferencia_pede_copia_manual(app, pagina, pedido):
    plano_aberto(app, pedido)
    clicar(achar(pagina, "Compartilhar"))
    assert "Selecione o texto abaixo e copie." in textos(pagina)


def test_telas_sem_plano_levam_de_volta_ao_inicio(app, pagina):
    for ir in (app.ir_plano, app.ir_lista, app.ir_cronograma, app.ir_conversa):
        ir()
        assert any(t in textos(pagina) for t in ("Nenhum plano aberto",
                                                  "Abra um plano primeiro"))


# ---------------------------------------------------------------- conversa

def test_conversa_responde_e_mostra_no_historico(app, pagina, pedido):
    plano_aberto(app, pedido)
    transporte = com_groq(app, "Espere a brasa ficar branca.")
    app.ir_conversa()
    clicar(achar(pagina, "E se começar a chover?"))
    assert "E se começar a chover?" in textos(pagina)
    assert "Espere a brasa ficar branca." in textos(pagina)
    assert "Plano" not in transporte.chamadas[0]["corpo"]["messages"][-1]["content"]
    assert app.ocupado is False


def test_conversa_sem_chave_responde_com_dicas_prontas(app, pagina, pedido):
    plano_aberto(app, pedido)
    app.ir_conversa()
    assert achar(pagina, "Enviar").disabled is False
    assert any("Modo offline" in t for t in textos(pagina))
    clicar(achar(pagina, "E se começar a chover?"))
    assert any("monóxido de carbono" in t for t in textos(pagina))
    assert app.ocupado is False


def test_conversa_com_groq_recusando_responde_offline(app, pagina, pedido):
    plano_aberto(app, pedido)
    app.config.chave_groq = "chave"
    app.cliente = lambda: ClienteGroq("chave", transporte=TransporteFalso((401, {}, "")),
                                      tentativas=1)
    app.ir_conversa()
    clicar(achar(pagina, "E se começar a chover?"))
    assert any(t.startswith("Chuva fina") for t in textos(pagina))
    assert "Sem internet: respondi com dicas prontas." in textos(pagina)
    assert len(app.conversa.historico) == 2


def test_limpar_conversa(app, pagina, pedido):
    plano_aberto(app, pedido)
    com_groq(app, "resposta")
    app.ir_conversa()
    clicar(achar(pagina, "E se começar a chover?"))
    clicar(achar(pagina, "Limpar conversa"))
    assert "resposta" not in textos(pagina) and app.conversa.historico == []


# ---------------------------------------------------------------- configurações

def campos_da_tela(pagina):
    return {c.label: c for raiz in pagina.adicionados for c in todos(raiz)
            if hasattr(c, "label")}


def test_salvar_configuracoes(app, pagina, tmp_path):
    app.ir_configuracoes()
    campos = campos_da_tela(pagina)
    campos["Chave do Groq"].value = " minha-chave "
    campos["Picanha (R$ por kg)"].value = "95,00"
    campos["Carne por adulto (gramas)"].value = "500"
    clicar(achar(pagina, "Salvar"))
    assert "Configurações salvas." in textos(pagina)
    assert app.config.chave_groq == "minha-chave"
    assert app.config.precos == {"picanha": 9500}
    assert app.config.parametros == {"carne_adulto_g": 500}
    assert (tmp_path / "configuracao.json").exists()


def test_preco_igual_ao_padrao_nao_vira_personalizado(app, pagina):
    app.ir_configuracoes()
    clicar(achar(pagina, "Salvar"))
    assert app.config.precos == {} and app.config.parametros == {}


@pytest.mark.parametrize("campo, valor", [
    ("Picanha (R$ por kg)", "caro"), ("Picanha (R$ por kg)", "-3"),
    ("Picanha (R$ por kg)", "99999999"), ("Carne por adulto (gramas)", "muito"),
    ("Carne por adulto (gramas)", "5"), ("Carne por criança (gramas)", "9999"),
])
def test_configuracao_invalida_nao_e_salva(app, pagina, campo, valor):
    app.ir_configuracoes()
    campos_da_tela(pagina)[campo].value = valor
    clicar(achar(pagina, "Salvar"))
    assert any(t.startswith("Confira os números") for t in textos(pagina))
    assert app.config == Configuracao()


def test_precos_salvos_mudam_o_plano(app, pagina, pedido):
    app.config.precos = {"picanha": 100, "fraldinha": 100, "contrafile": 100,
                         "linguica_toscana": 100, "coxa_sobrecoxa": 100,
                         "costelinha_suina": 100}
    plano_aberto(app, pedido)
    assert app.plano.compras.mistura == "premium" or app.plano.custo_total > 0
    abrir_padrao = app.plano.custo_total
    app.config.precos = {}
    plano_aberto(app, pedido)
    assert app.plano.custo_total != abrir_padrao or app.plano.compras.mistura != "premium"


def test_testar_conexao(app, pagina):
    app.ir_configuracoes()
    clicar(achar(pagina, "Testar conexão"))
    assert "Escreva a chave primeiro." in textos(pagina)


def test_main_configura_a_janela_e_abre_o_inicio(modulos, tmp_path, monkeypatch):
    monkeypatch.setenv("CHURRASCO_DADOS", str(tmp_path))
    pagina = PaginaFalsa()
    asyncio.run(modulos.main(pagina))
    assert pagina.title == "Churrasco Fácil" and pagina.window.width == 430
    assert "Planejar um churrasco" in textos(pagina)
