import math

from rag_project.rag_core.ingestion.chunker import chunk_text, split_into_sentences


def test_chunker_split_preserves_decimals_and_sentences():
    text = "Price is 1.6 euros. Next sentence starts. Version 2.0 is stable! New line?\nAnother line."
    sentences = split_into_sentences(text)
    assert "1.6 euros." in sentences[0]
    assert any(s.startswith("Next sentence") for s in sentences)
    assert any("Version 2.0" in s for s in sentences)


def test_chunker_respects_overlap_and_token_budget():
    # ~80 words, should produce multiple chunks with 25% overlap
    base_sentence = (
        "This is a moderately long sentence that we repeat to fill the buffer."
    )
    text = " ".join([base_sentence for _ in range(40)])
    chunks = chunk_text(text, max_tokens=50, overlap_tokens=12)
    assert len(chunks) > 1
    # Check overlap between consecutive chunks by word slices
    for i in range(len(chunks) - 1):
        prev_words = chunks[i].split()
        next_words = chunks[i + 1].split()
        overlap = len(set(prev_words[-12:]) & set(next_words[:12]))
        assert overlap >= 6  # allow some drift but expect meaningful overlap
        assert len(prev_words) <= 60  # slight tolerance over 50 target


def test_chunker_returns_no_empty_chunks():
    chunks = chunk_text("", max_tokens=10, overlap_tokens=2)
    assert chunks == []

    single = chunk_text("Short text.", max_tokens=10, overlap_tokens=2)
    assert len(single) == 1
    assert single[0].strip() != ""


def test_chunker_handles_very_short_text_single_chunk():
    text = "Tiny"
    chunks = chunk_text(text, max_tokens=5, overlap_tokens=2)
    assert chunks == [text]


def test_chunker_handles_exact_chunk_size_without_overlap():
    text = " ".join(["word" for _ in range(10)])
    chunks = chunk_text(text, max_tokens=10, overlap_tokens=0)
    assert len(chunks) == 1
    assert chunks[0].split() == text.split()


def test_chunker_handles_long_text_without_character_loss():
    text = " ".join(["longline" * 3 for _ in range(200)])
    chunks = chunk_text(text, max_tokens=40, overlap_tokens=8)
    assert len(chunks) >= 1
    recombined = " ".join(chunks)
    for token in set(text.split()[:20]):
        assert token in recombined


def test_chunker_handles_minimal_punctuation_and_long_lines():
    text = " ".join(["averyveryverylongword" for _ in range(120)])
    chunks = chunk_text(text, max_tokens=30, overlap_tokens=5)
    assert len(chunks) >= 1
    assert all(chunk.strip() for chunk in chunks)


def test_chunker_handles_unicode_and_emoji():
    text = "こんにちは 世界 😊. これはテストです！ Another sentence."
    chunks = chunk_text(text, max_tokens=12, overlap_tokens=3)
    assert any("😊" in c for c in chunks)
    assert any("こんにちは" in c for c in chunks)


def test_chunker_parse_and_chunk_pipeline_covers_all_characters(tmp_path):
    source_text = (
        "Line one.\nLine two with emoji 😊.\nLast line to cover chunk overlap."
    )
    txt_path = tmp_path / "pipeline.txt"
    txt_path.write_text(source_text, encoding="utf-8")
    loaded = txt_path.read_text(encoding="utf-8")
    chunks = chunk_text(loaded, max_tokens=8, overlap_tokens=2)

    combined = " ".join(chunks)
    for ch in set(source_text.replace("\n", " ").strip()):
        assert ch in combined
