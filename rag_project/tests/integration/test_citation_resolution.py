from PyQt5 import QtCore  # type: ignore

from rag_project.rag_gui.widgets.rag.chat_area import ChatArea


def test_citation_marker_resolves_to_correct_chunk(qtbot):
    app = type("DummyApp", (), {})()
    chat = ChatArea(app, parent=None)

    citations = [
        {"label": 1, "content": "Evidence A", "doc_type": "cv", "doc_id": "d1", "chunk_id": "c1"},
        {"label": 2, "content": "Evidence B", "doc_type": "cv", "doc_id": "d2", "chunk_id": "c2"},
    ]

    received = []
    chat.context_requested.connect(lambda sources: received.append(sources))

    bubble = chat.add_message("Verdict [1][2]", is_user=False, citations=citations)

    qtbot.wait(10)
    bubble.citation_clicked.emit("2")

    assert received
    assert received[0][0]["content"] == "Evidence B"
