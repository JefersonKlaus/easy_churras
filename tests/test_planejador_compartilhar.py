from datetime import datetime

from churrasco_facil.calculadora import Convidados
from churrasco_facil.compartilhar import (texto_cronograma, texto_lista, texto_resumo,
                                          texto_whatsapp)
from churrasco_facil.planejador import (Pedido, descrever_data, montar_plano, resumo_pedido,
                                        resumo_plano)

SERVIR = datetime(2026, 11, 21, 14, 0)


def test_mesmo_pedido_gera_sempre_o_mesmo_plano(pedido):
    a, b = montar_plano(pedido), montar_plano(pedido)
    assert a.compras == b.compras and a.cronograma == b.cronograma and a.avisos == b.avisos


def test_plano_tem_cortes_cronograma_e_avisos(pedido):
    plano = montar_plano(pedido)
    assert plano.cortes and plano.cronograma and plano.avisos
    assert plano.custo_total == plano.compras.custo_total
    assert plano.custo_por_pessoa * pedido.convidados.pessoas >= plano.custo_total
    assert plano.explicacao is None
    assert montar_plano(pedido, explicacao="oi").explicacao == "oi"


def test_vegetarianos_entram_no_cronograma_so_quando_existem():
    sem = montar_plano(Pedido(Convidados(adultos=4), SERVIR))
    com = montar_plano(Pedido(Convidados(adultos=4, vegetarianos=1), SERVIR))
    assert not any(c.id == "queijo_coalho" for c in sem.cortes)
    assert any(c.id == "queijo_coalho" for c in com.cortes)
    assert any("Queijo coalho" in e.titulo for e in com.cronograma)


def test_cortes_preferidos_aparecem_no_plano():
    plano = montar_plano(Pedido(Convidados(adultos=4), SERVIR, None, {"alcatra": 1}))
    assert [c.id for c in plano.cortes] == ["alcatra"]


def test_descrever_data():
    assert descrever_data(SERVIR) == "sábado, 21/11 às 14:00"
    assert descrever_data(datetime(2026, 11, 22, 9, 5)) == "domingo, 22/11 às 09:05"


def test_resumo_do_pedido_so_tem_numeros(convidados):
    texto = resumo_pedido(convidados, 60000)
    assert texto == ("10 adultos; 3 crianças; 1 vegetarianos; 6 bebem álcool; duração 5 horas; "
                     "orçamento R$ 600,00")
    assert resumo_pedido(Convidados(adultos=2), None).endswith("sem orçamento")


def test_resumo_do_plano_para_a_ia(pedido):
    texto = resumo_plano(montar_plano(pedido))
    assert "Hora de servir: sábado, 21/11 às 14:00" in texto
    assert "Carnes:" in texto and "Custo estimado:" in texto
    assert "Para vegetarianos:" in texto and "Avisos de segurança" in texto


def test_textos_para_whatsapp(pedido):
    plano = montar_plano(pedido)
    resumo = texto_resumo(plano)
    assert resumo.startswith("*Teste*") and "10 adultos e 3 crianças" in resumo
    assert "Atenção: passa" in resumo        # o plano de teste estoura os R$ 600
    lista = texto_lista(plano)
    assert "*Açougue*" in lista and "- Pão de alho: 13 un" in lista
    assert "R$" not in lista                  # a lista compartilhada não leva preços
    horarios = texto_cronograma(plano)
    assert "14:00 - Servir!" in horarios and "Apagar e limpar" not in horarios
    assert texto_whatsapp(plano) == "\n\n".join([resumo, lista, horarios])


def test_resumo_sem_aviso_quando_cabe_no_orcamento(convidados):
    plano = montar_plano(Pedido(convidados, SERVIR, 10 ** 8))
    assert "Atenção" not in texto_resumo(plano)
