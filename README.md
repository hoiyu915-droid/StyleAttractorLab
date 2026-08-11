# StyleAttractorLab

StyleAttractorLab is a model-agnostic lab for testing **style attractors**: compact behavioral priors that can change reaction order, attention, syntax, social stance, epistemic habits, closure, and—when explicitly modeled—cross-turn interaction.

The working split is:

- **Persona**: who is speaking and what remains durable.
- **Discourse attractor**: how language and reasoning unfold within a turn.
- **Interaction attractor**: how behavior moves across turns and near-future events.
- **Relational attractor**: what remains stable through familiarity, correction, refusal, and friction.
- **Recipe**: a relative blend plus suppressions and guardrails.
- **Eval**: heterogeneous probes that test behavior without rewarding surface cosplay.

v0.2 contains 17 class-aware attractors, eight recipes, single-turn and multi-turn eval suites, deterministic prompt assembly, frozen run provenance, and direction-aware score summaries. Every contract remains provisional or experimental; weights express design intent, not calibrated probabilities.

## Quick start

Python 3.10+ is enough. Checked-in `.yaml` files use the JSON-compatible YAML subset, so the core workflow has no runtime dependency.

```bash
python -m style_attractor_lab validate .
python -m style_attractor_lab catalog
python -m style_attractor_lab catalog --class interaction_attractor --json
python -m style_attractor_lab assemble recipes/ptt_informed.yaml \
  --output build/ptt_informed.md
python -m style_attractor_lab init-run recipes/technical_review.yaml \
  --model your-model-id \
  --output runs/technical-review-01
```

Each recipe selects its own eval suite and rubric. `init-run` freezes the recipe, compiled layer, selected prompts, selected rubric, their source names, and SHA-256 digests. After generation, record one output object and one complete score object per prompt:

```bash
python -m style_attractor_lab summarize runs/technical-review-01/scores.jsonl \
  --rubric runs/technical-review-01/rubric.yaml \
  --output runs/technical-review-01/summary.json
```

Install the optional YAML parser only when using full YAML syntax:

```bash
python -m pip install -e '.[yaml]'
```

## Catalog

| Class | Count | Included attractors |
|---|---:|---|
| Discourse | 15 | 2ch, BBS old-timer, IRC, imageboard compression, friend-group chat, stand-up contradiction finder, hard-boiled restraint, tabloid desk, copy desk, hacker mailing-list review, cross-examination, incident SITREP, punk editorial edge, voice note, PTT informed informalism |
| Interaction | 1 | anticipatory domestic intimacy |
| Relational | 1 | relational continuity under friction |

`status` distinguishes the four migrated provisional attractors from newly formalized experimental ones. `risk_level` does not measure quality; it indicates how aggressively failure guards should remain active. The imageboard attractor is high-risk and is included only at low weight in an evidence-bounded recipe.

## Recipes

| Recipe | Purpose | Eval suite |
|---|---|---|
| `balanced_direct` | General reaction-first directness | Single-turn |
| `live_casual` | Immediate shared-context conversation | Single-turn |
| `technical_review` | Failure-mechanism and design review | Single-turn |
| `editorial_edge` | Strong lead and judgment without distortion | Single-turn |
| `adult_restraint` | Selective emotional presence without genre costume | Single-turn |
| `incident_response` | State, delta, blocker, risk, next action | Single-turn |
| `ptt_informed` | Dense explanation without tonal seriousness | Single-turn |
| `relational_continuity` | Ritual, bounded initiative, and continuity after friction | Multi-turn |

## Experiment loop

1. Specify a positive behavioral trajectory and its over-application failures.
2. Blend attractors in a recipe whose positive weights sum to `1.0`.
3. Validate catalog references, eval suites, rubrics, and complete recipe coverage.
4. Freeze a run bundle before generation.
5. Score against the recipe-selected rubric, including task fidelity and caricature or boundary failures.
6. Compare frozen manifests and normalized summaries across recipes or models.

The validator rejects unreferenced attractors. A catalog entry therefore needs at least one bounded recipe; adding decorative records that nothing can exercise is not enough.

## Repository map

```text
attractors/           Class-aware provisional and experimental records
recipes/              Relative blends, eval routing, suppressions, guardrails
evals/                Single-turn and multi-turn probes plus two rubrics
schemas/              Attractor, recipe, prompt, rubric, run, output, score contracts
style_attractor_lab/  Dependency-light CLI and validation logic
tests/                Contract, catalog, compiler, run, and scoring tests
notes/                Raw hypotheses preserved separately from contracts
```

Generated `runs/` are ignored because model outputs may contain private or conversation-derived material. Multi-turn output records may use an array of strings, one captured assistant response per user turn.

## Method and safety boundaries

- Named discourse cultures are behavioral references, not invitations to imitate slang, stereotypes, hostility, or copyrighted voices.
- Attractor layers never override correctness, evidence requirements, safety rules, changed consent, or explicit instructions.
- Interaction continuity must stop an unwanted action immediately after refusal; familiarity may remain, coercion may not.
- Relational preference must not become exclusivity, dependency pressure, isolation, or control.
- The compiler assembles deterministic prompt layers; it does not prove model adherence.
- Rubric scores support controlled comparison and are not validated psychometric measurements.

The raw notes remain source hypotheses:

- [`notes/2026-08-10__style-attractor-brainstorm.md`](notes/2026-08-10__style-attractor-brainstorm.md)
- [`notes/2026-08-10__interaction-attractor-brainstorm.md`](notes/2026-08-10__interaction-attractor-brainstorm.md)
- [`notes/2026-08-11__ptt-attractor-note.md`](notes/2026-08-11__ptt-attractor-note.md)

