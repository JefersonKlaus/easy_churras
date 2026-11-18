"""Modo offline: explicar o plano com textos prontos, sem IA."""
from churrasco_facil.dinheiro import formatar_reais
from churrasco_facil.modo_offline import explicar_local
from dados import plano_para


def test_explicacao_comeca_pelo_tamanho_do_grupo():
    assert explicar_local(plano_para(adultos=10, criancas=3)).startswith("Para 13 pessoas")


def test_explicacao_usa_o_custo_calculado():
    plano = plano_para()
    assert formatar_reais(plano.custo_total) in explicar_local(plano)


def test_explicacao_lembra_do_termometro():
    assert "termômetro" in explicar_local(plano_para())


def test_explicacao_avisa_quando_estoura_o_orcamento():
    assert "do orçamento:" in explicar_local(plano_para(adultos=20, criancas=5, orcamento=5000))


def test_explicacao_diz_que_cabe_no_orcamento():
    assert "dentro do orçamento" in explicar_local(plano_para(adultos=3, criancas=0,
                                                              orcamento=500000))
