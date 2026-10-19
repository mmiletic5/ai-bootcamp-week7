# M1 change specification: sentence-aware chunking

## Status and scope

This is Mateja Miletic's pre-implementation contract for exactly one change intention, M1 from [the improvement menu](improvement-menu.md): sentence-aware chunking. It is written before implementation and does not authorize unrelated changes.

## 1. Identified failure

The baseline at `results/before.json` shows E04 and E09 failing despite retrieval hits from expected document `hb-01`. The active character splitter creates overlapping 140-character chunks. The complete phrase `5 business days` is in `hb-01-chunk-1`, while each E04 and E09 top-2 result cites `hb-01-chunk-0` and `hb-01-chunk-2`. Therefore `fact_in_citations` is false. Details and reconstructed chunks are in [baseline-analysis.md](baseline-analysis.md).

This is evidence of a chunk-boundary condition combined with retrieval ranking: the relevant sentence is split, and the answer-bearing chunk is not in top-2. Current citation selection cites every retrieved chunk, so it does not independently remove chunk 1.

## 2. Hypothesis

Character-based chunking divides relevant textual evidence across chunks, reducing the likelihood that the complete answer-bearing sentence is retrieved and cited. Preserving sentence boundaries should help the RAG system retrieve complete evidence.

## 3. Proposed change

Isidora will implement `split_text_by_sentences(text, chunk_size=140)` in `src/chunking.py`, replacing only its present `NotImplementedError`. The splitter must:

- validate `chunk_size` consistently with `split_text_with_overlap` (`chunk_size <= 0` raises `ValueError`);
- normalize whitespace and return `[]` for empty text, as the existing splitter does;
- identify and preserve complete sentences where possible;
- group consecutive complete sentences into chunks whose normalized text is within `chunk_size`;
- emit an individual complete sentence that exceeds `chunk_size` as one oversized chunk rather than splitting it;
- use no overlap between sentence-aware chunks;
- retain document order and cover the normalized document content without dropping or duplicating sentences.

The existing `split_text()` dispatcher already invokes this function when `config.CHUNK_STRATEGY == "sentences"`. The future runtime activation is to change only the configuration value in `src/config.py` from `"chars"` to `"sentences"`; `CHUNK_SIZE` remains 140 and `CHUNK_OVERLAP` remains part of the available character strategy. The `"chars"` branch and `split_text_with_overlap()` must remain available unchanged.

`build_chunks()` must keep its existing `doc_id`-based `"{doc_id}-chunk-{i}"` IDs and metadata (`doc_id`, title, version, status, text). This splitter plus configuration activation is one logical M1 change: a new strategy cannot be evaluated without selecting it.

No retrieval scoring, top-k value, refusal threshold, citation logic, answer construction, corpus, evaluation set, or evaluator metric calculation may change.

## 4. Expected improvement (hypothesis only)

Primary targets are E04 and E09. Sentence-aligned chunks should make the complete replacement-timeframe sentence available as a coherent evidence unit. That may improve retrieval of `5 business days`, citation quality, and possibly transition E04 and/or E09 from FAIL to PASS. These are predictions, not measured achievements; only the required post-change evaluation can establish the result.

## 5. Regression risks and limitations

- Larger chunks can dilute lexical-match scores.
- Questions that currently pass can regress when chunk boundaries and scores change.
- Different boundaries can change retrieval ordering and chunk IDs, affecting citations.
- The top-k limit can still exclude useful evidence.
- Sentence-aware chunking does not solve the E05 synonym/paraphrase mismatch.
- It does not directly solve obsolete-policy selection in E06.
- Incorrect answers to unsupported E10/E11 questions can remain because refusal behavior is unchanged.
- It does not independently improve citation selection; it only changes the chunks supplied to retrieval.

## 6. Post-implementation verification plan (Isidora)

After implementation, Isidora must run, using the activated project environment:

```bash
python -m pytest -q
python -m src.eval_runner --out results/after.json
python -m src.eval_compare results/before.json results/after.json
```

If this environment still lacks a `python` executable, use the explicit virtual-environment interpreter and record that equivalent command. Confirm that `results/after.json` has the same `eval_set_sha256` as `results/before.json` (`afe46db1e75a0b85bb5c9a93b6763e3b96e5cd7b289e12da6d2671e4d8650064`); otherwise comparison is invalid. Preserve both JSON artifacts and the comparison output.

Inspect the comparison's fixed, regressed, unchanged lists, metric deltas, and changed settings. Specifically compare E04/E09 `top_k`, cited chunks, fact-in-citations, citation precision, and pass state; also identify every regression rather than reporting only improvements. Inspect `src/config.py` and the post-run config snapshot to confirm the intended strategy activation, with no other runtime setting changes. Inspect the implementation diff and tests to verify the one-change rule: only the sentence splitter, its strategy selection/config activation, and directly necessary implementation tests should differ in behavior.

The team must manually verify at least one changed question later with `python -m src.cli --question "..." --show-retrieved`; that joint activity is pending and must report the displayed evidence and citations. The final report must retain remaining failures and limitations even if M1 improves targeted cases.
