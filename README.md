# StyleAttractorLab

StyleAttractorLab is a small, model-agnostic lab for testing **style attractors**: compact discourse frames that can change not only wording, but reaction order, attention, sentence structure, social stance, epistemic habits, and closure behavior.

The working distinction is deliberately narrow:

- **Persona** says who is speaking and what remains durable.
- **Attractor** says how a response tends to grow.
- **Recipe** combines attractors and suppressions for one context.
- **Eval** checks whether the behavior survives heterogeneous prompts without turning into caricature.

This repository now contains a runnable v0.1 experiment loop. The contracts are still provisional; weights express relative design intent, not calibrated probabilities or mixture coefficients.

## Quick start

Python 3.10+ is enough. The checked-in examples use the JSON-compatible subset of YAML, so the core workflow has no runtime dependency.

```bash
python -m style_attractor_lab validate .
python -m style_attractor_lab assemble recipes/balanced_direct.yaml \
  --output build/balanced_direct.md
python -m style_attractor_lab init-run recipes/balanced_direct.yaml \
  --model your-model-id \
  --output runs/first-run
```

`init-run` creates a self-contained run directory with the compiled style layer, frozen prompts, rubric, hashes, and empty `outputs.jsonl` / `scores.jsonl` files. Run your chosen model outside this repository, record one JSON object per line, then summarize human or evaluator scores:

```bash
python -m style_attractor_lab summarize runs/first-run/scores.jsonl \
  --rubric runs/first-run/rubric.yaml \
  --output runs/first-run/summary.json
```

Full YAML syntax is optional:

```bash
python -m pip install -e '.[yaml]'
```

Without PyYAML, documents must remain valid JSON even when their extension is `.yaml`.

## Experiment loop

1. Describe a discourse trajectory in `attractors/`, including its over-application failures.
2. Blend attractors in a recipe whose positive weights sum to `1.0`.
3. Validate the repository and compile the style layer.
4. Freeze a run bundle before generation.
5. Score every output against the same rubric, including fidelity and caricature checks.
6. Compare recipes or model versions using the frozen manifests and normalized summaries.

Do not score only whether an output “sounds like” the named culture. The useful target is the underlying behavior: what is noticed first, how directly the response moves, whether uncertainty stays visible, and whether it stops when the content is exhausted.

## Repository map

```text
attractors/       Provisional attractor records
recipes/          Relative blends and global suppressions
evals/            Heterogeneous fixed prompts and scoring rubric
schemas/          Machine-readable v0.1 contracts
style_attractor_lab/  Dependency-light CLI and validation logic
tests/            Contract, compiler, run-bundle, and scoring tests
notes/            Raw research notes; preserved as notes, not contracts
```

Generated `runs/` are ignored by default because model outputs may contain private or conversation-derived material. Commit only deliberately scrubbed fixtures or aggregate results.

## Method boundaries

- Named discourse cultures are behavioral references, not permission for slang cosplay, stereotyping, hostility, or unsafe content.
- An attractor layer never overrides task correctness, evidence requirements, safety rules, or explicit user instructions.
- The compiler is deterministic prompt assembly, not evidence that a model will follow the recipe.
- The supplied rubric supports controlled comparison; it is not a validated psychometric instrument.
- Do not infer stable persona traits from a single output or treat evaluator scores as ground truth.

The raw notes remain hypotheses rather than contracts:

- [`notes/2026-08-10__style-attractor-brainstorm.md`](notes/2026-08-10__style-attractor-brainstorm.md)
- [`notes/2026-08-10__interaction-attractor-brainstorm.md`](notes/2026-08-10__interaction-attractor-brainstorm.md)
- [`notes/2026-08-11__ptt-attractor-note.md`](notes/2026-08-11__ptt-attractor-note.md)
