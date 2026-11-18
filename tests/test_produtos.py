from churrasco_facil.produtos import ItemPlano, Produto

CARNE = Produto("carne", "Carne", "Açougue", "g", 9000, 1000)     # R$ 90,00 o kg
PAO = Produto("pao", "Pão", "Padaria", "un", 400, 1)              # R$ 4,00 a unidade


def test_custo_do_item_vendido_por_peso():
    assert ItemPlano(CARNE, 250).custo == 2250


def test_custo_do_item_vendido_por_unidade():
    assert ItemPlano(PAO, 3).custo == 1200


def test_com_preco_troca_o_preco_configurado():
    assert CARNE.com_preco({"carne": 1}).preco == 1


def test_com_preco_ignora_precos_de_outros_produtos():
    assert CARNE.com_preco({"pao": 1}) is CARNE


def test_com_preco_sem_precos_devolve_o_mesmo_produto():
    assert CARNE.com_preco(None) is CARNE
