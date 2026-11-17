"""Rode na máquina SEM internet, dentro da pasta copiada do projeto:

    python offline/instalar_offline.py

Cria a pasta .venv e instala tudo só a partir de vendor/ (sem acessar a internet).
"""
import shutil
import subprocess
import sys
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VENDOR = ROOT / "vendor"
VENV = ROOT / ".venv"


def pip(*args: str) -> None:
    python = VENV / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    subprocess.check_call([str(python), "-m", "pip", *args])


def main() -> int:
    if not list(VENDOR.glob("*.whl")) and not list(VENDOR.glob("*.tar.gz")):
        print("A pasta vendor/ está vazia. Rode offline/baixar_pacotes.py numa máquina com internet.")
        return 1
    venv.create(VENV, with_pip=True)
    pip("install", "--no-index", f"--find-links={VENDOR}", "flet[all]", "pytest",
        "setuptools", "wheel")
    pip("install", "--no-index", "--no-build-isolation", "--no-deps", "-e", str(ROOT))
    saved_home = VENDOR / "flet_home"
    target = Path.home() / ".flet"
    if saved_home.exists() and not target.exists():
        shutil.copytree(saved_home, target)
        print(f"Restaurei {target}")
    activate = r".venv\Scripts\activate" if sys.platform == "win32" else "source .venv/bin/activate"
    print(f"Pronto. Para abrir o app:  {activate}  e depois  flet run")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
