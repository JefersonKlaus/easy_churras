"""Rode UMA vez numa máquina COM internet: baixa tudo para a pasta vendor/ do projeto.

    python offline/baixar_pacotes.py

Depois é só copiar a pasta inteira do projeto (com vendor/) para o outro computador.
O outro computador precisa ter o mesmo sistema e a mesma versão do Python deste.
"""
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VENDOR = ROOT / "vendor"
PACOTES = ["flet[all]", "pytest", "setuptools>=68", "wheel"]


def main() -> int:
    VENDOR.mkdir(exist_ok=True)
    subprocess.check_call([sys.executable, "-m", "pip", "download", *PACOTES, "-d", str(VENDOR)])
    flet_home = Path.home() / ".flet"
    if flet_home.exists():  # algumas versões guardam aqui o programa que abre a janela
        shutil.copytree(flet_home, VENDOR / "flet_home", dirs_exist_ok=True)
        print(f"Copiei {flet_home} para vendor/flet_home")
    (VENDOR / "LEIAME.txt").write_text(
        f"Baixado com Python {platform.python_version()} em {platform.system()} "
        f"{platform.machine()}.\nO outro computador precisa ser igual.\n", encoding="utf-8")
    print(f"Pronto: {len(list(VENDOR.glob('*.whl')))} pacotes em {VENDOR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
