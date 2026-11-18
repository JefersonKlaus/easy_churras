from datetime import datetime

import pytest

from churrasco_facil.calculadora import Convidados
from churrasco_facil.planejador import (Pedido, descrever_data, montar_plano, resumo_pedido,
                                        resumo_plano)
from dados import SERVIR


def ids_dos_cortes(plano):
    return [c.id for c in plano.cortes]


def test_mesmo_pedido_gera_sempre_o_mesmo_plano(pedido):
    a, b = montar_plano(pedido), montar_plano(pedido)
    assert (a.compras, a.cronograma, a.avisos) == (b.compras, b.cronograma, b.avisos)


def test_plano_tem_cortes_cronograma_e_avisos(plano):
    assert plano.cortes and plano.cronograma and plano.avisos


def test_custo_total_do_plano_vem_das_compras(plano):
    assert plano.custo_total == plano.compras.custo_total


def test_custo_por_pessoa_cobre_o_total(plano):
    assert plano.custo_por_pessoa * plano.pedido.convidados.pessoas >= plano.custo_total


def test_plano_novo_nao_tem_explicacao(plano):
    assert plano.explicacao is None


def test_plano_guarda_a_explicacao_recebida(pedido):
    assert montar_plano(pedido, explicacao="oi").explicacao == "oi"


def test_lembretes_sao_a_mercearia_e_os_descartaveis(plano):
    assert {i.produto.secao for i in plano.lembretes} == {"Mercearia", "Descartáveis"}


def test_lembretes_nao_entram_no_custo(plano):
    assert plano.custo_total == sum(i.custo for i in plano.compras.itens)
    assert not {i.produto.id for i in plano.lembretes} & {i.produto.id for i in plano.compras.itens}


def test_secoes_fora_do_pedido_ficam_fora_do_plano(convidados):
    plano = montar_plano(Pedido(convidados, SERVIR, secoes_fora=("Hortifruti",)))
    assert "tomate" not in {i.produto.id for i in plano.compras.itens}


def test_cortes_preferidos_viram_os_cortes_do_plano():
    plano = montar_plano(Pedido(Convidados(adultos=4), SERVIR, None, {"alcatra": 1}))
    assert ids_dos_cortes(plano) == ["alcatra"]


def test_sem_vegetarianos_nao_ha_opcao_vegetariana():
    plano = montar_plano(Pedido(Convidados(adultos=4), SERVIR))
    assert "queijo_coalho" not in ids_dos_cortes(plano)


def test_com_vegetarianos_ha_opcao_vegetariana():
    plano = montar_plano(Pedido(Convidados(adultos=4, vegetarianos=1), SERVIR))
    assert "queijo_coalho" in ids_dos_cortes(plano)


def test_opcao_vegetariana_entra_no_cronograma():
    plano = montar_plano(Pedido(Convidados(adultos=4, vegetarianos=1), SERVIR))
    assert any("Queijo coalho" in e.titulo for e in plano.cronograma)


@pytest.mark.parametrize("hora, texto", [
    (SERVIR, "sábado, 21/11 às 14:00"), (datetime(2026, 11, 22, 9, 5), "domingo, 22/11 às 09:05"),
])
def test_descrever_data(hora, texto):
    assert descrever_data(hora) == texto


def test_resumo_do_pedido_so_tem_numeros(convidados):
    assert resumo_pedido(convidados, 60000) == (
        "10 adultos; 3 crianças; 1 vegetarianos; 6 bebem álcool; duração 5 horas; "
        "orçamento R$ 600,00")


def test_resumo_do_pedido_sem_orcamento():
    assert resumo_pedido(Convidados(adultos=2), None).endswith("sem orçamento")


@pytest.mark.parametrize("trecho", [
    "Hora de servir: sábado, 21/11 às 14:00", "Carnes:", "Para vegetarianos:",
    "Custo estimado:", "Avisos de segurança",
])
def test_resumo_do_plano_para_a_ia(plano, trecho):
    assert trecho in resumo_plano(plano)
