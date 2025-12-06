import os
import re
import subprocess
import sys
import types
from pathlib import Path

import pytest

from rag_project.config import (
    DB_DEFAULT_HOST,
    DB_DEFAULT_NAME,
    DB_DEFAULT_PASSWORD,
    DB_DEFAULT_PORT,
    DB_DEFAULT_USER,
    INTEGRATION_BOOTSTRAP_ENV,
    REQUIRED_TABLES,
    TEST_DB_HOST,
    TEST_DB_NAME,
    TEST_DB_PASSWORD,
    TEST_DB_PORT,
    TEST_DB_USER,
)
from rag_project.rag_core.config import get_settings

# Provide a lightweight stub for python-dotenv if it's not installed.
try:
    import dotenv  # noqa: F401
except ImportError:
    sys.modules["dotenv"] = types.SimpleNamespace(load_dotenv=lambda *args, **kwargs: None)

# Stub sentence_transformers if unavailable.
try:
    import sentence_transformers  # noqa: F401
except ImportError:
    class _DummyModel:
        def __init__(self, *_args, **_kwargs):
            pass

        def encode(self, texts, normalize_embeddings=True):
            if isinstance(texts, str):
                texts = [texts]
            return [[0.0] for _ in texts]

    sys.modules["sentence_transformers"] = types.SimpleNamespace(SentenceTransformer=_DummyModel)

# Stub httpx if unavailable.
try:
    import httpx  # noqa: F401
except ImportError:
    class _DummyHTTPError(Exception):
        pass

    class _DummyTimeout(_DummyHTTPError):
        pass

    def _dummy_post(*_args, **_kwargs):
        raise _DummyHTTPError("httpx stubbed")

    def _dummy_get(*_args, **_kwargs):
        raise _DummyHTTPError("httpx stubbed")

    sys.modules["httpx"] = types.SimpleNamespace(
        post=_dummy_post,
        get=_dummy_get,
        HTTPError=_DummyHTTPError,
        TimeoutException=_DummyTimeout,
    )

# Provide a lightweight stub for psycopg/pgvector when not installed so imports succeed.
try:
    import psycopg  # noqa: F401
except ImportError:
    class _OperationalError(Exception):
        pass

    class _DummyCursor:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def execute(self, *_args, **_kwargs):
            raise _OperationalError("psycopg stubbed")

        def fetchone(self):
            return None

        def fetchall(self):
            return []

    class _DummyConn:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def cursor(self):
            return _DummyCursor()

        def close(self):
            return None

    def _connect(*_args, **_kwargs):
        raise _OperationalError("psycopg stubbed")

    sys.modules["psycopg"] = types.SimpleNamespace(
        connect=_connect,
        OperationalError=_OperationalError,
    )
    json_mod = types.SimpleNamespace(Json=lambda obj: obj)
    sys.modules["psycopg.types"] = types.SimpleNamespace(json=json_mod)
    sys.modules["psycopg.types.json"] = json_mod

try:
    import pgvector.psycopg  # noqa: F401
except ImportError:
    sys.modules["pgvector.psycopg"] = types.SimpleNamespace(register_vector=lambda *_args, **_kwargs: None)

# Ensure project root is on sys.path so test packages resolve.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _assert_valid_identifier(value: str, label: str):
    if not re.match(r"^[A-Za-z0-9_]+$", value or ""):
        raise ValueError(f"Invalid {label}: {value!r}. Only alphanumeric characters and underscores are allowed.")


def _service_bootstrap():
    flag = os.getenv(INTEGRATION_BOOTSTRAP_ENV, "0").lower()
    if flag in {"0", "false", "no"}:
        return
    script = ROOT.parent / "scripts" / "ensure_services.sh"
    if not script.is_file():
        return
    subprocess.run([str(script)], check=True, cwd=script.parent, text=True, capture_output=False)


def _source_db_settings():
    settings = get_settings()
    return {
        "host": settings.db_host or DB_DEFAULT_HOST,
        "port": settings.db_port or DB_DEFAULT_PORT,
        "dbname": settings.db_name or DB_DEFAULT_NAME,
        "user": settings.db_user or DB_DEFAULT_USER,
        "password": settings.db_password or DB_DEFAULT_PASSWORD,
    }


def _test_db_settings(source: dict) -> dict:
    # Always target the dedicated test database, never the main rag DB.
    return {
        "host": TEST_DB_HOST or "127.0.0.1",
        "port": TEST_DB_PORT or source["port"],
        "dbname": TEST_DB_NAME,
        "user": TEST_DB_USER or source["user"],
        "password": TEST_DB_PASSWORD or source["password"],
    }


def _get_test_target() -> dict:
    """Build test DB target from constants/env."""
    host = os.getenv("TEST_DB_HOST") or TEST_DB_HOST or "127.0.0.1"
    port = os.getenv("TEST_DB_PORT") or TEST_DB_PORT or 5433
    dbname = os.getenv("TEST_DB_NAME") or TEST_DB_NAME or "rag_test_db"
    user = os.getenv("TEST_DB_USER") or TEST_DB_USER or "rag"
    password = os.getenv("TEST_DB_PASSWORD") or TEST_DB_PASSWORD or DB_DEFAULT_PASSWORD or os.getenv("PGPASSWORD")
    
    return {
        "host": host,
        "port": int(port),
        "dbname": dbname,
        "user": user,
        "password": password,
    }

def _ensure_not_production(target: dict, source: dict):
    """Safety check to avoid truncating the main rag DB."""
    if target["dbname"] == source["dbname"]:
        msg = (
            f"[tests] Refusing to truncate DB '{target['dbname']}' because it matches the source DB. "
            f"Set TEST_DB_NAME to a dedicated test database."
        )
        print(msg)
        raise RuntimeError(msg)


def _ensure_schema_exists(source: dict, target: dict):
    """
    Ensure the test DB exists and has the required tables.
    - Creates the test DB if missing.
    - Copies schema from source DB (schema-only) if required tables are absent.
    """
    import psycopg  # noqa: WPS433

    # 1) Create DB if missing
    try:
        psycopg.connect(
            f"host={target['host']} port={target['port']} dbname={target['dbname']} user={target['user']}",
            password=target.get("password"),
            connect_timeout=30,
        ).close()
    except psycopg.OperationalError:
        maint_db = "postgres"
        print(f"[tests] creating test db {target['dbname']} (host={target['host']} port={target['port']}) from maintenance db {maint_db}")
        with psycopg.connect(
            f"host={target['host']} port={target['port']} dbname={maint_db} user={target['user']}",
            password=target.get("password"),
            connect_timeout=30,
        ) as conn:
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (target["dbname"],))
                if not cur.fetchone():
                    _assert_valid_identifier(target["dbname"], "database name")
                    _assert_valid_identifier(target["user"], "database user")
                    print(f"[tests] creating database {target['dbname']} owned by {target['user']}")
                    cur.execute(f"CREATE DATABASE {target['dbname']} OWNER {target['user']}")

    # 2) Check for required tables
    required = list(REQUIRED_TABLES)
    with psycopg.connect(
        f"host={target['host']} port={target['port']} dbname={target['dbname']} user={target['user']}",
        password=target.get("password"),
        connect_timeout=30,
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT table_name FROM information_schema.tables
                WHERE table_schema='public' AND table_name = ANY(%s)
                """,
                (required,),
            )
            existing = {row[0] for row in cur.fetchall()}
    if set(required).issubset(existing):
        return

    # 3) Clone schema-only from source
    env = _psql_env({**source, **target})
    dump_cmd = [
        "pg_dump",
        "-h",
        str(source["host"]),
        "-p",
        str(source["port"]),
        "-U",
        str(source["user"]),
        "-d",
        str(source["dbname"]),
        "--schema-only",
        "--no-owner",
        "--no-privileges",
    ]
    restore_cmd = [
        "psql",
        "-h",
        str(target["host"]),
        "-p",
        str(target["port"]),
        "-U",
        str(target["user"]),
        "-d",
        str(target["dbname"]),
    ]
    proc = subprocess.run(
        " ".join(dump_cmd) + " | " + " ".join(restore_cmd),
        shell=True,
        env=env,
        cwd=str(ROOT.parent),
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Schema clone failed: {proc.stderr}")


def _ensure_test_db_exists(target: dict):
    """Create test DB if missing, or just verify it exists."""
    import psycopg  # noqa: WPS433

    try:
        with psycopg.connect(
            f"host={target['host']} port={target['port']} dbname={target['dbname']} user={target['user']}",
            password=target.get("password"),
            connect_timeout=5,
        ) as conn:
            print(f"[tests] Test DB '{target['dbname']}' exists")
    except psycopg.OperationalError:
        print(f"[tests] Creating test DB '{target['dbname']}'")
        with psycopg.connect(
            f"host={target['host']} port={target['port']} dbname=postgres user={target['user']}",
            password=target.get("password"),
            connect_timeout=5,
        ) as conn:
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute(f"CREATE DATABASE {target['dbname']} OWNER {target['user']}")


def _psql_env(settings: dict) -> dict:
    env = os.environ.copy()
    if settings.get("password"):
        env["PGPASSWORD"] = str(settings["password"])
    return env


def _drop_create_test_db(source: dict, target: dict):
    """
    UTILITY FUNCTION - Not called in normal test flow.
    Use manually when schema drift requires full test DB refresh.
    WARNING: Terminates all connections to source DB briefly.
    """
    maint_db = "postgres"
    conn_dsn = f"host={target['host']} port={target['port']} dbname={maint_db} user={target['user']}"
    import psycopg  # noqa: WPS433  # local import to honor stubs only when absent

    with psycopg.connect(conn_dsn, connect_timeout=30, password=target.get("password")) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = %s AND pid <> pg_backend_pid();
                """,
                (target["dbname"],),
            )
            cur.execute(
                """
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = %s AND pid <> pg_backend_pid();
                """,
                (source["dbname"],),
            )
            _assert_valid_identifier(target["dbname"], "database name")
            _assert_valid_identifier(source["dbname"], "source database name")
            _assert_valid_identifier(target["user"], "database user")
            cur.execute(f"DROP DATABASE IF EXISTS {target['dbname']}")
            cur.execute(f"CREATE DATABASE {target['dbname']} OWNER {target['user']}")

    dump_cmd = [
        "pg_dump",
        "-h",
        str(source["host"]),
        "-p",
        str(source["port"]),
        "-U",
        str(source["user"]),
        "-d",
        str(source["dbname"]),
        "--schema-only",
        "--no-owner",
        "--no-privileges",
    ]
    restore_cmd = [
        "psql",
        "-h",
        str(target["host"]),
        "-p",
        str(target["port"]),
        "-U",
        str(target["user"]),
        "-d",
        str(target["dbname"]),
    ]

    env = _psql_env(source)
    env.update(_psql_env(target))
    proc = subprocess.run(
        " ".join(dump_cmd) + " | " + " ".join(restore_cmd),
        shell=True,
        env=env,
        cwd=str(ROOT.parent),
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError("pg_dump/psql schema clone failed; ensure pg_dump and psql are installed and accessible")
    # Ensure app tables are empty after clone
    _truncate_tables(target)


def _truncate_tables(target: dict):
    table_list = list(REQUIRED_TABLES)
    if not table_list:
        return
    quoted = ", ".join(f'"{t}"' for t in table_list)
    print(
        f"[tests] TRUNCATE target db={target['dbname']} host={target['host']} port={target['port']} "
        f"user={target['user']} tables={table_list}"
    )
    cmd = [
        "psql",
        "-h",
        str(target["host"]),
        "-p",
        str(target["port"]),
        "-U",
        str(target["user"]),
        "-d",
        str(target["dbname"]),
        "-c",
        f"TRUNCATE {quoted} RESTART IDENTITY CASCADE",
    ]
    env = _psql_env(target)
    try:
        subprocess.run(cmd, check=True, env=env, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        if "does not exist" in exc.stderr:
            print(f"[tests] TRUNCATE skipped, tables not yet created")
            return
        raise RuntimeError(f"TRUNCATE failed: {exc.stderr}") from exc


@pytest.fixture(scope="session", autouse=True)
def _bootstrap_and_clone_db():
    _service_bootstrap()
    target = _get_test_target()
    if target["dbname"] in ("rag", None, ""):
        raise RuntimeError(f"TEST_DB_NAME must be a dedicated test DB, not '{target['dbname']}'")
    _ensure_test_db_exists(target)
    print(f"[tests] SESSION DB settings -> target={target['dbname']}")
    os.environ["DB_NAME"] = target["dbname"]
    os.environ["DB_POSTGRESDB_DATABASE"] = target["dbname"]
    os.environ["POSTGRES_DB"] = target["dbname"]
    os.environ["DB_HOST"] = target["host"]
    os.environ["DB_PORT"] = str(target["port"])
    os.environ["DB_USER"] = target["user"]
    if target.get("password") is not None:
        os.environ["DB_PASSWORD"] = str(target["password"])
    get_settings.cache_clear()
    yield


@pytest.fixture(autouse=True)
def _reset_test_db():
    target = _get_test_target()
    if target["dbname"] in ("rag", None, ""):
        raise RuntimeError(f"TEST_DB_NAME must be a dedicated test DB, not '{target['dbname']}'")
    print(f"[tests] PER-TEST TRUNCATE target={target['dbname']}")
    _truncate_tables(target)
    yield
