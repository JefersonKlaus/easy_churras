"""Aba Horários: lembretes de uma linha, da véspera ao fim da festa; o cuidado de cada hora
fica a um toque, marcado por um triângulo."""
import pytest
from tela import cartao_de, textos, tocar, todos

pytestmark = pytest.mark.usefixtures("horarios_abertos")

FECHADO = "Nunca use a churrasqueira em lugar fechado"


@pytest.fixture
def horarios_abertos(app, plano_aberto):
    app.ir_horarios()


@pytest.fixture
def servir(plano):
    return next(e for e in plano.cronograma if e.titulo == "Servir!")


@pytest.fixture
def monoxido(plano):
    return next(a for a in plano.avisos if a.titulo == FECHADO)


@pytest.mark.parametrize("etapa", ["Comprar tudo da lista", "Acender o carvão", "Servir!"])
def test_horarios_mostram_as_etapas(pagina, etapa):
    assert etapa in textos(pagina)


def test_horario_aparece_ao_lado_da_etapa(pagina):
    assert "14:00" in textos(pagina)


# ---------------------------------------------------------------- cuidados na hora certa

def triangulo(pagina, etapa):
    """O triângulo de cuidado no cartão da etapa (None se não houver)."""
    return next((c for c in todos(cartao_de(pagina, etapa))
                 if getattr(c, "tooltip", None) == "Tem um cuidado nesta hora"), None)


def test_dias_sao_a_vespera_e_o_dia_da_festa(pagina):
    assert {"Na véspera · sexta, 20/11", "No dia · sábado, 21/11"} <= set(textos(pagina))


@pytest.mark.parametrize("etapa", ["Passar a carne do congelador para a geladeira",
                                   "Colocar a cerveja na geladeira"])
def test_vespera_lembra_da_carne_e_da_cerveja(pagina, etapa):
    assert etapa in textos(pagina)


@pytest.mark.parametrize("etapa, cuidado", [
    ("Acender o carvão", FECHADO),
    ("Acender o carvão", "Não use álcool nem gasolina para acender"),
    ("Tirar a carne da geladeira", "Carne crua não fica horas fora da geladeira"),
    ("Na grelha", "Linguiça: sem parte rosada"),
    ("Servir!", "Separe o que é cru do que é pronto"),
    ("Apagar e limpar", "Depois da festa"),
])
def test_cuidado_aparece_ao_tocar_na_etapa(pagina, etapa, cuidado):
    assert cuidado not in textos(pagina)           # um lembrete de uma linha só
    tocar(pagina, etapa)
    assert cuidado in textos(cartao_de(pagina, etapa))


def test_todas_as_carnes_vao_para_a_grelha_num_cartao_so(pagina, plano):
    cartao = textos(cartao_de(pagina, "Na grelha"))
    assert all(c.nome in cartao for c in plano.cortes)
    assert sum(t == "Na grelha" for t in textos(pagina)) == 1


def test_tirar_cada_carne_e_servir_ficam_num_cartao_so(pagina, plano):
    cartao = textos(cartao_de(pagina, "Tirar e servir"))
    assert "Servir!" in cartao and "Picanha · esperar 8 min" in cartao


def test_etapa_com_cuidado_grave_tem_triangulo_vermelho(pagina):
    from churrasco_facil.telas.tema import PERIGO  # já carregado com o Flet de mentira
    assert triangulo(pagina, "Acender o carvão").color == PERIGO


def test_etapa_sem_cuidado_nao_tem_triangulo(pagina):
    assert triangulo(pagina, "Preparar a farofa") is None


def test_texto_do_cuidado_fica_escondido_ate_tocar(pagina, monoxido):
    assert monoxido.texto not in textos(pagina)


def test_tocar_na_etapa_mostra_o_texto_do_cuidado(pagina, monoxido):
    tocar(pagina, "Acender o carvão")
    assert monoxido.texto in textos(pagina)


def test_como_preparar_cada_carne_aparece_ao_tocar_na_grelha(pagina, plano):
    # as dicas de preparo ficam aqui, na hora de grelhar (não na aba Carnes)
    def com_preparo():
        return [c for c in plano.cortes if any(c.preparo in t for t in textos(pagina))]
    assert com_preparo() == []
    tocar(pagina, "Na grelha")
    assert com_preparo() == list(plano.cortes)
