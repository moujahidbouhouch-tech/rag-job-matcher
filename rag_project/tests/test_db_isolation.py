import os

import psycopg

from rag_project.rag_core.config import get_settings


def test_which_database_am_i_using():
    """Diagnostic test to confirm which DB tests are connecting to."""
    settings = get_settings()

    print("\n" + "=" * 80)
    print("DIAGNOSTIC: Which database are tests using?")
    print(f"  settings.db_name: {settings.db_name}")
    print(f"  DB_NAME env: {os.getenv('DB_NAME')}")
    print(f"  TEST_DB_NAME env: {os.getenv('TEST_DB_NAME')}")
    print("=" * 80)

    conn_str = (
        f"host={settings.db_host} port={settings.db_port} "
        f"dbname={settings.db_name} user={settings.db_user}"
    )
    with psycopg.connect(conn_str, password=settings.db_password) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT current_database()")
            actual_db = cur.fetchone()[0]
            print(f"\nACTUAL DATABASE CONNECTED: {actual_db}")
            print("=" * 80 + "\n")
            # Guard: ensure we are not on production DB
            assert (
                actual_db != "rag"
            ), f"DANGER: Tests are using production DB '{actual_db}'!"
            assert actual_db == os.getenv(
                "TEST_DB_NAME", "rag_test_db"
            ), f"Tests should use '{os.getenv('TEST_DB_NAME', 'rag_test_db')}', but using '{actual_db}'"
