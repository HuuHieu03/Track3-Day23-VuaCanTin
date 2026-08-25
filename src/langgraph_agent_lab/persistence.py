"""Checkpointer adapter."""

from __future__ import annotations

import sqlite3
from typing import Any

DEFAULT_SQLITE_PATH = "outputs/checkpoints.sqlite"


def build_checkpointer(kind: str = "memory", database_url: str | None = None) -> Any | None:
    """Return a LangGraph checkpointer.

    For SQLite: connects with sqlite3, enables WAL mode, and hands the
    connection to SqliteSaver so state history survives across runs
    for the same thread_id.
    """
    if kind == "none":
        return None
    if kind == "memory":
        from langgraph.checkpoint.memory import MemorySaver

        return MemorySaver()
    if kind == "sqlite":
        from langgraph.checkpoint.sqlite import SqliteSaver

        conn = sqlite3.connect(database_url or DEFAULT_SQLITE_PATH, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        saver = SqliteSaver(conn)
        saver.setup()
        return saver
    if kind == "postgres":
        raise NotImplementedError(
            "TODO(student): implement Postgres checkpointer (optional extension)"
        )
    raise ValueError(f"Unknown checkpointer kind: {kind}")
