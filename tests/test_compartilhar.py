import pytest

from churrasco_facil.compartilhar import (texto_cronograma, texto_lista, texto_resumo,
                                          texto_whatsapp)
from churrasco_facil.planejador import Pedido, montar_plano
from dados import SERVIR


def test_resumo_comeca_pelo_nome_em_negrito(plano):
    assert texto_resumo(plano).startswith("*Teste*")


def test_resumo_diz_quem_vem(plano):
    assert "10 adultos e 3 crianças" in texto_resumo(plano)


def test_resumo_avisa_quando_estoura_o_orcamento(convidados):
    plano = montar_plano(Pedido(convidados, SERVIR, 1000))   # R$ 10,00 não dá para nada
    assert "Atenção: passa" in texto_resumo(plano)


def test_resumo_sem_aviso_quando_cabe_no_orcamento(convidados):
    plano = montar_plano(Pedido(convidados, SERVIR, 10 ** 8))
    assert "Atenção" not in texto_resumo(plano)


def test_lista_agrupa_por_secao_em_negrito(plano):
    lista = texto_lista(plano)
    assert "*Açougue*" in lista and "- Pão de alho: 13 un" in lista


@pytest.mark.parametrize("linha", ["- Sal grosso (pacote 1 kg): 1 un",
                                   "- Copos descartáveis (pacote 50): 1 un"])
def test_lista_lembra_da_mercearia_e_dos_descartaveis(plano, linha):
    lista = texto_lista(plano)
    assert "*Não esqueça*" in lista and linha in lista.split("*Não esqueça*")[1]


def test_lista_compartilhada_nao_leva_precos(plano):
    assert "R$" not in texto_lista(plano)


def test_horarios_incluem_a_hora_de_servir(plano):
    assert "14:00 - Servir!" in texto_cronograma(plano)


def test_horarios_omitem_o_que_e_depois_da_festa(plano):
    assert "Apagar e limpar" not in texto_cronograma(plano)


def test_whatsapp_junta_resumo_lista_e_horarios(plano):
    assert texto_whatsapp(plano) == "\n\n".join(
        [texto_resumo(plano), texto_lista(plano), texto_cronograma(plano)])
