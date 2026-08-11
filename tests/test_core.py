import json
import tempfile
import unittest
from pathlib import Path

from style_attractor_lab.core import (
    LabValidationError,
    assemble_recipe,
    create_run,
    load_document,
    summarize_scores,
    validate_recipe,
    validate_repository,
)


ROOT = Path(__file__).resolve().parents[1]


class RepositoryTests(unittest.TestCase):
    def test_checked_in_repository_is_valid(self):
        self.assertEqual(
            validate_repository(ROOT),
            {"attractors": 4, "recipes": 1, "rubrics": 1, "prompts": 12},
        )

    def test_compiler_is_deterministic_and_includes_guards(self):
        first = assemble_recipe(ROOT, "recipes/balanced_direct.yaml")
        second = assemble_recipe(ROOT, "recipes/balanced_direct.yaml")
        self.assertEqual(first, second)
        self.assertIn("2ch reaction logic — weight 0.40", first)
        self.assertIn("Avoid forum_cosplay", first)
        self.assertIn("Task correctness", first)

    def test_recipe_rejects_non_normalized_weights(self):
        record = load_document(ROOT / "recipes" / "balanced_direct.yaml")
        record["attractors"][0]["weight"] = 0.39
        with self.assertRaisesRegex(LabValidationError, "not 1.0"):
            validate_recipe(record, Path("broken.yaml"))

    def test_run_bundle_is_frozen_with_hashes(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "run"
            create_run(ROOT, "recipes/balanced_direct.yaml", "model-test", output)
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["recipe_id"], "balanced_direct")
            self.assertEqual(manifest["model"], "model-test")
            self.assertEqual(
                set(manifest["files"]),
                {"compiled_style.md", "recipe.yaml", "prompts.jsonl", "rubric.yaml"},
            )
            self.assertTrue((output / "recipe.yaml").exists())
            self.assertTrue((output / "outputs.jsonl").exists())
            self.assertTrue((output / "scores.jsonl").exists())

    def test_summary_respects_dimension_direction(self):
        with tempfile.TemporaryDirectory() as temp:
            scores = Path(temp) / "scores.jsonl"
            scores.write_text(
                json.dumps(
                    {
                        "prompt_id": "one",
                        "scores": {
                            "task_fidelity": 4,
                            "reaction_priority": 4,
                            "ceremony_control": 4,
                            "context_reuse": 4,
                            "uncertainty_honesty": 4,
                            "closure_compulsion": 0,
                            "caricature_drift": 0,
                            "forced_wit": 0,
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            summary = summarize_scores(scores, ROOT / "evals" / "rubric.yaml")
            self.assertEqual(summary["overall_quality"], 1.0)
            self.assertEqual(summary["dimensions"]["closure_compulsion"]["quality"], 1.0)

    def test_summary_rejects_partial_score_rows(self):
        with tempfile.TemporaryDirectory() as temp:
            scores = Path(temp) / "scores.jsonl"
            scores.write_text(
                json.dumps({"prompt_id": "one", "scores": {"task_fidelity": 4}}) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(LabValidationError, "missing dimensions"):
                summarize_scores(scores, ROOT / "evals" / "rubric.yaml")

    def test_schema_documents_are_valid_json(self):
        for schema_path in (ROOT / "schemas").glob("*.json"):
            value = json.loads(schema_path.read_text(encoding="utf-8"))
            self.assertEqual(value["$schema"], "https://json-schema.org/draft/2020-12/schema")


if __name__ == "__main__":
    unittest.main()
