"""Versioned administrator settings used for both public and internal calculations."""
import json
from . import store


def current(conn):
    row = conn.execute("SELECT id,payload FROM commercial_settings ORDER BY created_at DESC,id DESC LIMIT 1").fetchone()
    return {**json.loads(row["payload"]), "settings_version": row["id"]} if row else None


def save(conn, data, user):
    identifier = store.identifier("CFG")
    conn.execute("INSERT INTO commercial_settings VALUES(?,?,?,?)", (identifier, store.dumps(data.model_dump(mode="json")), user["id"], store.timestamp()))
    store.audit(conn, user, "settings.published", identifier, details=data.model_dump(mode="json"))
    return identifier
