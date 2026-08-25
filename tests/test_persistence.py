"""Persistence layer tests.

These tests verify the SQLite checkpointer: WAL mode, and that state
survives across separate build_checkpointer() calls against the same
database file (the core "does persistence actually persist" guarantee).
"""

import sqlite3

import pytest

from langgraph_agent_lab.persistence import build_checkpointer


def test_build_checkpointer_none_returns_none():
    assert build_checkpointer("none") is None


def test_build_checkpointer_memory_returns_saver():
    from langgraph.checkpoint.memory import MemorySaver

    assert isinstance(build_checkpointer("memory"), MemorySaver)


def test_build_checkpointer_unknown_kind_raises():
    with pytest.raises(ValueError):
        build_checkpointer("bogus")


def test_build_checkpointer_sqlite_creates_wal_mode_db(tmp_path):
    db_path = tmp_path / "checkpoints.sqlite"

    build_checkpointer("sqlite", database_url=str(db_path))

    assert db_path.exists()
    conn = sqlite3.connect(str(db_path))
    mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
    conn.close()
    assert mode.lower() == "wal"


def test_build_checkpointer_sqlite_persists_state_across_instances(tmp_path):
    from langgraph.checkpoint.base import empty_checkpoint

    db_path = tmp_path / "checkpoints.sqlite"
    thread_id = "thread-persist-test"
    config = {"configurable": {"thread_id": thread_id, "checkpoint_ns": ""}}
    checkpoint = empty_checkpoint()
    checkpoint["channel_values"] = {"query": "hello"}

    writer = build_checkpointer("sqlite", database_url=str(db_path))
    writer.put(config, checkpoint, {"source": "input", "step": 0, "writes": {}, "parents": {}}, {})

    reader = build_checkpointer("sqlite", database_url=str(db_path))
    tuple_ = reader.get_tuple(config)

    assert tuple_ is not None
    assert tuple_.checkpoint["channel_values"]["query"] == "hello"
