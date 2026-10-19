import pytest

from src import config
from src.chunking import (
    build_chunks,
    split_text,
    split_text_by_sentences,
    split_text_with_overlap,
)
from src.corpus import load_corpus


def test_split_text_with_overlap_returns_multiple_chunks() -> None:
    text = "abcdefghijklmnopqrstuvwxyz" * 4
    chunks = split_text_with_overlap(text, chunk_size=30, overlap=10)
    assert len(chunks) >= 3


def test_split_text_with_overlap_rejects_invalid_overlap() -> None:
    with pytest.raises(ValueError):
        split_text_with_overlap("abc", chunk_size=10, overlap=10)


def test_sentence_boundaries_and_whitespace_are_normalized() -> None:
    text = "  First sentence.\nSecond question?\tThird exclamation!  "

    assert split_text_by_sentences(text, chunk_size=16) == [
        "First sentence.",
        "Second question?",
        "Third exclamation!",
    ]


def test_sentence_splitter_greedily_packs_consecutive_sentences() -> None:
    assert split_text_by_sentences("One. Two. Three.", chunk_size=9) == [
        "One. Two.",
        "Three.",
    ]


def test_sentence_splitter_accepts_chunk_at_exact_size_limit() -> None:
    chunks = split_text_by_sentences("One. Two.", chunk_size=9)

    assert chunks == ["One. Two."]
    assert len(chunks[0]) == 9


def test_sentence_splitter_moves_overflowing_sentence_to_next_chunk() -> None:
    assert split_text_by_sentences("One. Two. Three.", chunk_size=10) == [
        "One. Two.",
        "Three.",
    ]


def test_sentence_splitter_preserves_oversized_sentence_intact() -> None:
    oversized = "This sentence is longer than ten characters."

    assert split_text_by_sentences(f"{oversized} Tiny.", chunk_size=10) == [
        oversized,
        "Tiny.",
    ]


@pytest.mark.parametrize("text", ["", "   ", "\t", "\n\n"])
def test_sentence_splitter_returns_empty_for_blank_input(text: str) -> None:
    assert split_text_by_sentences(text) == []


@pytest.mark.parametrize("chunk_size", [0, -1])
def test_sentence_splitter_rejects_nonpositive_chunk_size(chunk_size: int) -> None:
    with pytest.raises(ValueError, match="chunk_size must be > 0"):
        split_text_by_sentences("Sentence.", chunk_size=chunk_size)


def test_sentence_splitter_preserves_trailing_fragment_without_punctuation() -> None:
    assert split_text_by_sentences("One. Final fragment", chunk_size=5) == [
        "One.",
        "Final fragment",
    ]


def test_punctuation_without_following_whitespace_is_not_a_boundary() -> None:
    assert split_text_by_sentences("One.Two.", chunk_size=20) == ["One.Two."]


def test_sentence_splitter_preserves_normalized_content_and_order() -> None:
    text = "  Alpha.  Beta?\nGamma!\tTail  "
    chunks = split_text_by_sentences(text, chunk_size=12)

    assert chunks == ["Alpha. Beta?", "Gamma! Tail"]
    assert " ".join(chunks) == " ".join(text.split())


def test_sentence_splitter_is_deterministic() -> None:
    text = "Alpha. Beta? Gamma! Tail"

    first = split_text_by_sentences(text, chunk_size=12)
    second = split_text_by_sentences(text, chunk_size=12)

    assert first == second


def test_sentence_strategy_is_active_and_used_by_dispatcher() -> None:
    assert config.CHUNK_STRATEGY == "sentences"
    assert split_text("One. Two.") == split_text_by_sentences(
        "One. Two.", chunk_size=config.CHUNK_SIZE
    )


def test_build_chunks_uses_stable_ids_and_keeps_metadata() -> None:
    chunks = build_chunks(load_corpus())
    ids = [chunk.chunk_id for chunk in chunks]
    assert len(ids) == len(set(ids))
    first = chunks[0]
    assert first.chunk_id == f"{first.doc_id}-chunk-0"
    assert first.version and first.status in {"current", "superseded"}
