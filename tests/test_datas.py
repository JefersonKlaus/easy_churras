"""Datas e horas como aparecem na tela."""
from datetime import datetime

import pytest
from dados import SERVIR

from churrasco_facil.datas import descrever_data


@pytest.mark.parametrize("hora, texto", [
    (SERVIR, "sábado, 21/11 às 14:00"),
    (datetime(2026, 11, 22, 9, 5), "domingo, 22/11 às 09:05"),
])
def test_descrever_data(hora, texto):
    assert descrever_data(hora) == texto
