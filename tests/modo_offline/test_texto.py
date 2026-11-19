"""Texto digitado de qualquer jeito, pronto para comparar."""
from churrasco_facil.modo_offline.texto import normalizar


def test_normalizar_tira_acento_e_maiuscula():
    assert normalizar("Crianças, AÇÃO!") == "criancas, acao!"
