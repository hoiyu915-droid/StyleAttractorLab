"""Command-line interface for the lab."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .core import (
    LabValidationError,
    assemble_recipe,
    catalog_records,
    create_run,
    summarize_scores,
    validate_repository,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="salab", description="Style attractor experiment utilities")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="validate catalog, recipes, and eval contracts")
    validate.add_argument("root", nargs="?", default=".")

    catalog = subparsers.add_parser("catalog", help="list available attractors")
    catalog.add_argument("--root", default=".")
    catalog.add_argument(
        "--class",
        dest="attractor_class",
        choices=["discourse_attractor", "interaction_attractor", "relational_attractor"],
    )
    catalog.add_argument("--status", choices=["provisional", "experimental"])
    catalog.add_argument("--risk", choices=["low", "moderate", "high"])
    catalog.add_argument("--json", action="store_true")

    assemble = subparsers.add_parser("assemble", help="compile one recipe into a prompt layer")
    assemble.add_argument("recipe")
    assemble.add_argument("--root", default=".")
    assemble.add_argument("--output")

    init_run = subparsers.add_parser("init-run", help="freeze a self-contained experiment bundle")
    init_run.add_argument("recipe")
    init_run.add_argument("--root", default=".")
    init_run.add_argument("--model", required=True)
    init_run.add_argument("--output", required=True)

    summarize = subparsers.add_parser("summarize", help="summarize rubric scores")
    summarize.add_argument("scores")
    summarize.add_argument("--rubric", required=True)
    summarize.add_argument("--output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "validate":
            summary = validate_repository(args.root)
            print(json.dumps({"status": "valid", **summary}, indent=2))
            return 0
        if args.command == "catalog":
            records = catalog_records(
                args.root,
                attractor_class=args.attractor_class,
                status=args.status,
                risk_level=args.risk,
            )
            if args.json:
                print(json.dumps(records, ensure_ascii=False, indent=2))
            else:
                print("ID\tCLASS\tSTATUS\tRISK\tNAME")
                for record in records:
                    print(
                        "\t".join(
                            [
                                record["id"],
                                record["class"],
                                record["status"],
                                record["risk_level"],
                                record["name"],
                            ]
                        )
                    )
            return 0
        if args.command == "assemble":
            compiled = assemble_recipe(args.root, args.recipe)
            if args.output:
                output = Path(args.output)
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(compiled, encoding="utf-8")
            else:
                print(compiled, end="")
            return 0
        if args.command == "init-run":
            run_path = create_run(args.root, args.recipe, args.model, args.output)
            print(run_path)
            return 0
        if args.command == "summarize":
            summary = summarize_scores(args.scores, args.rubric)
            payload = json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
            if args.output:
                Path(args.output).write_text(payload, encoding="utf-8")
            else:
                print(payload, end="")
            return 0
    except (LabValidationError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 2
