import os
import subprocess
from pathlib import Path

import pytest

from rag_project.config import INTEGRATION_BOOTSTRAP_ENV


def _should_run_bootstrap(config: pytest.Config) -> bool:
    """Decide whether to invoke service bootstrap."""
    flag = os.getenv(INTEGRATION_BOOTSTRAP_ENV)
    if flag is not None:
        if flag.lower() in {"0", "false", "no"}:
            return False
        if flag == "1":
            return True
        return False

    markexpr = (getattr(config.option, "markexpr", "") or "").lower()
    if "integration" in markexpr:
        return False

    args = [str(a) for a in config.invocation_params.args]
    if any("tests/integration" in arg for arg in args):
        return False

    # No args means full suite, which includes integration tests.
    if not args:
        return False

    return False


@pytest.hookimpl(tryfirst=True)
def pytest_sessionstart(session: pytest.Session) -> None:
    if not _should_run_bootstrap(session.config):
        return

    script = Path(__file__).resolve().parents[3] / "scripts" / "ensure_services.sh"
    if not script.is_file():
        pytest.exit(f"Service bootstrap script missing: {script}", returncode=1)

    result = subprocess.run(
        [str(script)],
        capture_output=True,
        text=True,
        cwd=script.parent,
    )

    if result.returncode != 0:
        msg = (
            f"ensure_services.sh failed with exit code {result.returncode}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
        pytest.exit(msg, returncode=result.returncode)

    if result.stdout:
        print(result.stdout, end="")
