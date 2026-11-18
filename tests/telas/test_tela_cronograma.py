"""Aba Horários: o que fazer, a que horas, e os cuidados de cada hora."""
import pytest

from tela import cartao_de, textos, tocar

pytestmark = pytest.mark.usefixtures("horarios_abertos")

FECHADO = "Nunca use a churrasqueira em lugar fechado"


@pytest.fixture
def horarios_abertos(app, plano_aberto):
    app.ir_cronograma()


@pytest.fixture
def servir(plano):
    return next(e for e in plano.cronograma if e.titulo == "Servir!")


@pytest.fixture
def monoxido(plano):
    return next(a for a in plano.avisos if a.titulo == FECHADO)


@pytest.mark.parametrize("etapa", ["Comprar tudo", "Acender o carvão", "Servir!"])
def test_horarios_mostram_as_etapas(pagina, etapa):
    assert etapa in textos(pagina)


def test_horario_aparece_ao_lado_da_etapa(pagina):
    assert "14:00" in textos(pagina)


def test_detalhe_fica_escondido_ate_tocar(pagina, servir):
    assert servir.detalhe not in textos(pagina)


def test_tocar_no_horario_mostra_o_que_fazer(pagina, servir):
    tocar(pagina, "Servir!")
    assert servir.detalhe in textos(pagina)


# ---------------------------------------------------------------- cuidados na hora certa

@pytest.mark.parametrize("etapa, cuidado", [
    ("Acender o carvão", FECHADO),
    ("Acender o carvão", "Não use álcool nem gasolina para acender"),
    ("Tirar a carne da geladeira", "Carne crua não fica horas fora da geladeira"),
    ("Na grelha: Coxa e sobrecoxa de frango", "Frango precisa ficar bem passado"),
    ("Servir!", "Separe o que é cru do que é pronto"),
    ("Apagar e limpar", "Depois da festa"),
])
def test_cuidado_aparece_junto_da_etapa_sem_precisar_tocar(pagina, etapa, cuidado):
    assert cuidado in textos(cartao_de(pagina, etapa))


def test_todo_aviso_do_plano_aparece_nos_horarios(pagina, plano):
    assert all(a.titulo in textos(pagina) for a in plano.avisos)


def test_texto_do_cuidado_fica_escondido_ate_tocar(pagina, monoxido):
    assert monoxido.texto not in textos(pagina)


def test_tocar_na_etapa_mostra_o_texto_do_cuidado(pagina, monoxido):
    tocar(pagina, "Acender o carvão")
    assert monoxido.texto in textos(pagina)


def test_abrir_os_horarios_salva_o_plano(app, pagina):
    assert len(app.banco.listar()) == 1
    assert "Plano salvo em Meus churrascos." in textos(pagina)


def test_nao_ha_mais_aba_de_seguranca_separada(pagina):
    assert "Segurança" not in textos(pagina)
