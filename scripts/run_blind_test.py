#!/usr/bin/env python3
"""CLI tool for blind test execution.

Usage:
  python scripts/run_blind_test.py import <csv_file>   Import survey results
  python scripts/run_blind_test.py analyze              Run analysis and print report
  python scripts/run_blind_test.py guide                Print execution runbook
  python scripts/run_blind_test.py validate <csv_file>  Validate survey data quality
"""

import argparse
import asyncio
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "backend"))

from db.init_db import AsyncSessionFactory
from models.database import TestResult
from services.results_analyzer import ResultsAnalyzer


async def import_results(csv_path: str):
    """Import results from 腾讯问卷 CSV export."""
    summary_path = Path("data/survey-summary.json")
    summary = json.loads(summary_path.read_text()) if summary_path.exists() else {}

    count = 0
    async with AsyncSessionFactory() as sess:
        for row in csv.DictReader(open(csv_path, encoding="utf-8")):
            participant_id = row.get("participant_id", f"p_{count}")
            for col, val in row.items():
                if col.startswith("scenario_") and col.endswith("_choice") and val.strip():
                    scen_key = col.replace("_choice", "").replace("scenario_", "")
                    choice = val.strip()  # "A", "B", or "C"
                    reason_col = f"{col.replace('_choice', '_reason')}"
                    reason = row.get(reason_col, "")

                    scen_data = summary.get(scen_key, {})
                    itinerary_ids = scen_data.get("itinerary_ids", {})
                    preferred_id = itinerary_ids.get(choice, "")

                    tr = TestResult(
                        id=f"{participant_id}_{scen_key}",
                        scenario_id=scen_key,
                        participant_id=participant_id,
                        group=choice,
                        preferred_itinerary_id=preferred_id,
                        preference_reason=reason,
                    )
                    sess.add(tr)
                    count += 1
        await sess.commit()
    print(f"Imported {count} results")


async def analyze():
    """Run analysis on current TestResult table."""
    async with AsyncSessionFactory() as sess:
        analyzer = ResultsAnalyzer(sess)
        report = await analyzer.analyze()
        print("\n=== BLIND TEST RESULTS ===")
        print(f"Total responses: {report.total_responses}")
        print(f"A preference rate: {report.aggregated_a_rate:.1%}")
        print(f"Verdict: {report.verdict}")
        print(f"Reason: {report.verdict_reason}")
        print(f"highlight_note effect: {report.highlight_note_effect}")
        print("\nPer-scenario:")
        for s in report.scenario_results:
            print(f"  {s.scenario_id}: A={s.a_count} B={s.b_count} C={s.c_count} (A rate: {s.a_rate:.1%})")


def guide():
    print("""
=== 拾途 SOUL Blind Test Execution Runbook ===

1. PREPARE SURVEY (问卷设计)
   - Create 腾讯问卷 survey with 4 scenario questions
   - Each question: "A/B/C哪个行程更符合你的偏好？"
   - Attach formatted itinerary text for groups A, B, C
   - Randomize order within each question (D-06)

2. COLLECT RESPONSES (数据收集)
   - Target: 25 participants via 朋友圈/好友邀请
   - Each participant completes all 4 scenarios
   - Export results as CSV from 腾讯问卷

3. IMPORT DATA
   python scripts/run_blind_test.py import survey_results.csv

4. RUN ANALYSIS
   python scripts/run_blind_test.py analyze

5. DECISION
   - PASS (≥60%): Proceed to Phase 1 engineering
   - RETRY (40-59%): Improve SOUL prompt, rerun blind test
   - PLAN_B (<40%): Activate Plan B (narrow category or human-AI hybrid)
""")


async def validate(csv_path: str):
    """Validate survey CSV format and completeness."""
    reader = csv.DictReader(open(csv_path, encoding="utf-8"))
    rows = list(reader)
    required_scenarios = ["scenario_1", "scenario_2", "scenario_3", "scenario_4"]
    issues = []
    for i, row in enumerate(rows):
        for scen in required_scenarios:
            choice = row.get(f"{scen}_choice", "").strip()
            if choice not in ("A", "B", "C"):
                issues.append(f"Row {i + 1}: invalid choice '{choice}' for {scen}")
    if issues:
        for issue in issues[:10]:
            print(f"WARNING: {issue}")
    else:
        print(f"All {len(rows)} rows valid")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")

    import_parser = sub.add_parser("import", help="Import CSV")
    import_parser.add_argument("csv_file")

    sub.add_parser("analyze", help="Run analysis")
    sub.add_parser("guide", help="Show runbook")

    validate_parser = sub.add_parser("validate", help="Validate CSV")
    validate_parser.add_argument("csv_file")

    args = parser.parse_args()

    if args.command == "import":
        asyncio.run(import_results(args.csv_file))
    elif args.command == "analyze":
        asyncio.run(analyze())
    elif args.command == "guide":
        guide()
    elif args.command == "validate":
        asyncio.run(validate(args.csv_file))
    else:
        parser.print_help()
