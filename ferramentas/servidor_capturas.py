"""Abre o app de verdade no navegador, já numa tela com dados de exemplo, para as capturas das
lojas (veja ferramentas/capturar.mjs).

    FLET_WEB_NO_CDN=true python ferramentas/servidor_capturas.py      # http://127.0.0.1:8550

Cada endereço abre uma tela: /inicio, /quem, /escolha, /carnes, /compras, /horarios.
Nada é gravado no aparelho: os planos de exemplo ficam num banco em memória.
"""
from __future__ import annotations

import os
import sys
import webbrowser
from datetime import date, datetime, time, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
webbrowser.open = lambda *a, **k: True          # o navegador é o das capturas

import flet as ft  # noqa: E402

from churrasco_facil import app as modulo_app  # noqa: E402
from churrasco_facil.armazenamento import Armazenamento  # noqa: E402
from churrasco_facil.catalogo_carnes import MISTURAS  # noqa: E402
from churrasco_facil.configuracao import Configuracao  # noqa: E402
from churrasco_facil.convidados import Convidados  # noqa: E402
from churrasco_facil.entradas import formatar_data, proximo_sabado  # noqa: E402
from churrasco_facil.planejador import Pedido, montar_plano  # noqa: E402

SABADO = proximo_sabado(date.today() + timedelta(days=1))
SERVIR = datetime.combine(SABADO, time(13, 0))
GRUPO = Convidados(adultos=10, criancas=3, vegetarianos=1, bebem_alcool=7, duracao_horas=5)


async def main(page: ft.Page) -> None:
    tela = (page.route or "/").strip("/") or "inicio"
    page.title = "Churrasco Fácil"
    modulo_app.tema.aplicar(page)
    banco = Armazenamento(":memory:")
    app = modulo_app.AppChurrasco(page, banco, Configuracao())
    tradicional = Pedido(GRUPO, SERVIR, pesos_preferidos=MISTURAS["tradicional"],
                         nome="Churrasco Tradicional")
    banco.salvar(Pedido(Convidados(adultos=6, criancas=2, bebem_alcool=4),
                        SERVIR + timedelta(days=21), pesos_preferidos=MISTURAS["economica"],
                        nome="Aniversário do Pedro"))
    banco.salvar(tradicional)
    r = app.rascunho
    r.adultos, r.criancas, r.vegetarianos, r.bebem_alcool, r.duracao_horas = 10, 3, 1, 7, 5
    r.data_texto, r.hora_texto = formatar_data(SABADO), "13:00"
    passos = {"precos": 0, "quem": 1, "quando": 2, "escolha": 3}
    if tela in passos:
        app.ir_assistente(passos[tela])
    elif tela in ("carnes", "compras", "horarios"):
        app.novo_plano(montar_plano(tradicional))
        getattr(app, f"ir_{tela}")()
    else:
        app.ir_inicio()
    page.update()


ft.run(main, view=ft.AppView.WEB_BROWSER, port=int(os.environ.get("PORTA", "8550")),
       no_cdn=True)
