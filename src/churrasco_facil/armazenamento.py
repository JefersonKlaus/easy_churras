"""Planos salvos em SQLite ("Meus churrascos"). Guardamos só o pedido: o plano é recalculado
ao abrir (veja `serializacao`)."""
from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from .pastas import pasta_de_dados
from .planejador import Pedido
from .serializacao import pedido_de_dict, pedido_para_dict

NOME_BANCO = "planos.sqlite3"
VERSAO = 1


@dataclass(frozen=True)
class PlanoSalvo:
    """Um item de "Meus churrascos": o que a tela inicial mostra."""

    id: int
    nome: str
    hora_servir: datetime


class Armazenamento:
    """Abre uma conexão por operação: simples e seguro com a interface em tarefas async."""

    def __init__(self, caminho: Optional[Path | str] = None) -> None:
        self.caminho = str(caminho) if caminho else str(pasta_de_dados() / NOME_BANCO)
        self._memoria: Optional[sqlite3.Connection] = None
        if self.caminho == ":memory:":
            self._memoria = sqlite3.connect(":memory:")
        else:
            Path(self.caminho).parent.mkdir(parents=True, exist_ok=True)
        with self._conexao() as con:
            con.execute("CREATE TABLE IF NOT EXISTS planos ("
                        "id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, "
                        "criado_em TEXT NOT NULL, hora_servir TEXT NOT NULL, "
                        "dados TEXT NOT NULL)")
            con.execute(f"PRAGMA user_version = {VERSAO}")

    @contextmanager
    def _conexao(self) -> Iterator[sqlite3.Connection]:
        """Uma conexão com transação (grava tudo ou nada), fechada no fim."""
        con = self._memoria or sqlite3.connect(self.caminho)
        try:
            with con:
                yield con
        finally:
            if con is not self._memoria:
                con.close()

    def salvar(self, pedido: Pedido, agora: Optional[datetime] = None) -> int:
        with self._conexao() as con:
            cursor = con.execute(
                "INSERT INTO planos (nome, criado_em, hora_servir, dados) VALUES (?, ?, ?, ?)",
                (pedido.nome, (agora or datetime.now()).isoformat(timespec="seconds"),
                 pedido.hora_servir.isoformat(timespec="minutes"), _json(pedido)))
            return int(cursor.lastrowid)

    def atualizar(self, id: int, pedido: Pedido) -> bool:
        """Grava o pedido por cima de um plano já salvo (ex.: a pessoa trocou as carnes)."""
        with self._conexao() as con:
            return con.execute(
                "UPDATE planos SET nome = ?, hora_servir = ?, dados = ? WHERE id = ?",
                (pedido.nome, pedido.hora_servir.isoformat(timespec="minutes"), _json(pedido),
                 id)).rowcount > 0

    def listar(self) -> list[PlanoSalvo]:
        """Do mais recente para o mais antigo."""
        with self._conexao() as con:
            linhas = con.execute("SELECT id, nome, hora_servir FROM planos "
                                 "ORDER BY id DESC").fetchall()
        return [PlanoSalvo(i, n, datetime.fromisoformat(h)) for i, n, h in linhas]

    def carregar(self, id: int) -> Pedido:
        with self._conexao() as con:
            linha = con.execute("SELECT dados FROM planos WHERE id = ?", (id,)).fetchone()
        if linha is None:
            raise KeyError(f"plano {id} não existe")
        try:
            return pedido_de_dict(json.loads(linha[0]))
        except json.JSONDecodeError:
            raise ValueError("registro corrompido") from None

    def excluir(self, id: int) -> bool:
        with self._conexao() as con:
            return con.execute("DELETE FROM planos WHERE id = ?", (id,)).rowcount > 0


def _json(pedido: Pedido) -> str:
    return json.dumps(pedido_para_dict(pedido), ensure_ascii=False)
