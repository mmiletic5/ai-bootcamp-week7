# Week 7 RAG checkpoint

A small local question-answering tool over a fictional employee handbook. It retrieves relevant text chunks, produces grounded answers with chunk citations, and refuses questions when appropriate evidence is unavailable. It runs offline and requires no API keys, network access, or paid services.

We implemented one controlled RAG improvement, M1 sentence-aware chunking, and measured it before and after on the same fixed 12-question evaluation set.

## Setup

The project target is Python 3.12. The completed verification also ran successfully on Python 3.10.x. No external API key or paid service is required.

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Commands

Run commands from an activated virtual environment.

| Task | Command |
| --- | --- |
| Supported CLI question | `python -m src.cli --question "How often do passwords need to be changed?"` |
| Show retrieved chunks and lexical scores | `python -m src.cli --question "How many business days does a laptop replacement take?" --show-retrieved` |
| Full test suite | `python -m pytest -q` |
| Focused sentence-chunking tests | `python -m pytest tests/test_chunking.py -q` |
| Alternative full test runner (Linux/macOS) | `./scripts/run_tests.sh` |
| Compare preserved baseline and post-change results | `python -m src.eval_compare results/before.json results/after.json` |

`--show-retrieved` prints the retrieved chunk IDs, text, and scores in addition to the answer and citations. The completed project has **34 passing tests** with `python -m pytest -q`.

Other focused test modules are available when investigating a specific subsystem:

```bash
python -m pytest tests/test_retrieval.py -q
python -m pytest tests/test_rag.py -q
python -m pytest tests/test_eval_metrics.py -q
python -m pytest tests/test_eval_compare.py -q
python -m pytest tests/test_eval_set.py -q
```

### Evaluation

The following is the **historical baseline command** that produced the character-chunking artifact. Do not run it against the current sentence-aware configuration, because it would overwrite baseline evidence:

```bash
python -m src.eval_runner --out results/before.json
```

Likewise, preserve the recorded post-change artifact rather than overwriting it:

```bash
python -m src.eval_runner --out results/after.json
```

To reproduce the current sentence-aware evaluation safely, write to a new local file instead:

```bash
python -m src.eval_runner --out results/local-check.json
```

`results/before.json` and `results/after.json` are preserved comparison artifacts. The comparison command reports improved questions, regressions, unchanged questions, metric differences, and configuration differences:

```bash
python -m src.eval_compare results/before.json results/after.json
```

## Project layout

- `src/config.py`: centralized runtime settings; the active strategy is `CHUNK_STRATEGY="sentences"`.
- `src/corpus.py`: ten fictional handbook documents with title, section, version, and status.
- `src/chunking.py`: original character-overlap splitter and the active sentence-aware splitter.
- `src/retrieval.py`: lexical retrieval over chunks.
- `src/rag.py`: grounded-answer construction, citations, and refusal behavior.
- `src/cli.py`: command-line question interface with optional retrieved-context display.
- `src/eval_runner.py`: fixed-set evaluation and JSON artifact generation.
- `src/eval_compare.py`: before/after comparison with metric and configuration deltas.
- `eval/eval_set.json`: the unchanged 12-question evaluation set.
- `tests/`: unit and evaluation-mechanics tests.
- `docs/improvement-menu.md`: original one-change improvement menu.
- `docs/baseline-analysis.md`: pre-M1 baseline and failure analysis.
- `docs/m1-change-spec.md`: the pre-implementation M1 contract.
- `docs/week7-before-after-report.md`: completed technical report and joint conclusion.
- `results/before.json`, `results/after.json`, `results/comparison.txt`: preserved evaluation evidence.

## Metrics

| Column | Meaning |
| --- | --- |
| `Hit` | For questions that should be answered, at least one retrieved chunk comes from an expected document. |
| `Fact` | The expected fact appears in at least one cited chunk. |
| `CitPrec` | Cited chunks from expected documents divided by all cited chunks; 0.00 when an unsupported question is answered. |
| `Pass` | Correct answer/refusal behaviour and, for answered questions, a cited expected fact with `CitPrec` of at least 0.50. |

## Week 7 — Implemented improvement and results

M1 introduced sentence-aware chunking as the single intentional RAG behavior change. Sentence mode preserves complete sentences where possible, greedily groups consecutive sentences within the target chunk size, keeps oversized sentences intact, and uses no overlap. It retains the existing chunk-ID and metadata conventions, while the original character-based splitter remains available.

The active strategy changed from `CHUNK_STRATEGY="chars"` to `CHUNK_STRATEGY="sentences"`. Retrieval scoring, top-k, refusal and citation behavior, corpus content, evaluation set, and evaluator metrics were not intentionally changed.

| Metric | Before | After |
| --- | ---: | ---: |
| Passing evaluation cases | 6/12 | 9/12 |
| Behaviour accuracy | 0.8333 | 0.8333 |
| Retrieval hit rate | 0.7778 | 0.8889 |
| Mean citation precision | 0.4545 | 0.5455 |

**Improved questions:** E04, E06, E09

**Remaining failures:** E05, E10, E11

**Regressions:** No PASS-to-FAIL regressions observed on the fixed evaluation set.

E04 and E09 were the original M1 targets; E06 was an additional observed improvement. These results support sentence-aware chunking for this checkpoint, but do not mean it solves all retrieval, citation, paraphrase, version-selection, or unsupported-question limitations.

## Reproducibility and evidence

The historical baseline, post-change evaluation, and comparison output are preserved in `results/before.json`, `results/after.json`, and `results/comparison.txt`. `.gitignore` still ignores newly generated `results/*.json` files, but these official before/after artifacts were explicitly tracked and committed as assignment evidence.

For the complete methods, limitations, integration audit, and shared conclusion, see [docs/week7-before-after-report.md](docs/week7-before-after-report.md).
