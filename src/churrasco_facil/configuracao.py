"""Configurações do usuário, guardadas só no aparelho (chave, modelo, preços, quantidades)."""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Optional

from .calculadora import Parametros
from .catalogo_carnes import CORTES
from .catalogo_itens import ITENS
from .cliente_groq import MODELO_PADRAO, ClienteGroq
from .dinheiro import reais_para_centavos

logger = logging.getLogger(__name__)

NOME_ARQUIVO = "configuracao.json"
PRECO_MAXIMO = 10_000_00   # R$ 10.000,00 por unidade base: acima disso é erro de digitação


@dataclass
class Configuracao:
    chave_groq: str = ""
    modelo: str = MODELO_PADRAO
    precos: dict[str, int] = field(default_factory=dict)        # id -> centavos
    parametros: dict[str, float] = field(default_factory=dict)  # campo de Parametros -> valor


def pasta_de_dados() -> Path:
    """CHURRASCO_DADOS (testes) > pasta de dados do Flet > pasta do usuário."""
    for variavel in ("CHURRASCO_DADOS", "FLET_APP_STORAGE_DATA"):
        valor = os.environ.get(variavel)
        if valor:
            return Path(valor)
    return Path.home() / ".churrasco_facil"


def caminho_configuracao() -> Path:
    return pasta_de_dados() / NOME_ARQUIVO


def _precos_limpos(bruto: object) -> dict[str, int]:
    if not isinstance(bruto, dict):
        return {}
    validos = set(CORTES) | set(ITENS)
    return {k: v for k, v in bruto.items()
            if k in validos and isinstance(v, int) and not isinstance(v, bool)
            and 0 <= v <= PRECO_MAXIMO}


def juntar_precos(atuais: Mapping[str, int], digitados: Mapping[str, str]) -> dict[str, int]:
    """Junta aos preços salvos os que o usuário digitou (em reais), por id do produto.

    Preço igual ao do catálogo não é guardado. Levanta ValueError citando o produto.
    """
    novos = dict(atuais)
    for id, texto in digitados.items():
        produto = CORTES.get(id) or ITENS[id]
        try:
            centavos = reais_para_centavos(texto)
        except ValueError as erro:
            raise ValueError(f"{produto.nome}: {erro}") from None
        if centavos > PRECO_MAXIMO:
            raise ValueError(f"{produto.nome}: preço alto demais")
        if centavos == produto.preco:
            novos.pop(id, None)
        else:
            novos[id] = centavos
    return novos


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
        precos=_precos_limpos(dados.get("precos")),
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
