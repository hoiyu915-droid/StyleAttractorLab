"""Validation, assembly, run freezing, and score summaries."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "0.1"
ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
LEVELS = {"very_low", "low", "moderate", "high", "very_high"}


class LabValidationError(ValueError):
    """Raised when a lab document or repository violates the v0.1 contract."""


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
    if not isinstance(record["name"], str) or not record["name"].strip():
        raise LabValidationError(f"{source}: 'name' must be a non-empty string")
    if not isinstance(record["summary"], str) or not record["summary"].strip():
        raise LabValidationError(f"{source}: 'summary' must be a non-empty string")
    _string_list(record["reaction_path"], source, "reaction_path")
    _string_list(record["attention"], source, "attention")
    _string_list(record["prompt_cues"], source, "prompt_cues")

    for section in ("syntax", "social_contract", "epistemics", "closure", "affect"):
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
            if isinstance(setting, str) and setting.endswith("_low"):
                if setting not in LEVELS:
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
        ("schema_version", "id", "name", "attractors", "suppressions", "guardrails"),
        source,
    )
    if record["schema_version"] != SCHEMA_VERSION:
        raise LabValidationError(f"{source}: unsupported schema_version")
    recipe_id = _validate_id(record["id"], source)
    if not isinstance(record["name"], str) or not record["name"].strip():
        raise LabValidationError(f"{source}: 'name' must be a non-empty string")
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
    if not recipes:
        raise LabValidationError(f"{root}: no recipes found")

    rubric_paths = sorted((root / "evals").glob("rubric*.yaml"))
    if not rubric_paths:
        raise LabValidationError(f"{root}: no rubric found")
    for path in rubric_paths:
        validate_rubric(load_document(path), path)

    prompts_path = root / "evals" / "prompts.jsonl"
    prompts = _read_jsonl(prompts_path)
    if not prompts:
        raise LabValidationError(f"{prompts_path}: no prompts found")
    prompt_ids: set[str] = set()
    required_prompt_fields = {"id", "category", "language", "prompt"}
    for number, prompt in enumerate(prompts, start=1):
        missing = required_prompt_fields - prompt.keys()
        if missing:
            raise LabValidationError(
                f"{prompts_path}:{number}: missing {', '.join(sorted(missing))}"
            )
        prompt_id = _validate_id(prompt["id"], prompts_path, "prompt.id")
        if prompt_id in prompt_ids:
            raise LabValidationError(f"{prompts_path}: duplicate prompt id '{prompt_id}'")
        prompt_ids.add(prompt_id)

    return {
        "attractors": len(attractors),
        "recipes": len(recipes),
        "rubrics": len(rubric_paths),
        "prompts": len(prompts),
    }


def _catalog(root: Path) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for path in sorted((root / "attractors").glob("*.yaml")):
        record = load_document(path)
        result[validate_attractor(record, path)] = record
    return result


def assemble_recipe(root: str | Path, recipe_path: str | Path) -> str:
    root = Path(root).resolve()
    recipe_path = Path(recipe_path)
    if not recipe_path.is_absolute():
        recipe_path = root / recipe_path
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
    recipe = load_document(recipe_path)
    validate_recipe(recipe, recipe_path)
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=False)

    compiled_path = output_dir / "compiled_style.md"
    compiled_path.write_text(assemble_recipe(root, recipe_path), encoding="utf-8")
    recipe_target = output_dir / "recipe.yaml"
    shutil.copy2(recipe_path, recipe_target)
    prompts_source = root / "evals" / "prompts.jsonl"
    rubric_source = root / "evals" / "rubric.yaml"
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
        "source_recipe": str(recipe_path.relative_to(root)),
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
    (output_dir / "README.md").write_text(
        "# Frozen run bundle\n\n"
        "Do not edit the compiled style, prompts, rubric, or manifest after generation starts.\n"
        "Write one output record per prompt to `outputs.jsonl`, then one score record per "
        "output to `scores.jsonl`. Every score record needs `prompt_id` and a complete "
        "`scores` object.\n\n"
        "```json\n"
        '{"prompt_id":"technical_explanation","output":"...","metadata":{"seed":1}}\n'
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
