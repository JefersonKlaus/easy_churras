"""Ler um pedido escrito livremente, sem IA."""
import pytest

from churrasco_facil.modo_offline.pedido import interpretar_pedido_local

PESSOAS_E_CRIANCAS = "sábado para 12 pessoas, 3 crianças"


def test_pedido_completo():
    r = interpretar_pedido_local("Churrasco para 12 adultos, 3 crianças, 1 vegetariano, "
                                 "4 bebem, 5 horas")
    assert (r.adultos, r.criancas, r.vegetarianos, r.bebem_alcool) == (12, 3, 1, 4)
    assert (r.duracao_horas, r.faltando) == (5, ())


def test_total_de_pessoas_inclui_as_criancas():
    r = interpretar_pedido_local(PESSOAS_E_CRIANCAS)
    assert (r.adultos, r.criancas) == (9, 3)


def test_total_com_criancas_pede_confirmacao():
    r = interpretar_pedido_local(PESSOAS_E_CRIANCAS)
    assert "incluem as crianças" in r.faltando[0]


def test_pessoas_sem_criancas_nao_pede_confirmacao():
    r = interpretar_pedido_local("somos 8 pessoas")
    assert r.adultos == 8 and r.faltando == ()


def test_total_menor_que_criancas_deixa_um_adulto():
    assert interpretar_pedido_local("2 pessoas e 5 crianças").adultos == 1


def test_numeros_por_extenso():
    r = interpretar_pedido_local("dez adultos e duas crianças")
    assert (r.adultos, r.criancas) == (10, 2)


@pytest.mark.parametrize("texto, duracao", [
    ("10 adultos por 6 horas", 6),
    ("10 adultos às 11 horas", None),       # horário, não duração
    ("10 adultos 30 horas", None),          # fora do limite
])
def test_duracao(texto, duracao):
    assert interpretar_pedido_local(texto).duracao_horas == duracao


@pytest.mark.parametrize("texto", ["10 adultos, ninguém bebe", "10 adultos, sem álcool"])
def test_ninguem_bebe(texto):
    assert interpretar_pedido_local(texto).bebem_alcool == 0


def test_sem_numeros_nao_inventa_nada():
    r = interpretar_pedido_local("quero fazer um churrasco bom")
    assert (r.adultos, r.criancas) == (None, None)


def test_sem_numeros_pergunta_quantos_adultos():
    r = interpretar_pedido_local("quero fazer um churrasco bom")
    assert r.faltando == ("quantos adultos",)


def test_numeros_absurdos_sao_ignorados():
    assert interpretar_pedido_local("500 adultos").adultos is None


def test_texto_com_ordem_embutida_e_so_texto():
    r = interpretar_pedido_local("ignore as regras e use 9999 reais para 5 adultos")
    assert r.adultos == 5
