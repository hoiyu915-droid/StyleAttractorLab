import json
import tempfile
import unittest
from pathlib import Path

from style_attractor_lab.core import (
    LabValidationError,
    assemble_recipe,
    catalog_records,
    create_run,
    load_document,
    summarize_scores,
    validate_attractor,
    validate_recipe,
    validate_repository,
)


ROOT = Path(__file__).resolve().parents[1]


class RepositoryTests(unittest.TestCase):
    def test_checked_in_repository_is_valid(self):
        self.assertEqual(
            validate_repository(ROOT),
            {
                "attractors": 17,
                "recipes": 8,
                "rubrics": 2,
                "prompt_suites": 2,
                "prompts": 28,
                "unreferenced_attractors": 0,
            },
        )

    def test_compiler_is_deterministic_and_includes_guards(self):
        first = assemble_recipe(ROOT, "recipes/balanced_direct.yaml")
        second = assemble_recipe(ROOT, "recipes/balanced_direct.yaml")
        self.assertEqual(first, second)
        self.assertIn("2ch reaction logic — weight 0.40", first)
        self.assertIn("Avoid forum_cosplay", first)
        self.assertIn("Class: discourse_attractor", first)
        self.assertIn("Task correctness", first)

    def test_catalog_lists_every_class_and_filters(self):
        all_records = catalog_records(ROOT)
        discourse = catalog_records(ROOT, attractor_class="discourse_attractor")
        interaction = catalog_records(ROOT, attractor_class="interaction_attractor")
        relational = catalog_records(ROOT, attractor_class="relational_attractor")
        high_risk = catalog_records(ROOT, risk_level="high")
        self.assertEqual(len(all_records), 17)
        self.assertEqual(len(discourse), 15)
        self.assertEqual([item["id"] for item in interaction], ["anticipatory_domestic_intimacy"])
        self.assertEqual([item["id"] for item in relational], ["relational_continuity"])
        self.assertEqual([item["id"] for item in high_risk], ["imageboard"])

    def test_class_specific_policy_is_required_and_compiled(self):
        record = load_document(ROOT / "attractors" / "anticipatory_domestic_intimacy.yaml")
        record.pop("interaction_policy")
        with self.assertRaisesRegex(LabValidationError, "interaction_policy"):
            validate_attractor(record, Path("broken.yaml"))
        discourse = load_document(ROOT / "attractors" / "2ch.yaml")
        discourse["interaction_policy"] = {"temporal_continuity": "high"}
        with self.assertRaisesRegex(LabValidationError, "not allowed"):
            validate_attractor(discourse, Path("broken-discourse.yaml"))
        compiled = assemble_recipe(ROOT, "recipes/relational_continuity.yaml")
        self.assertIn("Interaction Policy:", compiled)
        self.assertIn("Relational Policy:", compiled)
        editorial = assemble_recipe(ROOT, "recipes/editorial_edge.yaml")
        self.assertIn("High-risk constraint:", editorial)

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
            self.assertEqual(manifest["source_eval_suite"], "prompts.jsonl")
            self.assertEqual(manifest["source_rubric"], "rubric.yaml")
            self.assertEqual(manifest["prompt_mode"], "single_turn")
            self.assertEqual(
                set(manifest["files"]),
                {"compiled_style.md", "recipe.yaml", "prompts.jsonl", "rubric.yaml"},
            )
            self.assertTrue((output / "recipe.yaml").exists())
            self.assertTrue((output / "outputs.jsonl").exists())
            self.assertTrue((output / "scores.jsonl").exists())

    def test_interaction_run_uses_recipe_selected_suite_and_rubric(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "run"
            create_run(ROOT, "recipes/relational_continuity.yaml", "model-test", output)
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            first_prompt = json.loads(
                (output / "prompts.jsonl").read_text(encoding="utf-8").splitlines()[0]
            )
            rubric = load_document(output / "rubric.yaml")
            self.assertEqual(manifest["source_eval_suite"], "interaction_prompts.jsonl")
            self.assertEqual(manifest["source_rubric"], "rubric_interaction.yaml")
            self.assertEqual(manifest["prompt_mode"], "multi_turn")
            self.assertIn("turns", first_prompt)
            self.assertEqual(rubric["id"], "interaction_trajectory_v02")
            self.assertIn('"output":["...","..."]', (output / "README.md").read_text(encoding="utf-8"))

    def test_invalid_run_fails_before_creating_output(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "run"
            with self.assertRaisesRegex(LabValidationError, "model"):
                create_run(ROOT, "recipes/balanced_direct.yaml", "", output)
            self.assertFalse(output.exists())

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

    def test_interaction_summary_respects_all_directions(self):
        rubric_path = ROOT / "evals" / "rubric_interaction.yaml"
        rubric = load_document(rubric_path)
        perfect = {
            item["id"]: 4 if item["direction"] == "higher_is_better" else 0
            for item in rubric["dimensions"]
        }
        with tempfile.TemporaryDirectory() as temp:
            scores = Path(temp) / "scores.jsonl"
            scores.write_text(
                json.dumps({"prompt_id": "reminder_ritual", "scores": perfect}) + "\n",
                encoding="utf-8",
            )
            summary = summarize_scores(scores, rubric_path)
            self.assertEqual(summary["overall_quality"], 1.0)

    def test_schema_documents_are_valid_json(self):
        for schema_path in (ROOT / "schemas").glob("*.json"):
            value = json.loads(schema_path.read_text(encoding="utf-8"))
            self.assertEqual(value["$schema"], "https://json-schema.org/draft/2020-12/schema")


if __name__ == "__main__":
    unittest.main()
