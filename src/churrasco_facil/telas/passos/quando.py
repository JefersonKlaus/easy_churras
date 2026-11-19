"""Passo 3: quando é (data, hora de servir) e quanto tempo dura a festa."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .. import widgets as w
from . import comum as c

if TYPE_CHECKING:
    from ...app import AppChurrasco


def montar(app: AppChurrasco) -> w.Tela:
    r = app.rascunho
    erro = w.erro("")
    duracao = w.Contador("Duração da festa (horas)", r.duracao_horas, 1, 12,
                         c.guardar(app, "duracao_horas"), app.atualizar)

    def proximo(_evento: Any) -> None:
        try:
            r.para_data_hora()
        except ValueError as problema:
            erro.value = str(problema)
            app.atualizar()
            return
        app.ir_assistente(c.ESCOLHA)

    return w.Tela([
        w.campo_texto("Data", r.data_texto, c.guardar(app, "data_texto"), "dd/mm/aaaa"),
        w.campo_texto("Hora de servir", r.hora_texto, c.guardar(app, "hora_texto"), "14:00"),
        duracao.controle,
        w.dica("Quanto tempo os convidados vão ficar. Festa mais longa pede mais carne e "
               "bebida."),
    ], topo=c.topo(app, c.QUANDO), rodape=c.rodape(app, c.QUANDO, erro, proximo))
