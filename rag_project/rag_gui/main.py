import sys
from pathlib import Path

import torch

from PyQt5 import QtWidgets  # type: ignore

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rag_project.rag_gui.core.main_window import ManualIngestionGUI  # noqa: E402
from rag_project.logger import get_logger  # noqa: E402


logger = get_logger(__name__)


def main():
    logger.info("Starting Ingestion & Retrieval GUI")
    app = QtWidgets.QApplication(sys.argv)
    ui = ManualIngestionGUI()
    ui.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
