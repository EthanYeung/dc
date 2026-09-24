from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "runtime" / "db" / "company.db"
SCHEMA_PATH = ROOT / "runtime" / "schema.sql"


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        conn.execute(
            """
            INSERT OR IGNORE INTO company_state
            (id, mode, objective_version, available_capital_usd, committed_capital_usd)
            VALUES (1, 'discovery', 'v1', 0, 0)
            """
        )
    print(f"initialized: {DB_PATH}")


if __name__ == "__main__":
    main()
