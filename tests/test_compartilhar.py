"""O que se compartilha é a lista de compras."""
from churrasco_facil.compartilhar import texto_compras
from churrasco_facil.dinheiro import formatar_reais


def test_comeca_pelo_churrasco_quando_e_para_quantos(plano):
    assert texto_compras(plano).startswith("*Teste*\nsábado, 21/11 às 14:00 · 13 pessoas")


def test_lista_agrupa_por_secao_em_negrito_com_as_pecas(plano):
    texto = texto_compras(plano)
    carne = plano.compras.carnes[0]
    assert "*Açougue*" in texto and f"- {carne.produto.nome}: " in texto and " · " in texto


def test_bebidas_dizem_quanto_e_indicado_por_pessoa(plano):
    assert "- Água (garrafa 1,5 L): " in texto_compras(plano)
    assert "Indicado: " in texto_compras(plano).split("*Bebidas*")[1]


def test_lembra_do_que_nao_pode_esquecer(plano):
    nao_esqueca = texto_compras(plano).split("*Não esqueça*")[1]
    assert "- Pão de alho: 13 un" in nao_esqueca
    assert "- Copos descartáveis (pacote 50)" in nao_esqueca


def test_itens_sem_preco_mas_com_o_total_estimado(plano):
    texto = texto_compras(plano)
    assert texto.count("R$") == 1
    total = formatar_reais(plano.custo_total)
    assert texto.endswith(f"Total estimado (carnes, bebidas e carvão): {total}")
