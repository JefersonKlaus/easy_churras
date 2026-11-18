import pytest

from churrasco_facil.catalogo_carnes import CORTES
from churrasco_facil.catalogo_itens import ITENS, obter_item
from churrasco_facil.produtos import SECOES


@pytest.mark.parametrize("item", ITENS.values(), ids=list(ITENS))
def test_item_fica_numa_secao_conhecida(item):
    assert item.secao in SECOES


def test_ids_dos_itens_nao_colidem_com_os_dos_cortes():
    # os preços personalizados são guardados por id, num dicionário só
    assert not set(CORTES) & set(ITENS)


def test_obter_item_desconhecido_levanta_keyerror():
    with pytest.raises(KeyError):
        obter_item("zebra")
