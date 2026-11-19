import pytest

from churrasco_facil.catalogo_carnes import CORTES
from churrasco_facil.catalogo_itens import ITENS, obter_item
from churrasco_facil.produtos import SECOES


def test_todo_item_fica_numa_secao_conhecida():
    # item de seção desconhecida entraria na conta sem campo de preço para conferir
    assert {i.secao for i in ITENS.values()} <= set(SECOES)


def test_ids_dos_itens_nao_colidem_com_os_dos_cortes():
    # os preços personalizados são guardados por id, num dicionário só
    assert not set(CORTES) & set(ITENS)


def test_obter_item_desconhecido_levanta_keyerror():
    with pytest.raises(KeyError):
        obter_item("zebra")
