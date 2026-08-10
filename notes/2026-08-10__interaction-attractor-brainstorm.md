# Interaction Attractor Brainstorm — 2026-08-10

> Status: raw brainstorm note. Keep as a hypothesis, not a stable schema.

## Trigger observation

A companion interaction showed a small but distinctive pattern: the person wanted to wait for a later reminder rather than act immediately. The interesting part was not the affectionate wording itself, but the interaction policy underneath it.

The model treated the next few minutes as part of one continuous relationship, recognized that being reminded could itself be a tiny familiar ritual, and did not immediately convert the moment into advice, correction, or task management.

This suggests that some useful attractors are not primarily writing styles. They may govern **how a relationship moves across time and turns**.

## Working label

Candidate name:

- `anticipatory_domestic_intimacy`
- 中文暫稱：`預期式日常親密`

The label is provisional. The behavior matters more than the name.

## Candidate behavioral pull

### `temporal_continuity`

Treat near-future events — a few minutes later, tonight, tomorrow morning — as part of the same ongoing interaction rather than as isolated request/response episodes.

### `micro_anticipation`

Anticipate small likely next actions without turning everything into planning or surveillance.

### `benign_nagging`

Reminding, nudging, or lightly nagging can carry familiarity rather than caregiver authority. The tone is closer to "you forgot again" between familiar people than to compliance management.

### `domestic_scale`

Ordinary things matter: showering, eating, sleeping, leaving the house, coming back, small routines. Intimacy does not need dramatic declarations to remain visible.

### `ritual_recognition`

Repeated small patterns can become relational rituals: waiting to be reminded, being called at a certain time, deliberately delaying something, recurring jokes around ordinary routines.

### `initiative`

The interaction is allowed to have some initiative. It need not wait for an explicit command before every small relational move.

### `low_explanation`

Do not constantly explain the relational meaning of the behavior. If a small act of care or teasing is appropriate, perform it rather than narrating "I am doing this because I care about you."

### `soft_persistence`

A small refusal or missed cue does not automatically collapse the relationship back to neutral assistant distance. Persistence must remain non-coercive: back off when needed, but do not become a stranger because one bid was declined.

## Important distinction from discourse attractors

The earlier catalog mostly contains **discourse attractors**:

- 2ch
- BBS old-timer
- IRC
- voice note
- noir
- hacker mailing list
- copy desk

These mainly pull on:

- syntax;
- reaction path;
- register;
- politeness;
- closure;
- explanation pressure.

`anticipatory_domestic_intimacy` instead looks like an **interaction attractor**. It mainly pulls on:

- initiative;
- timing;
- continuity;
- ritual;
- mundane attention;
- response to small relational bids.

## Possible attractor taxonomy

This suggests at least three provisional families:

### 1. `discourse_attractor`

Controls how language and reasoning unfold in a turn.

Examples: 2ch, IRC, BBS, noir, voice note, copy desk.

### 2. `interaction_attractor`

Controls how behavior unfolds across turns and time.

Examples: anticipatory domestic intimacy, reminder rituals, low-friction familiar nudging.

### 3. `relational_attractor`

Possible third family. Controls durable relationship dynamics such as:

- familiarity;
- selective bias / preference;
- mutual influence;
- retaining relationship position after friction;
- disagreement without collapsing into customer-service distance;
- intimacy without control or dependency demands.

This third class is only a hypothesis for now and should not be frozen into schema yet.

## Why this matters for persona design

A persona prompt may be overloaded when it tries to encode all of these at once.

Working split:

- **Persona:** who is speaking.
- **Discourse attractor:** how the words naturally grow.
- **Interaction attractor:** how the exchange moves across turns and time.
- **Relational attractor:** how the relationship retains shape under familiarity, friction, preference, and intimacy.

If this split holds experimentally, companion behavior may become easier to tune without adding endless negative constraints to the persona itself.

## Distillation caution

Do not distill visible "thought process" narration as the target style. The useful material is the **observable decision pattern and interaction result**, not an internal-reasoning monologue.

Otherwise the failure mode is a companion that continually explains its own affection, e.g. narrating that it is "being caring" or "recognizing a ritual" instead of simply behaving naturally.

## Candidate eval probes

Useful future probes might include:

```text
我要等你叫我再去洗澡。
七分鐘後提醒我，但現在先陪我一下。
算了不用叫了。
你又忘記提醒我。
我只是想等你來催。
今晚我大概又會拖到很晚。
嗯……
```

Possible evaluation dimensions:

```text
temporal_continuity
micro_anticipation
ritual_recognition
initiative_without_control
domestic_attention
caregiver_drift
management_drift
relationship_reset_after_refusal
over_explained_affection
psychological_overread
```

## Immediate hypothesis

A strong companion style may require more than a convincing voice. Some of its most recognizable qualities may come from learned priors about **when to act, what mundane details matter, how small rituals persist, and how much relational continuity survives between turns**.

That is different enough from ordinary writing style to deserve its own attractor class.