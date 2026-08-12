import sqlite3
from tabulate import tabulate
from typing import List, Tuple, Any

# NOTE: For production you should replace sqlite3 with SQLAlchemy / psycopg2 and use pooled connections + timeouts.

class SQLTools:
    def __init__(self, db_path="example.db", readonly=True, timeout_seconds=10):
        self.db_path = db_path
        self.readonly = readonly
        self.timeout_seconds = timeout_seconds

    def _connect(self):
        # For sqlite: use URI to force read-only if requested
        if self.readonly:
            uri = f"file:{self.db_path}?mode=ro"
            conn = sqlite3.connect(uri, uri=True, timeout=self.timeout_seconds)
        else:
            conn = sqlite3.connect(self.db_path, timeout=self.timeout_seconds)
        conn.row_factory = sqlite3.Row
        return conn

    def get_schema(self) -> str:
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("SELECT name, type, sql FROM sqlite_master WHERE type IN ('table','view') ORDER BY name")
        rows = cur.fetchall()
        parts = []
        for r in rows:
            parts.append(f"{r['type']} {r['name']}: {r['sql']}")
        conn.close()
        return "\n".join(parts) if parts else "No tables found."

    def list_tables(self) -> List[str]:
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [r[0] for r in cur.fetchall()]
        conn.close()
        return tables

    def run_sql(self, sql: str, max_rows: int = 50) -> Tuple[str, List[str]]:
        # Basic safety: allow only SELECT, PRAGMA read-only statements; block write statements
        sql_stripped = sql.strip().lower()
        allowed_prefixes = ("select", "with", "pragma", "explain")
        if not sql_stripped:
            return "Empty query", []
        if not sql_stripped.split()[0].startswith(allowed_prefixes):
            return f"Refused to run non-read query. Allowed prefixes: {allowed_prefixes}", []

        conn = self._connect()
        cur = conn.cursor()
        try:
            cur.execute(sql)
            cols = [d[0] for d in cur.description] if cur.description else []
            rows = cur.fetchmany(max_rows)
            table = tabulate(rows, headers=cols, tablefmt="psql") if rows else "No rows returned."
            conn.close()
            return table, cols
        except Exception as e:
            conn.close()
            return f"SQL error: {e}", []

    def explain_sql(self, sql: str) -> str:
        # SQLite EXPLAIN QUERY PLAN
        try:
            conn = self._connect()
            cur = conn.cursor()
            cur.execute(f"EXPLAIN QUERY PLAN {sql}")
            rows = cur.fetchall()
            conn.close()
            if not rows:
                return "No explain output."
            return "\n".join(str(r) for r in rows)
        except Exception as e:
            return f"EXPLAIN error: {e}"
