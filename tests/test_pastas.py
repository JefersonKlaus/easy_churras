"""Onde o app guarda os dados."""
import pytest

from churrasco_facil.pastas import pasta_de_dados


@pytest.fixture
def sem_variaveis(monkeypatch):
    for variavel in ("GROQ_API_KEY", "CHURRASCO_DADOS", "FLET_APP_STORAGE_DATA"):
        monkeypatch.delenv(variavel, raising=False)
    return monkeypatch


def test_pasta_de_dados_do_app_vale_primeiro(sem_variaveis, tmp_path):
    sem_variaveis.setenv("CHURRASCO_DADOS", str(tmp_path))
    sem_variaveis.setenv("FLET_APP_STORAGE_DATA", str(tmp_path / "flet"))
    assert pasta_de_dados() == tmp_path


def test_pasta_de_dados_do_flet_vale_em_seguida(sem_variaveis, tmp_path):
    sem_variaveis.setenv("FLET_APP_STORAGE_DATA", str(tmp_path / "flet"))
    assert pasta_de_dados() == tmp_path / "flet"


def test_pasta_de_dados_padrao_fica_na_pasta_do_usuario(sem_variaveis):
    assert pasta_de_dados().name == ".churrasco_facil"
