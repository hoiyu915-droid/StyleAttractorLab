# Contributing

Keep additions empirical and small. The repository is meant to earn structure through experiments, not collect prompt architecture for its own sake.

## Add or change an attractor

1. Start from an observed response trajectory, not a list of aesthetic adjectives.
2. Describe the positive pull in `prompt_cues`.
3. Add concrete over-application risks in `failure_modes`.
4. Avoid copyrighted imitation requests, identity stereotypes, and surface costume.
5. Reference it from a recipe and test it across ordinary, technical, ambiguous, corrective, and low-context prompts.
6. Run:

```bash
python -m style_attractor_lab validate .
python -m unittest discover -s tests -v
```

## Data hygiene

Do not commit raw private conversations, hidden prompts, credentials, or unsanitized model outputs. `runs/` is ignored for that reason. Aggregate scores and deliberately constructed fixtures are preferred.

## Contract changes

The v0.1 schemas are provisional, but changes must stay synchronized across:

- `schemas/`;
- the validator/compiler;
- starter records;
- tests;
- the changelog when behavior changes.

