"""Um "Flet de mentira" para testar as telas sem a biblioteca de verdade.

Isto NÃO valida a aparência nem a API real do Flet: qualquer `ft.Algo(...)` vira um
`Controle` que guarda os argumentos, o bastante para conferir a lógica das telas.
"""
import types
from types import SimpleNamespace

ENUMS = {"FontWeight", "CrossAxisAlignment", "MainAxisAlignment", "ScrollMode", "ThemeMode",
         "TextAlign", "Icons", "DeviceOrientation"}


class _Enum:
    def __getattr__(self, nome):
        return nome


class _MetaControle(type):
    """Permite `ft.Border.all(...)`, `ft.Padding.symmetric(...)`: devolvem um Controle."""

    def __getattr__(cls, nome):
        if nome.startswith("__"):
            raise AttributeError(nome)
        return lambda *args, **kwargs: Controle(*args, **kwargs)


class Controle(metaclass=_MetaControle):
    def __init__(self, *args, **kwargs):
        self.value = args[0] if args and isinstance(args[0], str) else None
        self.controls = []
        self.disabled = False
        self.__dict__.update(kwargs)


class FletFalso(types.ModuleType):
    def __getattr__(self, nome):
        if nome.startswith("__"):
            raise AttributeError(nome)
        return _Enum() if nome in ENUMS else Controle


class PaginaFalsa:
    """Guarda o que a tela desenhou. Sem área de transferência até ser liberada."""

    def __init__(self):
        self.adicionados = []
        self.navigation_bar = None
        self.window = SimpleNamespace()
        self.copiado = []
        self.dialogo = None          # diálogo aberto por cima da tela (ex.: confirmar)

    def liberar_area_de_transferencia(self):
        self.set_clipboard = self.copiado.append

    def add(self, *controles):
        self.adicionados.extend(controles)

    def clean(self):
        self.adicionados.clear()

    def show_dialog(self, dialogo):
        self.dialogo = dialogo

    def pop_dialog(self):
        self.dialogo = None

    def update(self):
        pass
