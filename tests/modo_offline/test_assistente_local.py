"""O assistente sem rede."""
import asyncio

import pytest

from churrasco_facil.modo_offline.assistente_local import AssistenteLocal


def test_assistente_local_exige_texto():
    with pytest.raises(ValueError):
        asyncio.run(AssistenteLocal().interpretar_pedido("  "))
