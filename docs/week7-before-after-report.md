# Week 7 RAG before/after report (draft)

## Assignment objective

Measure a fixed 12-question RAG evaluation set, apply exactly one controlled improvement, and compare the baseline against the post-change result without changing the evaluation set.

## Team and responsibility split

- Mateja Miletic: original-state inspection, pre-change tests and evaluation, baseline artifact, failure analysis, M1 specification, and baseline/report preparation.
- Isidora Prica: sentence-aware chunking implementation and configuration activation, implementation-related tests, post-change tests/evaluation, `results/after.json`, and preserved comparison output.

## Baseline methodology and environment

Mateja inspected the original repository on 2026-10-19, confirmed the active character strategy (`CHUNK_STRATEGY="chars"`, `CHUNK_SIZE=140`, `CHUNK_OVERLAP=30`), and ran all existing tests before implementation. Python 3.10.12 was available; the README's Python 3.12 target was not. Since no `python` command existed, a local `.venv` used equivalent explicit commands:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m src.eval_runner --out results/before.json
```

The tests produced 18 passed, 0 failed. The evaluator ran all E01–E12 entries and recorded eval-set SHA-256 `afe46db1e75a0b85bb5c9a93b6763e3b96e5cd7b289e12da6d2671e4d8650064`. See [baseline-analysis.md](baseline-analysis.md) and `results/before.json`.

## Baseline metrics

| Metric | Baseline |
| --- | ---: |
| Pass cases | 6/12 |
| Behaviour accuracy | 0.8333 |
| Retrieval hit rate | 0.7778 |
| Mean citation precision | 0.4545 |

## Baseline failure analysis

### E04

E04 required `5 business days` from `hb-01`. The character splitter put the full phrase only in `hb-01-chunk-1`; top-2 cited `hb-01-chunk-0` and `hb-01-chunk-2` (scores 0.217391 and 0.173913). Behaviour was correct and the document hit, but the required fact was absent from citations, so the case failed.

### E09

E09 required both the IT portal/Hardware request location and `5 business days`. Top-2 again cited chunks 0 and 2 (scores 0.260870 and 0.217391). Chunk 2 contains the request location, but the full timeframe is only in omitted chunk 1; the case failed on `fact_in_citations=false`.

### Other baseline failures

- E05: expected `hb-01`, but lexical retrieval selected `hb-06-chunk-0` and `hb-07-chunk-1`; a paraphrase/synonym retrieval failure.
- E06: expected current `hb-03`, but superseded `hb-02` chunks ranked first; a version-selection retrieval failure.
- E10: unsupported stock-price question was answered from weak matches; incorrect refusal.
- E11: unsupported parental-leave question was answered from annual-leave chunks; incorrect refusal.

## M1 hypothesis and expected effects

M1 is sentence-aware chunking, specified before implementation in [m1-change-spec.md](m1-change-spec.md). Its hypothesis is that keeping complete sentences together will make complete replacement-timeframe evidence more retrievable and citable for E04/E09. Potentially those cases can improve, including citation quality. This is not an observed post-change result.

## Predicted regression risks

Chunk sizes, lexical scores, ordering, chunk IDs, and citations can all change; previously passing questions can regress; top-k can still omit helpful evidence. M1 does not directly solve E05 paraphrase matching, E06 obsolete-policy selection, or E10/E11 unsupported-answer behavior.

## Mateja's contribution

Mateja completed the original-state inspection, pre-change tests, baseline evaluation and evidence preservation, E04/E09 and other baseline-failure analysis, the M1 specification, this draft, and the handoff. No application implementation, test modification, post-change evaluation, or implementation review was performed in this phase.

## Preliminary AI-assistance disclosure (baseline phase)

Codex assistance was used to inspect repository files, create the local environment, execute the pre-change tests and evaluator, reconstruct chunks by calling the existing splitter, and draft these documents. Mateja's recorded claims were checked against the command output, generated baseline JSON, source code, fixed evaluation set, and Git status. The assistant did not implement M1 or run post-change evaluation.

## Pending: Isidora implementation summary

Not yet performed or supplied.

## Pending: actual implementation diff

Not yet implemented or reviewed.

## Pending: post-change evaluation and after metrics

Not yet run; `results/after.json` has not been created in this phase.

## Pending: comparison output, fixed questions, and actual regressions

Not yet run or analyzed.

## Pending: remaining post-change limitations and manual CLI verification

Not yet performed. A joint CLI verification of a changed question remains required.

## Pending: joint final conclusions and external peer review

Not yet prepared or received.

## Pending: Session 2 demonstration lead

No lead has been confirmed.
