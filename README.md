# Effect of Prompt Phrasing on LLMs: A Pilot Study of SAT-Style Question Formatting

Dylan Santwani · pilot data collected February 2025 · revised October 2026 · [PDF](effect-of-prompt-phrasing-on-llms.pdf)

Does a question written like an SAT item get a clearer worked solution than the same question written as plain prose? Four models (GPT-4o, DeepSeek-R1, Qwen2.5 72B, Llama 3 70B) answered two released SAT items, an algebra word problem and a reading item, in their original form and as a Gemini paraphrase. Each of the 16 responses was hand-scored out of 18.

## Findings

| | Q1 algebra, original | Q1 algebra, rewritten | Q2 reading, original | Q2 reading, rewritten |
|---|---|---|---|---|
| GPT-4o | 16 | 14 | 18 | 17 |
| DeepSeek-R1 | 16 | 15 | 17 | 17 |
| Qwen2.5 72B | 18 | 15 | 17 | 16 |
| Llama 3 70B | 17 | 13 | 16 | 16 |
| Mean | 16.75 | 14.25 | 17.00 | 16.50 |

- Every response was correct, so the differences are in how clear the explanations were, not in accuracy.
- On the algebra item, all four models scored lower on the rewrite, and 80% of the drop was in clarity. On the reading item, two models did not change.
- With four paired observations per item, the algebra result is not statistically significant: the exact one-sided p = 0.0625 is the smallest value four pairs can produce.
- The algebra rewrite changed far more wording than the reading rewrite. That alone could explain the difference between the two items, and the paper sets out this and five other confounds.

The paper treats this as a pilot. It specifies a confirmatory study (426 AGIEval SAT items plus newly written items, five conditions that separate layout, wording, memorization and image input, and blind scoring with measured inter-rater agreement) and an evaluation plan for the small-model question-rewriting pipeline the hypothesis suggests.

## Repository

| Path | Contents |
|---|---|
| `effect-of-prompt-phrasing-on-llms.pdf` | The current paper |
| `paper/` | LaTeX source, bibliography, generated figures and tables |
| `analysis/analyze.py` | Computes every number, table and data figure from the scores |
| `data/scores.csv` | Hand scores for all 16 responses |
| `v1/` | The original February 2025 version and its charts |

## Rebuild

Needs Python 3 with numpy, scipy and matplotlib, and [Tectonic](https://tectonic-typesetting.github.io/).

```bash
make
```

This regenerates `paper/figures/` and `paper/generated/` from `data/scores.csv` and then compiles the PDF. The prose reads its statistics from `paper/generated/stats.tex`, so the text cannot drift from the data.

## Citation

```bibtex
@misc{santwani2026phrasing,
  title  = {Effect of Prompt Phrasing on {LLMs}: A Pilot Study of {SAT}-Style Question Formatting},
  author = {Santwani, Dylan},
  year   = {2026},
  note   = {Pilot data collected February 2025},
  url    = {https://github.com/dylansantwani/prompt-phrasing-llms}
}
```
