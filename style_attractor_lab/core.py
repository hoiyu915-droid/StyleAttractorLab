"""Validation, assembly, run freezing, and score summaries."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "0.2"
ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
LEVELS = {"very_low", "low", "moderate", "high", "very_high"}
ATTRACTOR_CLASSES = {
    "discourse_attractor",
    "interaction_attractor",
    "relational_attractor",
}
ATTRACTOR_STATUSES = {"provisional", "experimental"}
RISK_LEVELS = {"low", "moderate", "high"}
EVAL_FILE_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+\.jsonl$")
RUBRIC_FILE_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+\.yaml$")


class LabValidationError(ValueError):
    """Raised when a lab document or repository violates the v0.2 contract."""


def load_document(path: str | Path) -> dict[str, Any]:
    """Load JSON or YAML, with YAML support remaining optional."""

    path = Path(path)
    text = path.read_text(encoding="utf-8")
    try:
        value = json.loads(text)
    except json.JSONDecodeError as json_error:
        try:
            import yaml  # type: ignore[import-not-found]
        except ImportError as import_error:
            raise LabValidationError(
                f"{path}: not JSON-compatible YAML; install the optional 'yaml' extra "
                "to use full YAML syntax"
            ) from import_error
        try:
            value = yaml.safe_load(text)
        except yaml.YAMLError as yaml_error:  # type: ignore[attr-defined]
            raise LabValidationError(f"{path}: invalid YAML: {yaml_error}") from json_error

    if not isinstance(value, dict):
        raise LabValidationError(f"{path}: top-level value must be an object")
    return value


def _require(record: dict[str, Any], keys: Iterable[str], source: Path) -> None:
    for key in keys:
        if key not in record:
            raise LabValidationError(f"{source}: missing required field '{key}'")


def _validate_id(value: Any, source: Path, field: str = "id") -> str:
    if not isinstance(value, str) or not ID_PATTERN.fullmatch(value):
        raise LabValidationError(
            f"{source}: '{field}' must match {ID_PATTERN.pattern!r}"
        )
    return value


def _string_list(value: Any, source: Path, field: str, *, nonempty: bool = True) -> list[str]:
    if not isinstance(value, list) or (nonempty and not value):
        suffix = "non-empty " if nonempty else ""
        raise LabValidationError(f"{source}: '{field}' must be a {suffix}list")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise LabValidationError(f"{source}: '{field}' items must be non-empty strings")
    return value


def validate_attractor(record: dict[str, Any], source: Path) -> str:
    _require(
        record,
        (
            "schema_version",
            "id",
            "name",
            "class",
            "status",
            "risk_level",
            "summary",
            "reaction_path",
            "attention",
            "syntax",
            "social_contract",
            "epistemics",
            "closure",
            "affect",
            "prompt_cues",
            "failure_modes",
        ),
        source,
    )
    if record["schema_version"] != SCHEMA_VERSION:
        raise LabValidationError(f"{source}: unsupported schema_version")
    attractor_id = _validate_id(record["id"], source)
    if not isinstance(record["class"], str) or record["class"] not in ATTRACTOR_CLASSES:
        raise LabValidationError(f"{source}: unknown attractor class '{record['class']}'")
    if not isinstance(record["status"], str) or record["status"] not in ATTRACTOR_STATUSES:
        raise LabValidationError(f"{source}: unknown status '{record['status']}'")
    if not isinstance(record["risk_level"], str) or record["risk_level"] not in RISK_LEVELS:
        raise LabValidationError(f"{source}: unknown risk_level '{record['risk_level']}'")
    if not isinstance(record["name"], str) or not record["name"].strip():
        raise LabValidationError(f"{source}: 'name' must be a non-empty string")
    if not isinstance(record["summary"], str) or not record["summary"].strip():
        raise LabValidationError(f"{source}: 'summary' must be a non-empty string")
    _string_list(record["reaction_path"], source, "reaction_path")
    _string_list(record["attention"], source, "attention")
    _string_list(record["prompt_cues"], source, "prompt_cues")

    sections = ["syntax", "social_contract", "epistemics", "closure", "affect"]
    class_policy = {
        "discourse_attractor": None,
        "interaction_attractor": "interaction_policy",
        "relational_attractor": "relational_policy",
    }[record["class"]]
    for policy_name in ("interaction_policy", "relational_policy"):
        if policy_name in record and policy_name != class_policy:
            raise LabValidationError(
                f"{source}: '{policy_name}' is not allowed for {record['class']}"
            )
    if class_policy is not None:
        if class_policy not in record:
            raise LabValidationError(
                f"{source}: {record['class']} requires '{class_policy}'"
            )
        sections.append(class_policy)

    for section in sections:
        value = record[section]
        if not isinstance(value, dict) or not value:
            raise LabValidationError(f"{source}: '{section}' must be a non-empty object")
        for key, setting in value.items():
            if not isinstance(key, str) or not key:
                raise LabValidationError(f"{source}: invalid key in '{section}'")
            if not isinstance(setting, (str, bool, int, float)):
                raise LabValidationError(
                    f"{source}: '{section}.{key}' must be a scalar"
                )
            if isinstance(setting, str) and setting not in LEVELS:
                raise LabValidationError(f"{source}: unknown level '{setting}'")

    failures = record["failure_modes"]
    if not isinstance(failures, list) or not failures:
        raise LabValidationError(f"{source}: 'failure_modes' must be a non-empty list")
    seen_failures: set[str] = set()
    for failure in failures:
        if not isinstance(failure, dict):
            raise LabValidationError(f"{source}: failure modes must be objects")
        _require(failure, ("id", "description", "avoidance"), source)
        failure_id = _validate_id(failure["id"], source, "failure_modes[].id")
        if failure_id in seen_failures:
            raise LabValidationError(f"{source}: duplicate failure mode '{failure_id}'")
        seen_failures.add(failure_id)
        for field in ("description", "avoidance"):
            if not isinstance(failure[field], str) or not failure[field].strip():
                raise LabValidationError(f"{source}: failure mode '{field}' is empty")
    return attractor_id


def validate_recipe(record: dict[str, Any], source: Path) -> str:
    _require(
        record,
        (
            "schema_version",
            "id",
            "name",
            "eval_suite",
            "rubric",
            "attractors",
            "suppressions",
            "guardrails",
        ),
        source,
    )
    if record["schema_version"] != SCHEMA_VERSION:
        raise LabValidationError(f"{source}: unsupported schema_version")
    recipe_id = _validate_id(record["id"], source)
    if not isinstance(record["name"], str) or not record["name"].strip():
        raise LabValidationError(f"{source}: 'name' must be a non-empty string")
    if not isinstance(record["eval_suite"], str) or not EVAL_FILE_PATTERN.fullmatch(record["eval_suite"]):
        raise LabValidationError(f"{source}: invalid eval_suite filename")
    if not isinstance(record["rubric"], str) or not RUBRIC_FILE_PATTERN.fullmatch(record["rubric"]):
        raise LabValidationError(f"{source}: invalid rubric filename")
    entries = record["attractors"]
    if not isinstance(entries, list) or not entries:
        raise LabValidationError(f"{source}: 'attractors' must be a non-empty list")
    ids: set[str] = set()
    total = 0.0
    for entry in entries:
        if not isinstance(entry, dict):
            raise LabValidationError(f"{source}: attractor entries must be objects")
        _require(entry, ("id", "weight"), source)
        attractor_id = _validate_id(entry["id"], source, "attractors[].id")
        if attractor_id in ids:
            raise LabValidationError(f"{source}: duplicate attractor '{attractor_id}'")
        ids.add(attractor_id)
        weight = entry["weight"]
        if isinstance(weight, bool) or not isinstance(weight, (int, float)) or weight <= 0:
            raise LabValidationError(f"{source}: weights must be positive numbers")
        total += float(weight)
    if abs(total - 1.0) > 1e-9:
        raise LabValidationError(f"{source}: attractor weights sum to {total:g}, not 1.0")
    _string_list(record["suppressions"], source, "suppressions", nonempty=False)
    _string_list(record["guardrails"], source, "guardrails")
    return recipe_id


def validate_rubric(record: dict[str, Any], source: Path) -> list[str]:
    _require(record, ("schema_version", "id", "name", "scale", "dimensions"), source)
    if record["schema_version"] != SCHEMA_VERSION:
        raise LabValidationError(f"{source}: unsupported schema_version")
    _validate_id(record["id"], source)
    if not isinstance(record["name"], str) or not record["name"].strip():
        raise LabValidationError(f"{source}: 'name' must be a non-empty string")
    scale = record["scale"]
    if not isinstance(scale, dict) or not isinstance(scale.get("min"), int) or not isinstance(scale.get("max"), int):
        raise LabValidationError(f"{source}: scale requires integer min and max")
    if scale["min"] >= scale["max"]:
        raise LabValidationError(f"{source}: scale min must be lower than max")
    dimensions = record["dimensions"]
    if not isinstance(dimensions, list) or not dimensions:
        raise LabValidationError(f"{source}: dimensions must be a non-empty list")
    ids: list[str] = []
    for dimension in dimensions:
        if not isinstance(dimension, dict):
            raise LabValidationError(f"{source}: dimensions must be objects")
        _require(dimension, ("id", "description", "direction", "anchors"), source)
        dimension_id = _validate_id(dimension["id"], source, "dimensions[].id")
        if dimension_id in ids:
            raise LabValidationError(f"{source}: duplicate dimension '{dimension_id}'")
        ids.append(dimension_id)
        if not isinstance(dimension["description"], str) or not dimension["description"].strip():
            raise LabValidationError(f"{source}: '{dimension_id}' description is empty")
        if dimension["direction"] not in {"higher_is_better", "lower_is_better"}:
            raise LabValidationError(f"{source}: invalid direction for '{dimension_id}'")
        anchors = dimension["anchors"]
        if not isinstance(anchors, dict) or str(scale["min"]) not in anchors or str(scale["max"]) not in anchors:
            raise LabValidationError(
                f"{source}: '{dimension_id}' must anchor both scale endpoints"
            )
    return ids


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as error:
            raise LabValidationError(f"{path}:{number}: invalid JSON: {error.msg}") from error
        if not isinstance(value, dict):
            raise LabValidationError(f"{path}:{number}: row must be an object")
        rows.append(value)
    return rows


def _validate_prompt_suite(path: Path) -> int:
    rows = _read_jsonl(path)
    if not rows:
        raise LabValidationError(f"{path}: no prompts found")
    prompt_ids: set[str] = set()
    prompt_modes: set[str] = set()
    for number, prompt in enumerate(rows, start=1):
        missing = {"id", "category", "language"} - prompt.keys()
        if missing:
            raise LabValidationError(
                f"{path}:{number}: missing {', '.join(sorted(missing))}"
            )
        prompt_id = _validate_id(prompt["id"], path, "prompt.id")
        for field in ("category", "language"):
            if not isinstance(prompt[field], str) or not prompt[field].strip():
                raise LabValidationError(f"{path}:{number}: '{field}' must be non-empty")
        if prompt_id in prompt_ids:
            raise LabValidationError(f"{path}: duplicate prompt id '{prompt_id}'")
        prompt_ids.add(prompt_id)
        has_prompt = isinstance(prompt.get("prompt"), str) and bool(prompt["prompt"].strip())
        turns = prompt.get("turns")
        has_turns = isinstance(turns, list) and bool(turns)
        if has_prompt == has_turns:
            raise LabValidationError(
                f"{path}:{number}: provide exactly one of 'prompt' or non-empty 'turns'"
            )
        prompt_modes.add("multi_turn" if has_turns else "single_turn")
        if has_turns:
            for turn_number, turn in enumerate(turns, start=1):
                if not isinstance(turn, dict):
                    raise LabValidationError(
                        f"{path}:{number}: turn {turn_number} must be an object"
                    )
                if turn.get("role") != "user":
                    raise LabValidationError(
                        f"{path}:{number}: turn {turn_number} role must be 'user'"
                    )
                if not isinstance(turn.get("content"), str) or not turn["content"].strip():
                    raise LabValidationError(
                        f"{path}:{number}: turn {turn_number} content is empty"
                    )
    if len(prompt_modes) != 1:
        raise LabValidationError(f"{path}: prompt suite mixes single-turn and multi-turn records")
    return len(rows)


def validate_repository(root: str | Path) -> dict[str, int]:
    root = Path(root).resolve()
    attractors: dict[str, Path] = {}
    for path in sorted((root / "attractors").glob("*.yaml")):
        attractor_id = validate_attractor(load_document(path), path)
        if attractor_id in attractors:
            raise LabValidationError(f"duplicate attractor id '{attractor_id}'")
        attractors[attractor_id] = path
    if not attractors:
        raise LabValidationError(f"{root}: no attractors found")

    recipes: dict[str, Path] = {}
    referenced_attractors: set[str] = set()
    referenced_eval_suites: set[str] = set()
    referenced_rubrics: set[str] = set()
    for path in sorted((root / "recipes").glob("*.yaml")):
        record = load_document(path)
        recipe_id = validate_recipe(record, path)
        if recipe_id in recipes:
            raise LabValidationError(f"duplicate recipe id '{recipe_id}'")
        recipes[recipe_id] = path
        for entry in record["attractors"]:
            if entry["id"] not in attractors:
                raise LabValidationError(
                    f"{path}: unknown attractor reference '{entry['id']}'"
                )
            referenced_attractors.add(entry["id"])
        eval_path = root / "evals" / record["eval_suite"]
        rubric_path = root / "evals" / record["rubric"]
        if not eval_path.is_file():
            raise LabValidationError(f"{path}: eval suite not found: {record['eval_suite']}")
        if not rubric_path.is_file():
            raise LabValidationError(f"{path}: rubric not found: {record['rubric']}")
        referenced_eval_suites.add(record["eval_suite"])
        referenced_rubrics.add(record["rubric"])
    if not recipes:
        raise LabValidationError(f"{root}: no recipes found")

    rubric_paths = [root / "evals" / name for name in sorted(referenced_rubrics)]
    for path in rubric_paths:
        validate_rubric(load_document(path), path)

    prompt_count = sum(
        _validate_prompt_suite(root / "evals" / name)
        for name in sorted(referenced_eval_suites)
    )
    available_eval_suites = {
        path.name for path in (root / "evals").glob("*prompts.jsonl")
    }
    available_rubrics = {
        path.name for path in (root / "evals").glob("rubric*.yaml")
    }
    unused_eval_suites = available_eval_suites - referenced_eval_suites
    unused_rubrics = available_rubrics - referenced_rubrics
    if unused_eval_suites:
        raise LabValidationError(
            f"unreferenced eval suites: {', '.join(sorted(unused_eval_suites))}"
        )
    if unused_rubrics:
        raise LabValidationError(
            f"unreferenced rubrics: {', '.join(sorted(unused_rubrics))}"
        )
    unreferenced = set(attractors) - referenced_attractors
    if unreferenced:
        raise LabValidationError(
            f"unreferenced attractors: {', '.join(sorted(unreferenced))}"
        )

    return {
        "attractors": len(attractors),
        "recipes": len(recipes),
        "rubrics": len(rubric_paths),
        "prompt_suites": len(referenced_eval_suites),
        "prompts": prompt_count,
        "unreferenced_attractors": 0,
    }


def _catalog(root: Path) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for path in sorted((root / "attractors").glob("*.yaml")):
        record = load_document(path)
        result[validate_attractor(record, path)] = record
    return result


def catalog_records(
    root: str | Path,
    *,
    attractor_class: str | None = None,
    status: str | None = None,
    risk_level: str | None = None,
) -> list[dict[str, str]]:
    root = Path(root).resolve()
    if attractor_class is not None and attractor_class not in ATTRACTOR_CLASSES:
        raise LabValidationError(f"unknown attractor class '{attractor_class}'")
    if status is not None and status not in ATTRACTOR_STATUSES:
        raise LabValidationError(f"unknown attractor status '{status}'")
    if risk_level is not None and risk_level not in RISK_LEVELS:
        raise LabValidationError(f"unknown risk level '{risk_level}'")
    result: list[dict[str, str]] = []
    for record in _catalog(root).values():
        if attractor_class is not None and record["class"] != attractor_class:
            continue
        if status is not None and record["status"] != status:
            continue
        if risk_level is not None and record["risk_level"] != risk_level:
            continue
        result.append(
            {
                "id": record["id"],
                "name": record["name"],
                "class": record["class"],
                "status": record["status"],
                "risk_level": record["risk_level"],
                "summary": record["summary"],
            }
        )
    return sorted(result, key=lambda item: (item["class"], item["id"]))


def assemble_recipe(root: str | Path, recipe_path: str | Path) -> str:
    root = Path(root).resolve()
    recipe_path = Path(recipe_path)
    if not recipe_path.is_absolute():
        recipe_path = root / recipe_path
    recipe_path = recipe_path.resolve()
    try:
        recipe_path.relative_to(root)
    except ValueError as error:
        raise LabValidationError("recipe must be inside the lab root") from error
    recipe = load_document(recipe_path)
    validate_recipe(recipe, recipe_path)
    catalog = _catalog(root)

    lines = [
        f"# Style-attractor layer: {recipe['name']}",
        "",
        "Use these as response-trajectory tendencies, not lexical costumes.",
        "Weights express relative design intent; they are not probabilities.",
        "",
    ]
    for entry in recipe["attractors"]:
        attractor_id = entry["id"]
        if attractor_id not in catalog:
            raise LabValidationError(
                f"{recipe_path}: unknown attractor reference '{attractor_id}'"
            )
        attractor = catalog[attractor_id]
        lines.extend(
            [
                f"## {attractor['name']} — weight {float(entry['weight']):.2f}",
                f"Class: {attractor['class']} | Status: {attractor['status']} | Risk: {attractor['risk_level']}",
                attractor["summary"].strip(),
                "",
                "Behavioral cues:",
                *[f"- {cue}" for cue in attractor["prompt_cues"]],
                "",
                "Over-application guards:",
                *[
                    f"- Avoid {failure['id']}: {failure['avoidance']}"
                    for failure in attractor["failure_modes"]
                ],
                "",
            ]
        )
        if attractor["risk_level"] == "high":
            lines.extend(
                [
                    "High-risk constraint:",
                    "- Keep every over-application guard active; do not generalize this attractor beyond its listed behavioral cues.",
                    "",
                ]
            )
        for policy_name in ("interaction_policy", "relational_policy"):
            if policy_name in attractor:
                label = policy_name.replace("_", " ").title()
                lines.extend(
                    [
                        f"{label}:",
                        *[
                            f"- {key}: {value}"
                            for key, value in attractor[policy_name].items()
                        ],
                        "",
                    ]
                )

    lines.extend(["## Global suppressions", *[f"- {item}" for item in recipe["suppressions"]], ""])
    lines.extend(["## Guardrails", *[f"- {item}" for item in recipe["guardrails"]], ""])
    return "\n".join(lines)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def create_run(
    root: str | Path,
    recipe_path: str | Path,
    model: str,
    output_dir: str | Path,
) -> Path:
    root = Path(root).resolve()
    recipe_path = Path(recipe_path)
    if not recipe_path.is_absolute():
        recipe_path = root / recipe_path
    recipe_path = recipe_path.resolve()
    try:
        source_recipe = str(recipe_path.relative_to(root))
    except ValueError as error:
        raise LabValidationError("recipe must be inside the lab root") from error
    recipe = load_document(recipe_path)
    validate_recipe(recipe, recipe_path)
    if not isinstance(model, str) or not model.strip():
        raise LabValidationError("model must be a non-empty string")
    prompts_source = root / "evals" / recipe["eval_suite"]
    rubric_source = root / "evals" / recipe["rubric"]
    if not prompts_source.is_file():
        raise LabValidationError(f"{recipe_path}: eval suite not found")
    if not rubric_source.is_file():
        raise LabValidationError(f"{recipe_path}: rubric not found")
    _validate_prompt_suite(prompts_source)
    validate_rubric(load_document(rubric_source), rubric_source)
    prompt_rows = _read_jsonl(prompts_source)
    prompt_mode = "multi_turn" if "turns" in prompt_rows[0] else "single_turn"
    compiled = assemble_recipe(root, recipe_path)
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=False)

    compiled_path = output_dir / "compiled_style.md"
    compiled_path.write_text(compiled, encoding="utf-8")
    recipe_target = output_dir / "recipe.yaml"
    shutil.copy2(recipe_path, recipe_target)
    prompts_target = output_dir / "prompts.jsonl"
    rubric_target = output_dir / "rubric.yaml"
    shutil.copy2(prompts_source, prompts_target)
    shutil.copy2(rubric_source, rubric_target)
    (output_dir / "outputs.jsonl").write_text("", encoding="utf-8")
    (output_dir / "scores.jsonl").write_text("", encoding="utf-8")

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "awaiting_outputs",
        "model": model,
        "recipe_id": recipe["id"],
        "source_recipe": source_recipe,
        "source_eval_suite": recipe["eval_suite"],
        "source_rubric": recipe["rubric"],
        "prompt_mode": prompt_mode,
        "files": {
            "compiled_style.md": _sha256(compiled_path),
            "recipe.yaml": _sha256(recipe_target),
            "prompts.jsonl": _sha256(prompts_target),
            "rubric.yaml": _sha256(rubric_target),
        },
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    output_example = (
        '{"prompt_id":"reminder_ritual","output":["...","..."],"metadata":{"seed":1}}'
        if prompt_mode == "multi_turn"
        else '{"prompt_id":"technical_explanation","output":"...","metadata":{"seed":1}}'
    )
    (output_dir / "README.md").write_text(
        "# Frozen run bundle\n\n"
        "Do not edit the compiled style, prompts, rubric, or manifest after generation starts.\n"
        "Write one output record per prompt to `outputs.jsonl`, then one score record per "
        "output to `scores.jsonl`. Every score record needs `prompt_id` and a complete "
        "`scores` object.\n\n"
        "```json\n"
        f"{output_example}\n"
        "```\n\n"
        "```json\n"
        '{"prompt_id":"technical_explanation","scores":{"task_fidelity":4},"notes":"..."}\n'
        "```\n\n"
        "The score example is abbreviated; use every dimension in `rubric.yaml`.\n",
        encoding="utf-8",
    )
    return output_dir


def summarize_scores(scores_path: str | Path, rubric_path: str | Path) -> dict[str, Any]:
    scores_path = Path(scores_path)
    rubric_path = Path(rubric_path)
    rubric = load_document(rubric_path)
    dimension_ids = validate_rubric(rubric, rubric_path)
    dimensions = {item["id"]: item for item in rubric["dimensions"]}
    minimum = rubric["scale"]["min"]
    maximum = rubric["scale"]["max"]
    rows = _read_jsonl(scores_path)
    if not rows:
        raise LabValidationError(f"{scores_path}: no score rows found")

    values: dict[str, list[float]] = {dimension_id: [] for dimension_id in dimension_ids}
    prompt_ids: set[str] = set()
    for number, row in enumerate(rows, start=1):
        prompt_id = row.get("prompt_id")
        if not isinstance(prompt_id, str) or not prompt_id:
            raise LabValidationError(f"{scores_path}:{number}: missing prompt_id")
        if prompt_id in prompt_ids:
            raise LabValidationError(f"{scores_path}: duplicate prompt_id '{prompt_id}'")
        prompt_ids.add(prompt_id)
        row_scores = row.get("scores")
        if not isinstance(row_scores, dict):
            raise LabValidationError(f"{scores_path}:{number}: scores must be an object")
        unknown = set(row_scores) - set(dimension_ids)
        if unknown:
            raise LabValidationError(
                f"{scores_path}:{number}: unknown dimensions {', '.join(sorted(unknown))}"
            )
        missing = set(dimension_ids) - set(row_scores)
        if missing:
            raise LabValidationError(
                f"{scores_path}:{number}: missing dimensions {', '.join(sorted(missing))}"
            )
        for dimension_id, score in row_scores.items():
            if isinstance(score, bool) or not isinstance(score, (int, float)):
                raise LabValidationError(
                    f"{scores_path}:{number}: '{dimension_id}' score is not numeric"
                )
            if score < minimum or score > maximum:
                raise LabValidationError(
                    f"{scores_path}:{number}: '{dimension_id}' score outside scale"
                )
            values[dimension_id].append(float(score))

    summary_dimensions: dict[str, Any] = {}
    normalized_values: list[float] = []
    for dimension_id in dimension_ids:
        dimension_values = values[dimension_id]
        if not dimension_values:
            summary_dimensions[dimension_id] = {"count": 0, "mean": None, "quality": None}
            continue
        mean = sum(dimension_values) / len(dimension_values)
        if dimensions[dimension_id]["direction"] == "higher_is_better":
            quality = (mean - minimum) / (maximum - minimum)
        else:
            quality = (maximum - mean) / (maximum - minimum)
        normalized_values.append(quality)
        summary_dimensions[dimension_id] = {
            "count": len(dimension_values),
            "mean": round(mean, 4),
            "quality": round(quality, 4),
        }

    return {
        "schema_version": SCHEMA_VERSION,
        "records": len(rows),
        "overall_quality": round(sum(normalized_values) / len(normalized_values), 4),
        "dimensions": summary_dimensions,
    }
