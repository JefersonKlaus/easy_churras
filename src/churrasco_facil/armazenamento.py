"""Planos salvos em SQLite. Guardamos só o pedido: o plano é recalculado ao abrir."""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .calculadora import Convidados
from .catalogo_carnes import CORTES
from .configuracao import pasta_de_dados
from .planejador import Pedido

NOME_BANCO = "planos.sqlite3"
VERSAO = 1


@dataclass(frozen=True)
class PlanoSalvo:
    id: int
    nome: str
    criado_em: datetime
    hora_servir: datetime


def pedido_para_dict(pedido: Pedido) -> dict[str, Any]:
    c = pedido.convidados
    return {
        "nome": pedido.nome,
        "hora_servir": pedido.hora_servir.isoformat(timespec="minutes"),
        "orcamento": pedido.orcamento,
        "pesos_preferidos": pedido.pesos_preferidos,
        "convidados": {"adultos": c.adultos, "criancas": c.criancas,
                       "vegetarianos": c.vegetarianos, "bebem_alcool": c.bebem_alcool,
                       "duracao_horas": c.duracao_horas},
    }


def pedido_de_dict(dados: dict[str, Any]) -> Pedido:
    """Reconstrói o pedido. Levanta ValueError se o registro estiver corrompido."""
    try:
        conv = dados["convidados"]
        orcamento = dados.get("orcamento")
        pesos = dados.get("pesos_preferidos") or {}
        return Pedido(
            convidados=Convidados(adultos=int(conv["adultos"]), criancas=int(conv["criancas"]),
                                  vegetarianos=int(conv["vegetarianos"]),
                                  bebem_alcool=int(conv["bebem_alcool"]),
                                  duracao_horas=float(conv["duracao_horas"])),
            hora_servir=datetime.fromisoformat(dados["hora_servir"]),
            orcamento=int(orcamento) if orcamento else None,
            pesos_preferidos={k: int(v) for k, v in pesos.items() if k in CORTES},
            nome=str(dados.get("nome") or "Meu churrasco")[:60],
        )
    except (KeyError, TypeError, AttributeError) as erro:
        raise ValueError(f"registro inválido: {erro}") from None


class Armazenamento:
    """Abre uma conexão por operação: simples e seguro com a interface em tarefas async."""

    def __init__(self, caminho: Optional[Path | str] = None) -> None:
        self.caminho = str(caminho) if caminho else str(pasta_de_dados() / NOME_BANCO)
        self._memoria: Optional[sqlite3.Connection] = None
        if self.caminho == ":memory:":
            self._memoria = sqlite3.connect(":memory:")
        elif self.caminho != ":memory:":
            Path(self.caminho).parent.mkdir(parents=True, exist_ok=True)
        self._criar_tabelas()

    def _conectar(self) -> sqlite3.Connection:
        return self._memoria or sqlite3.connect(self.caminho)

    def _fechar(self, con: sqlite3.Connection) -> None:
        if con is not self._memoria:
            con.close()

    def _criar_tabelas(self) -> None:
        con = self._conectar()
        try:
            with con:
                con.execute("CREATE TABLE IF NOT EXISTS planos ("
                            "id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, "
                            "criado_em TEXT NOT NULL, hora_servir TEXT NOT NULL, "
                            "dados TEXT NOT NULL, explicacao TEXT)")
                con.execute(f"PRAGMA user_version = {VERSAO}")
        finally:
            self._fechar(con)

    def salvar(self, pedido: Pedido, explicacao: Optional[str] = None,
               agora: Optional[datetime] = None) -> int:
        con = self._conectar()
        try:
            with con:
                cursor = con.execute(
                    "INSERT INTO planos (nome, criado_em, hora_servir, dados, explicacao) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (pedido.nome, (agora or datetime.now()).isoformat(timespec="seconds"),
                     pedido.hora_servir.isoformat(timespec="minutes"),
                     json.dumps(pedido_para_dict(pedido), ensure_ascii=False), explicacao))
                return int(cursor.lastrowid)
        finally:
            self._fechar(con)

    def listar(self) -> list[PlanoSalvo]:
        """Do mais recente para o mais antigo."""
        con = self._conectar()
        try:
            linhas = con.execute("SELECT id, nome, criado_em, hora_servir FROM planos "
                                 "ORDER BY id DESC").fetchall()
        finally:
            self._fechar(con)
        return [PlanoSalvo(i, n, datetime.fromisoformat(c), datetime.fromisoformat(h))
                for i, n, c, h in linhas]

    def carregar(self, id: int) -> tuple[Pedido, Optional[str]]:
        con = self._conectar()
        try:
            linha = con.execute("SELECT dados, explicacao FROM planos WHERE id = ?",
                                (id,)).fetchone()
        finally:
            self._fechar(con)
        if linha is None:
            raise KeyError(f"plano {id} não existe")
        try:
            return pedido_de_dict(json.loads(linha[0])), linha[1]
        except json.JSONDecodeError:
            raise ValueError("registro corrompido") from None

    def atualizar_explicacao(self, id: int, explicacao: str) -> bool:
        con = self._conectar()
        try:
            with con:
                return con.execute("UPDATE planos SET explicacao = ? WHERE id = ?",
                                   (explicacao, id)).rowcount > 0
        finally:
            self._fechar(con)

    def excluir(self, id: int) -> bool:
        con = self._conectar()
        try:
            with con:
                return con.execute("DELETE FROM planos WHERE id = ?", (id,)).rowcount > 0
        finally:
            self._fechar(con)
