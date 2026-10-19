# Week 7 RAG before/after report

## Assignment objective

Measure the existing RAG system on a frozen 12-question evaluation set, document concrete failures, apply exactly one controlled improvement, and measure the result without changing the questions or evaluator.

The controlled improvement was M1: replace fixed-character chunking as the active strategy with sentence-aware chunking. The experiment changed chunk construction only. Retrieval scoring, `TOP_K`, stopword behavior, version filtering, refusal and citation thresholds, answer generation, corpus content, evaluation questions, and metric calculations remained unchanged.

## Team responsibilities

- Mateja Miletic completed the original-state inspection, baseline tests and evaluation, preservation of `results/before.json`, failure analysis, and the pre-implementation M1 specification.
- Isidora Prica added the focused tests, implemented and activated sentence-aware chunking, performed integration and regression verification, generated `results/after.json`, and preserved the comparison output.
- Joint final review, external peer review, and the Session 2 demonstration lead remain pending.

## Baseline and motivating failures

The baseline used `CHUNK_STRATEGY="chars"`, `CHUNK_SIZE=140`, and `CHUNK_OVERLAP=30`. Text was normalized and divided at fixed character positions with 30-character overlap. The frozen evaluation contained E01-E12 and had SHA-256:

```text
afe46db1e75a0b85bb5c9a93b6763e3b96e5cd7b289e12da6d2671e4d8650064
```

Baseline evidence is stored in `results/before.json`, whose SHA-256 is:

```text
67732267cc9cece69d4eef5fb5c52815f7b2903e1fc5f7baa1128067ca43256e
```

The original suite produced 18 passing tests. The baseline evaluation passed 6 of 12 cases.

E04 and E09 motivated M1. Both expected the phrase `5 business days` from `hb-01`. Character chunking split the answer-bearing sentence so that only `hb-01-chunk-1` contained the complete phrase. The top-two results for both questions instead cited `hb-01-chunk-0` and `hb-01-chunk-2`. Retrieval found the expected document, but the cited chunks did not contain the required fact, so both cases failed.

Other baseline failures were:

- E05: the paraphrase “new notebook computer” did not retrieve `hb-01` or cite `5 business days`.
- E06: superseded `hb-02` chunks ranked above current `hb-03`, so the current `3 days per week` fact was absent.
- E10: the unsupported stock-price question was answered rather than refused.
- E11: the unsupported parental-leave question was answered from annual-leave chunks.

Detailed baseline evidence appears in [baseline-analysis.md](baseline-analysis.md), and the change was specified before implementation in [m1-change-spec.md](m1-change-spec.md).

## Single controlled change: M1 sentence-aware chunking

The implementation added `split_text_by_sentences(text, chunk_size=140)` and activated the existing sentence-strategy dispatcher by changing only `CHUNK_STRATEGY` from `"chars"` to `"sentences"`.

The splitter:

- rejects `chunk_size <= 0` with `ValueError("chunk_size must be > 0")`;
- normalizes all whitespace with `" ".join(text.split())` and returns `[]` for empty normalized input;
- detects boundaries with `re.split(r"(?<=[.!?])\s+", cleaned)`, retaining `.`, `?`, or `!` on the preceding sentence;
- treats spaces, tabs, and line breaks consistently because normalization occurs before boundary detection;
- greedily joins consecutive sentences with one space while their combined length is at most 140 characters;
- starts a new chunk when the next sentence would exceed the target;
- preserves a single sentence longer than 140 characters intact as an oversized chunk;
- uses no overlap and preserves sentence order and normalized content.

The original character splitter remains available and unchanged. Chunk construction still uses `"{doc_id}-chunk-{i}"` IDs and preserves document ID, title, version, status, and text metadata.

The before/after configuration snapshots confirm that `CHUNK_STRATEGY: chars -> sentences` was the only changed setting. This implementation plus activation is one logical change because the new splitter cannot be evaluated without selecting it.

## Implementation and verification

Production changes were limited to:

- `src/chunking.py`: sentence-aware splitter implementation and standard-library `re` import.
- `src/config.py`: activation of `CHUNK_STRATEGY="sentences"`.

Focused tests in `tests/test_chunking.py` cover `.`, `?`, and `!` boundaries; whitespace normalization; greedy and exact-size packing; overflow; oversized sentences; empty and invalid inputs; trailing fragments; punctuation without following whitespace; deterministic output; normalized content coverage; strategy activation; and existing chunk ID and metadata behavior.

Verified test results:

```text
Focused chunking tests: 19 passed in 0.04s
Full test suite:         34 passed in 0.15s
```

The read-only integration smoke check loaded 10 documents and generated 26 sentence-aware chunks with 26 unique IDs. It verified normalized document coverage, metadata preservation, active sentence dispatch, retrieval, supported-answer citations, and the refusal interface. In `hb-01`, the 163-character replacement-timeframe sentence remained intact as an intentionally oversized chunk containing `5 business days`.

These checks demonstrate implementation correctness and pipeline compatibility. RAG quality is established separately by the fixed evaluation results below.

## Before/after metrics

| Metric | Before | After | Delta |
| --- | ---: | ---: | ---: |
| Passing cases | 6/12 | 9/12 | +3 |
| Behaviour accuracy | 0.8333 | 0.8333 | 0.0000 |
| Retrieval hit rate | 0.7778 | 0.8889 | +0.1111 |
| Mean citation precision | 0.4545 | 0.5455 | +0.0910 |

The measured result supports the M1 hypothesis for E04 and E09. It also produced a measured improvement for E06. Behaviour accuracy did not change because E10 and E11 still answered unsupported questions, while the newly fixed supported cases already had correct answer behavior before M1.

## Per-question results

| ID | Before | After | Evidence-based finding |
| --- | --- | --- | --- |
| E01 | PASS | PASS | No measured metric change. |
| E02 | PASS | PASS | No measured metric change. |
| E03 | PASS | PASS | Citation precision improved from 0.5 to 1.0. After M1, both cited chunks came from `hb-08`. |
| E04 | FAIL | PASS | `fact_in_citations` changed from false to true. After M1, top-two cited `hb-01-chunk-1` and `hb-01-chunk-0`; chunk 1 contains the complete `5 business days` sentence. |
| E05 | FAIL | FAIL | Retrieval still missed `hb-01`; retrieval hit, fact evidence, and citation precision remained false, false, and 0.0. |
| E06 | FAIL | PASS | Retrieval hit and fact evidence changed from false to true, and precision improved from 0.0 to 0.5. After M1, current `hb-03-chunk-0` ranked first and supplied `3 days per week`; superseded `hb-02-chunk-0` remained second. |
| E07 | PASS | PASS | No measured metric change. |
| E08 | PASS | PASS | No measured metric change. |
| E09 | FAIL | PASS | `fact_in_citations` changed from false to true. After M1, top-two cited `hb-01-chunk-2` for the request location and `hb-01-chunk-1` for `5 business days`. |
| E10 | FAIL | FAIL | The unsupported question was still answered; behavior remained incorrect and precision remained 0.0. |
| E11 | FAIL | FAIL | The unsupported near-domain question was still answered; behavior remained incorrect and precision remained 0.0. |
| E12 | PASS | PASS | Correct refusal remained unchanged. |

Fixed cases were E04, E06, and E09. No case moved from PASS to FAIL. Comparing behavior correctness, retrieval hit, fact-in-citations, and citation precision found no observed metric-level regression. E05, E10, and E11 remain unresolved.

## Limitations and remaining risks

- E05 demonstrates that sentence boundaries do not solve the lexical synonym gap between “notebook computer” and “laptop replacement.”
- E10 and E11 demonstrate that refusal calibration remains weak. M1 did not change refusal thresholds.
- The lightweight boundary rule treats punctuation followed by whitespace as a boundary. It can incorrectly split abbreviations such as `Dr. Smith` and is not a full linguistic sentence tokenizer.
- Intact oversized sentences can exceed the 140-character target and dilute lexical scores. The `hb-01` answer-bearing sentence is 163 characters.
- Changed boundaries alter chunk indexes, score denominators, retrieval order, and citations. The current fixed set showed no regression, but other questions may behave differently.
- The evaluation contains only 12 questions over a small fictional handbook. Results should not be generalized to other corpora, languages, punctuation conventions, or query distributions without further testing.
- The experiment demonstrated improvements for E04, E06, and E09 on this fixed set. It did not test abbreviation handling, broader corpora, semantic retrieval, threshold changes, or other advanced techniques.

## Reproducibility and preserved evidence

Commands used on Isidora's Windows environment:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_chunking.py -q
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m src.eval_runner --out results/after.json
.\.venv\Scripts\python.exe -m src.eval_compare results/before.json results/after.json
```

Evidence:

- Baseline: `results/before.json`
- Post-change evaluation: `results/after.json`
- Preserved comparison output: `results/comparison.txt`
- Evaluation fingerprint in both JSON artifacts: `afe46db1e75a0b85bb5c9a93b6763e3b96e5cd7b289e12da6d2671e4d8650064`
- Post-change artifact SHA-256: `8257be8b40d0f5762b565d8707e4d97e36ce16abf8860aa4d005ba32f478b82f`
- Comparison artifact SHA-256: `d85f43b120f082acc0d9d15e7bbf9a4d7c5e4168bc453d9864846c5bea682813`

Git for Windows initially checked the tracked JSON files out with CRLF endings because the system configuration had `core.autocrlf=true`. The canonical committed LF bytes produced the recorded fingerprints. The repository-local setting was changed to `core.autocrlf=false`, the index stat cache was refreshed, and subsequent verification confirmed LF working-tree bytes identical to the index blobs. System and global Git configuration were not changed.

The environments were similar but not identical: Mateja recorded Python 3.10.12 for the baseline, Isidora used Python 3.10.0 for implementation and post-change verification, and the README targets Python 3.12. Both recorded test suites passed, but the report does not claim exact interpreter parity.

## AI-assistance disclosure

Codex assisted with repository inspection, implementation planning, focused test drafting, the sentence-splitter implementation, command execution, integrity diagnosis, evaluation comparison, and report drafting. Mateja and Isidora retained checkpoint approval and review responsibility. Claims were checked against source code, Git diffs and status, test output, fixed evaluation JSON artifacts, their hashes, and the repository comparison tool. AI output was not treated as evaluation evidence; the saved before/after artifacts and unchanged evaluator provide that evidence.

## Manual CLI verification

The changed E04 question was manually inspected with:

```powershell
.\.venv\Scripts\python.exe -m src.cli --question "How many business days does a laptop replacement take?" --show-retrieved
```

The command exited with code 0 and returned an answer rather than a refusal (`Refused: False`). It retrieved and cited both `hb-01-chunk-1` at 0.2069 and `hb-01-chunk-0` at 0.2000. `hb-01-chunk-1` explicitly states that laptop handover can take up to `5 business days`. The displayed answer is supported by the retrieved evidence and agrees with the E04 PASS result in `results/after.json`.

## Pending team and submission work

The following requirements are not yet supported by completed evidence and remain pending:

- Mateja and Isidora jointly review the complete diff and confirm the one-change rule.
- Obtain the assigned external pair's review comment addressing whether the change is one controlled change, whether the evidence supports the conclusion, and whether any regression or limitation was omitted.
- Perform the reciprocal review of the assigned pair as required by the course process.
- Confirm and record the Session 2 demonstration lead.
- Prepare commit or diff evidence. Before every commit, verify the staged file list and summary, run `git diff --cached --check`, show the exact message, confirm Isidora as author, and confirm Mateja's exact co-author address.
- Ensure both team members submit the same report and required evidence through the official delivery process.

No peer review, joint final conclusion, commit, submission, or demonstration ownership is claimed complete in this report.
