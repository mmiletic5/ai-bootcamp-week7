# Week 7 baseline analysis

## Purpose and ownership

This document records Mateja Miletic's reproducible pre-implementation baseline for the Week 7 RAG checkpoint. It is evidence for the proposed M1 sentence-aware chunking change; it does not report any post-change outcome.

## Execution record

- Date: 2026-10-19.
- Repository state before baseline work: clean `main` branch at `11ade1a4cfe9d673c4e8b5c2d0fd38fe46097968` (`Initial commit`).
- Python: 3.10.12. The README specifies Python 3.12, but that interpreter was not available locally.
- Environment: a project-local `.venv` was created and populated with the pinned `pytest==8.3.3` requirement. The shell did not provide a `python` executable, so the equivalent explicit commands below were used.
- Tests: `.venv/bin/python -m pytest -q` — 18 passed, 0 failed, in 0.13 s.
- Evaluation: `.venv/bin/python -m src.eval_runner --out results/before.json`.

`results/before.json` did not exist before the run. It is ignored by `.gitignore` (`results/*.json`) and is preserved as baseline evidence. Its file SHA-256 after creation was `67732267cc9cece69d4eef5fb5c52815f7b2903e1fc5f7baa1128067ca43256e`.

## Fixed-evaluation identity and initial configuration

The evaluator executed all 12 entries (E01–E12) in `eval/eval_set.json`. Its evaluation-set fingerprint was:

`afe46db1e75a0b85bb5c9a93b6763e3b96e5cd7b289e12da6d2671e4d8650064`

This matches the supplied reference fingerprint. The captured initial runtime configuration was:

```text
CHUNK_STRATEGY="chars"; CHUNK_SIZE=140; CHUNK_OVERLAP=30
TOP_K=2; RETRIEVAL_MIN_SCORE=0.01; STOPWORDS_ENABLED=false; CURRENT_ONLY=false
REFUSAL_THRESHOLD=0.02; CITATION_MIN_SCORE=null
```

The implementation confirms that `split_text()` uses `split_text_with_overlap()` for this configuration. The sentence splitter exists only as an intentional `NotImplementedError`; it was not enabled or implemented in this baseline.

## Baseline metrics

| Metric | Measured result |
| --- | ---: |
| Passing evaluation cases | 6/12 |
| Failing evaluation cases | 6/12 |
| Behaviour accuracy | 0.8333 |
| Retrieval hit rate (supported questions) | 0.7778 |
| Mean citation precision (answered questions) | 0.4545 |

## Per-question baseline results

| ID | Status | Measured result and concise diagnosis |
| --- | --- | --- |
| E01 | PASS | Answered; fact cited from `hb-07-chunk-0`; citation precision 0.50 due to additional `hb-02-chunk-0`. |
| E02 | PASS | Answered; fact cited from `hb-05-chunk-0`; citation precision 0.50 due to additional `hb-02-chunk-1`. |
| E03 | PASS | Answered; fact cited from `hb-08-chunk-0`; citation precision 0.50 due to additional `hb-02-chunk-0`. |
| E04 | FAIL | Correct behaviour and expected-document hit, but citations `hb-01-chunk-0` and `hb-01-chunk-2` omit `5 business days`. |
| E05 | FAIL | Answered but retrieved `hb-06-chunk-0` and `hb-07-chunk-1`, not expected `hb-01`; the paraphrase did not retrieve the timeframe. |
| E06 | FAIL | Answered with superseded-policy chunks `hb-02-chunk-0` and `hb-02-chunk-1`, not current expected `hb-03`; expected fact absent. |
| E07 | PASS | Answered; both cited chunks are from `hb-10`, and the support-hours fact is cited. |
| E08 | PASS | Answered; fact cited from `hb-04-chunk-0`; citation precision 0.50 due to additional `hb-03-chunk-2`. |
| E09 | FAIL | Correct behaviour and expected-document hit, but citations `hb-01-chunk-0` and `hb-01-chunk-2` omit `5 business days`. |
| E10 | FAIL | Unsupported question was answered from low-score chunks `hb-09-chunk-1` and `hb-05-chunk-1`: incorrect refusal. |
| E11 | FAIL | Unsupported-near-domain question was answered from `hb-07-chunk-1` and `hb-07-chunk-0`: incorrect refusal. |
| E12 | PASS | Unsupported question correctly refused; no chunks retrieved or cited. |

## Detailed E04 investigation

**Expected evidence.** E04 asks “How many business days does a laptop replacement take?”, expects an answer from `hb-01`, and requires the fact `5 business days` in a cited chunk.

**Source and reconstructed baseline chunks.** The original `hb-01` text contains the sentence “After manager approval, a replacement laptop is set up by IT staff with your files, accounts, email and access rights, and handover can take up to 5 business days.” Reconstructing the active `split_text_with_overlap(text, chunk_size=140, overlap=30)` yielded:

```text
hb-01-chunk-0: Laptop replacement: broken, lost or stolen laptops can be replaced. After manager approval, a replacement laptop is set up by IT staff with
hb-01-chunk-1: op is set up by IT staff with your files, accounts, email and access rights, and handover can take up to 5 business days. Report lost or sto
hb-01-chunk-2: iness days. Report lost or stolen devices to security first. Request a replacement laptop in IT portal under Hardware. Accessories such as m
```

Only `hb-01-chunk-1` contains the complete expected phrase `5 business days`; chunk 2 contains only the overlap fragment `iness days`.

**Observed evaluation evidence.** E04 was answered, had a retrieval hit, and cited `hb-01-chunk-0` (score 0.217391) and `hb-01-chunk-2` (score 0.173913). Citation precision was 1.0 because both chunks belong to the expected document, but `fact_in_citations=false`; therefore the case failed.

**Classification and interpretation.** The measured failure is a citation-evidence failure. Its contributing chunking condition is the character cut through the answer-bearing sentence: only chunk 1 has the complete fact. It is also a retrieval-ranking outcome: top-2 selected chunks 0 and 2 rather than chunk 1. Citation selection merely cites all retrieved results under the current configuration, so it cannot recover the omitted evidence. This run demonstrates the problem; it does not prove a future sentence strategy will fix E04.

## Detailed E09 investigation

**Expected evidence.** E09 asks “Where do I request a replacement laptop and how long does it take?”, expects `hb-01`, and requires `5 business days` in cited evidence. The source also says: “Request a replacement laptop in IT portal under Hardware.”

**Observed evaluation evidence.** E09 was answered, had a retrieval hit, and cited `hb-01-chunk-0` (score 0.260870) and `hb-01-chunk-2` (score 0.217391). As in E04, citation precision was 1.0 but `fact_in_citations=false`. Chunk 2 supports the request location, whereas the complete timeframe is in omitted `hb-01-chunk-1`.

**Classification and interpretation.** The failed requirement is citation evidence for the timeframe. The same character-boundary condition puts the complete phrase only in chunk 1, while the top-2 ranking returns chunks 0 and 2. The current citation routine returns all retrieved chunks, so the direct failure mechanism is not a citation filter. E09 provides evidence for a chunking-plus-retrieval-ranking interaction, not confirmation that a sentence-aware change will pass it.

## Other failures and known weaknesses

- **E05 — retrieval / incorrect answer evidence:** Expected `hb-01` and `5 business days`; actual top-2 was `hb-06-chunk-0` (0.153846) and `hb-07-chunk-1` (0.083333), with retrieval hit false and citation precision 0.0. Interpretation: lexical scoring does not bridge “new notebook computer” to the laptop-replacement evidence. Sentence-aware chunking alone is not designed to solve that synonym/paraphrase gap.
- **E06 — retrieval / incorrect answer evidence:** Expected current `hb-03` and `3 days per week`; actual top-2 was superseded `hb-02-chunk-0` (0.481481) and `hb-02-chunk-1` (0.4), with retrieval hit false. Interpretation: no current-version filter is active (`CURRENT_ONLY=false`), so lexical ranking prefers obsolete material; M1 does not directly address policy currency.
- **E10 — incorrect refusal evidence:** The unsupported stock-price question was answered because the best score, 0.058824, exceeded the 0.02 refusal threshold. Interpretation: weak token overlap is enough to avoid refusal under the current threshold.
- **E11 — incorrect refusal evidence:** The unsupported parental-leave question was answered from annual-leave chunks with scores 0.166667 and 0.16. Interpretation: near-domain lexical overlap causes a grounded-looking but unsupported answer.

The passing E01, E02, E03, and E08 cases each have citation precision exactly 0.50, showing that top-2 citation padding already lowers precision even when the required fact is present.

## Measured facts versus future hypothesis

Measured facts are the JSON artifact, source text, active configuration, chunk reconstruction, scores, and outcomes above. The suspected common root cause for E04/E09 is character-based fragmentation of a sentence plus the resulting top-2 ranking that omits the chunk with the complete timeframe. M1 hypothesizes that retaining complete sentences will improve the available retrieval evidence for those two questions. No post-change run, comparison, implementation review, or manual CLI verification has occurred, so no improvement is claimed.
