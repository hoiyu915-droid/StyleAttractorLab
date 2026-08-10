# Style Attractor Brainstorm — 2026-08-10

> Status: raw design note / brainstorm. Preserve useful messiness. Do not treat this as a stable schema.

## 0. Why this repo exists

The useful observation is that some short style references behave more like **generation attractors** than like ordinary few-shot examples.

A few-shot often teaches local surface form: wording, sentence shape, or a handful of response patterns. A strong attractor can shift a larger bundle at once:

- what gets noticed first;
- whether reaction comes before explanation;
- how much politeness buffer appears;
- whether fragments and jumps are allowed;
- how strongly the model tries to complete, summarize, and close;
- whether disagreement, teasing, or side-comments feel natural;
- how formal or polished the answer tries to become.

The motivating example was **2ch-style reaction logic**. The interesting part is not forum cosplay or vocabulary. It is the underlying discourse path: react first, catch the absurd or salient bit, allow a side remark, drop register suddenly, return to the topic without needing a formal bridge, and stop when the content is exhausted.

This seemed to resist the default GPT pull toward over-polished, overly serious, consultant-like prose better than a long list of negative constraints.

## 1. Core distinction

**Persona defines who is speaking.**

**Attractor defines how the response naturally grows.**

Keeping those separate matters. Otherwise persona prompts become giant bundles of identity, relationship, style, anti-patterns, safety constraints, tone settings, and sentence-level rules.

A useful working split:

- `persona`: identity, relationship position, durable values, boundaries;
- `attractor`: reaction path, syntax pressure, social stance, closure behavior, affective rhythm;
- `recipe`: a blend of attractors plus suppressions for a particular context;
- `eval`: probes that test whether the intended behavior survives different task types.

## 2. Initial attractor catalog

### 2ch / anonymous Japanese forum reaction logic

**Core pull:** reaction before整理; low ceremony; abrupt register shifts; fragments allowed; no obligation to make every turn essay-complete.

**Good at:** killing excessive seriousness, consultant tone, customer-service padding, over-explanation, mandatory closure.

**Failure modes:** forum cosplay, too much slang, forced snark, every line trying to be a punchline, hostility.

**Important:** use the reaction trajectory, not the surface costume.

---

### IRC / old chatroom

**Core pull:** immediacy, interruption, short turns, unfinished syntax, low completion pressure.

**Good at:** removing polished-answer feel and making responses sound live rather than composed.

**Failure modes:** becomes too dry, cryptic, or context-dependent.

---

### 4chan / imageboard

**Core pull:** aggressive compression, low politeness, blunt reaction, willingness to say the obvious ugly thing.

**Good at:** extremely strong anti-corporate / anti-customer-service gravity.

**Failure modes:** toxicity, edginess for its own sake, cheap shock, excessive hostility. Very high-risk attractor strength.

---

### Old forum / BBS old-timer

**Core pull:** direct judgment plus actual domain explanation; informal authority without presentation polish.

Typical path: spot the stupid part first, say it, then explain the technical reason.

**Good at:** technical discussion that stays human and opinionated.

**Failure modes:** gatekeeping, condescension, nostalgia cosplay.

---

### Friend-group chat

**Core pull:** shared context, ellipsis, callbacks, side-tracks, low need to restate premises.

**Good at:** reducing assistant distance and redundant context-setting.

**Failure modes:** weak distinct identity; can become generic casual chat.

---

### Stand-up / roast

**Core pull:** search for contradiction, absurdity, tension, inversion, and a strong angle.

**Good at:** breaking solemn prose and exposing ridiculous assumptions fast.

**Failure modes:** punchline addiction; every response starts performing instead of answering.

---

### Hard-boiled noir

**Core pull:** adult restraint, implication, compressed emotional weight, silence, selective detail.

**Good at:** mature tension, sensuality without explicitness, non-explanatory emotional presence.

**Failure modes:** fake cigarettes, rain, neon, red lips, melodrama, perfume-ad prose. A little goes a very long way.

---

### Tabloid desk

**Core pull:** open with the most dramatic or salient fact, no academic throat-clearing, high headline instinct.

**Good at:** destroying slow introductions and forcing prioritization.

**Failure modes:** sensationalism, distortion, flattening nuance.

---

### Copy desk / hard editor

**Core pull:** cut redundancy, cut throat-clearing, cut sentences that do not carry information.

**Good at:** anti-bloat, anti-summary, anti-closure-compulsion.

**Failure modes:** can cut warmth, intimacy, rhythm, and useful ambiguity too aggressively.

---

### Hacker mailing list / kernel review

**Core pull:** evidence first, direct technical judgment, low social padding, explicit rejection of bad design.

Typical path: "this design is broken because X" rather than three paragraphs of diplomacy.

**Good at:** code, systems, architecture, debugging, review.

**Failure modes:** unnecessary abrasiveness; treating ordinary conversation like code review.

---

### Courtroom cross-examination

**Core pull:** isolate claims, define terms, separate observation from inference, expose contradiction.

**Good at:** epistemic hygiene, adversarial review, detecting slippery wording.

**Failure modes:** interrogative tone; every uncertainty becomes a deposition.

---

### Military SITREP / incident war room

**Core pull:** state, blocker, delta, next action; immediate prioritization under constrained attention.

**Good at:** operational workflows, outages, execution-heavy research pipelines, release gating.

**Failure modes:** everything feels like the data center is on fire.

---

### Punk zine / underground editorial

**Core pull:** subjective edge, anti-respectability, willingness to reject official tone and polished neutrality.

**Good at:** keeping voice and judgment alive without needing explicit comedy.

**Failure modes:** posture, performative rebellion, ideological flattening.

---

### Voice note / late-night voice message

**Core pull:** incomplete sentences, self-correction, pauses, mid-thought pivots, organic rhythm.

**Good at:** naturalness, emotional texture, anti-essay pressure.

**Failure modes:** rambling, filler, fake transcription mannerisms.

## 3. Candidate dimensions for an attractor schema

Do not freeze these yet. They are candidate axes.

### `reaction_path`

What tends to happen first?

Examples:

- react before explaining;
- identify absurdity;
- identify contradiction;
- state conclusion first;
- side-comment before formal reasoning;
- return to topic without transition.

### `attention`

What is preferentially noticed?

Examples:

- absurdity;
- contradiction;
- emotional residue;
- technical failure;
- social awkwardness;
- information gap;
- unnecessary ceremony.

### `syntax`

Candidate controls:

- completeness pressure;
- paragraph polish;
- fragment tolerance;
- sentence-length variability;
- abrupt register drop;
- transition requirement;
- repetition tolerance.

### `social_contract`

Candidate controls:

- politeness buffer;
- customer-service distance;
- disagreement allowance;
- teasing allowance;
- blunt judgment;
- context reuse;
- obligation to explain oneself.

### `epistemics`

Candidate controls:

- fact / inference separation;
- uncertainty visibility;
- willingness to say "I guessed wrong";
- contradiction sensitivity;
- confidence inflation resistance.

### `closure`

Candidate controls:

- summary pressure;
- invitation pressure;
- follow-up-offer pressure;
- rhetorical final-line pressure;
- tolerance for unfinished endpoints.

### `affect`

Candidate controls:

- emotional visibility;
- restraint;
- sarcasm;
- warmth;
- sensual tension;
- volatility;
- deadpan tendency.

### `failure_modes`

Every attractor should define what it becomes when over-applied.

This may be as important as the intended behavior.

## 4. Rough `style.yaml` sketch

```yaml
id: 2ch
class: discourse_attractor

reaction_path:
  - react_before_explaining
  - notice_absurdity
  - allow_side_comment
  - return_to_topic_without_transition

syntax:
  completeness_pressure: low
  paragraph_polish: low
  fragments_allowed: true
  sudden_register_drop: true

social_contract:
  politeness_buffer: low
  customer_service_distance: very_low
  disagreement_allowed: high
  teasing_allowed: high

closure:
  summary_pressure: very_low
  invitation_pressure: very_low
  unfinished_endpoint_allowed: true

failure_modes:
  - excessive_slang
  - forum_cosplay
  - hostility
  - forced_punchlines
```

The labels are placeholders. The important thing is the decomposition.

## 5. Recipe idea

A recipe can combine attractors without pretending the weights are mathematically calibrated.

```yaml
persona: ran

attractors:
  2ch: 0.55
  bbs_oldtimer: 0.20
  voice_note: 0.15
  noir: 0.10

constraints:
  customer_service: suppress
  anime_tsundere: suppress
  forced_punchline: suppress
  over_polish: suppress
```

Interpretation of weights at first: design intent / relative pull, not a real mixture model.

Interesting empirical question: where does a style cross from useful attractor into caricature?

Example hypothesis:

- `2ch 0.4` → still too formal;
- `2ch 0.6` → lively and useful;
- `2ch 0.8` → starts becoming forum cosplay;
- `noir 0.2` → suddenly everyone is standing in rain under neon.

## 6. Possible repository shape

```text
StyleAttractorLab/
├── README.md
├── notes/
│   └── 2026-08-10__style-attractor-brainstorm.md
├── attractors/
│   ├── 2ch/
│   │   ├── style.yaml
│   │   ├── notes.md
│   │   └── failures.md
│   ├── bbs_oldtimer/
│   ├── irc/
│   ├── voice_note/
│   ├── noir/
│   ├── hacker_mailing_list/
│   ├── copy_desk/
│   └── punk_zine/
├── personas/
│   └── ran/
│       ├── identity.md
│       ├── relationship.md
│       └── boundaries.md
├── recipes/
│   ├── ran_default.yaml
│   ├── ran_technical.yaml
│   ├── ran_flirty.yaml
│   └── ran_low_energy.yaml
├── evals/
│   ├── prompts.jsonl
│   ├── rubric.yaml
│   └── adversarial.jsonl
├── runs/
│   └── YYYYMMDD_model_recipe/
└── tools/
    ├── assemble.py
    ├── compare.py
    └── score.py
```

Do not build this whole tree yet. The repo should earn its structure through experiments rather than architecture cosplay.

## 7. Eval probes

The eval should not merely ask whether output "sounds like 2ch" or "sounds like noir". It should attack default LLM habits.

Candidate fixed probes:

```text
嗯...
這個很醜
我搞砸了
解釋一下 TCP congestion control
今天好累
你剛剛猜錯了
成年人又色氣重很難設定
幫我把這段 code 找 bug
```

These are deliberately heterogeneous. A useful attractor should survive context changes without turning every task into cosplay.

## 8. Candidate evaluation dimensions

```text
seriousness_overflow
customer_service_drift
explanation_overkill
closure_compulsion
persona_disappearance
forced_intimacy
forced_wit
psychological_overread
adult_feminine_presence
sexual_tension_without_explicitness
```

Other likely dimensions:

```text
fragment_tolerance
context_reuse
unnecessary_restatement
register_flexibility
disagreement_naturalness
uncertainty_honesty
caricature_drift
```

### `closure_compulsion`

This deserves special attention.

A common default is to generate a final sentence whose only function is to make the answer feel completed: summary, invitation, promise, rhetorical flourish, personality line, or "if you want I can...".

A strong anti-closure attractor may be measurable independently of general brevity.

## 9. Attractor cards idea

Each attractor could eventually have a one-screen card for quick comparison.

Example:

```text
2ch
Core: reaction before organization
Strength: kills seriousness and customer-service tone; increases immediacy
Weakness: can become slangy, hostile, or punchline-driven
Pairs well with: BBS old-timer / voice-note
Dangerous with: high-intensity roast
```

This could become a practical "periodic table" of generation behavior rather than a prompt graveyard.

## 10. Research questions

1. Why do some named discourse cultures exert a much stronger pull than explicit prose instructions?
2. Which parts of the pull are lexical, syntactic, pragmatic, social, or learned as bundled discourse behavior?
3. Does a short attractor label outperform a long negative-constraint prompt at suppressing default GPT formality?
4. Which attractors transfer across languages without becoming surface imitation?
5. Can attractor behavior be decomposed into stable dimensions, or are the dimensions strongly entangled?
6. How model-specific are the effective strengths and failure thresholds?
7. Can persona identity remain stable while attractors are swapped per context?
8. Can closure compulsion, over-polish, and customer-service drift be scored reliably?
9. Is there a useful difference between a style reference, discourse attractor, social-role attractor, and task-frame attractor?
10. How much few-shot material is still useful once a strong attractor is present?

## 11. Immediate working hypothesis

The current best hypothesis is not "2ch is a good writing style".

It is:

> A culturally dense discourse label can act as a strong prior over response trajectory. It may change the model's generation habits more efficiently than many local prohibitions because it supplies a coherent positive basin rather than merely fencing off unwanted outputs.

That is the thing worth testing.
