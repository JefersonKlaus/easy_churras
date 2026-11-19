"""Configurações do usuário, guardadas só no aparelho (chave, modelo, preços, quantidades):
ler e gravar o arquivo, e o que sai delas (a chave que vale, a tabela, o cliente do Groq)."""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .cliente_groq import MODELO_PADRAO, ClienteGroq
from .parametros import Parametros
from .pastas import pasta_de_dados
from .precos import precos_validos

logger = logging.getLogger(__name__)

NOME_ARQUIVO = "configuracao.json"


@dataclass
class Configuracao:
    chave_groq: str = ""
    modelo: str = MODELO_PADRAO
    precos: dict[str, int] = field(default_factory=dict)        # id -> centavos
    parametros: dict[str, float] = field(default_factory=dict)  # campo de Parametros -> valor


def caminho_configuracao() -> Path:
    return pasta_de_dados() / NOME_ARQUIVO


def carregar_configuracao(caminho: Optional[Path] = None) -> Configuracao:
    """Lê o arquivo; qualquer problema devolve a configuração padrão."""
    caminho = caminho or caminho_configuracao()
    try:
        dados = json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return Configuracao()
    if not isinstance(dados, dict):
        return Configuracao()
    chave, modelo = dados.get("chave_groq"), dados.get("modelo")
    parametros = Parametros.de_dicionario(dados.get("parametros"))
    padrao = Parametros()
    alterados = {k: v for k, v in vars(parametros).items() if v != getattr(padrao, k)}
    return Configuracao(
        chave_groq=chave.strip() if isinstance(chave, str) else "",
        modelo=modelo.strip()[:80] if isinstance(modelo, str) and modelo.strip()
        else MODELO_PADRAO,
        precos=precos_validos(dados.get("precos")),
        parametros=alterados,
    )


def salvar_configuracao(config: Configuracao, caminho: Optional[Path] = None) -> bool:
    """Grava com arquivo temporário. Tenta deixar o arquivo legível só pelo dono."""
    caminho = caminho or caminho_configuracao()
    conteudo = {"chave_groq": config.chave_groq, "modelo": config.modelo,
                "precos": config.precos, "parametros": config.parametros}
    try:
        caminho.parent.mkdir(parents=True, exist_ok=True)
        temporario = caminho.with_suffix(caminho.suffix + ".tmp")
        temporario.write_text(json.dumps(conteudo, ensure_ascii=False, indent=2),
                              encoding="utf-8")
        try:
            temporario.chmod(0o600)
        except OSError:
            logger.debug("não foi possível restringir permissões", exc_info=True)
        temporario.replace(caminho)
        return True
    except OSError:
        logger.warning("não consegui salvar a configuração", exc_info=True)
        return False


def chave_efetiva(config: Configuracao) -> str:
    """A variável de ambiente GROQ_API_KEY vale mais do que a chave salva no aparelho."""
    return os.environ.get("GROQ_API_KEY", "").strip() or config.chave_groq.strip()


def parametros_da_configuracao(config: Configuracao) -> Parametros:
    return Parametros.de_dicionario(config.parametros)


def cliente_da_configuracao(config: Configuracao) -> ClienteGroq:
    return ClienteGroq(chave_efetiva(config), modelo=config.modelo)
