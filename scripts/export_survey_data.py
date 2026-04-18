#!/usr/bin/env python3
"""Export itineraries as formatted text for WeChat survey (腾讯问卷).

Outputs CSV with scenario name, group, and formatted itinerary text.
"""

import asyncio
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "backend"))

from db.init_db import AsyncSessionFactory
from models.database import ItineraryRow, Scenario
from sqlalchemy import select


def format_itinerary_for_survey(itinerary_data: dict) -> str:
    """Format Itinerary as readable survey text."""
    lines = [f"# {itinerary_data.get('title', '行程')}", "", itinerary_data.get("summary", ""), ""]
    for day in itinerary_data.get("days", []):
        lines.append(f"## 第{day['day_number']}天：{day['theme']}")
        for poi in day.get("pois", []):
            lines.append(f"- {poi['time_slot']} {poi['name']}")
            if poi.get("highlight_note"):
                lines.append(f"  💡 {poi['highlight_note']}")
        lines.append("")
    return "\n".join(lines)


async def main():
    async with AsyncSessionFactory() as sess:
        scenarios_result = await sess.execute(select(Scenario))
        scenarios = {s.id: s for s in scenarios_result.scalars().all()}

        itin_result = await sess.execute(select(ItineraryRow))
        itineraries = list(itin_result.scalars().all())

        by_scenario = {}
        for itin in itineraries:
            by_scenario.setdefault(itin.scenario_id, {})[itin.group] = itin

        output_path = Path("data/survey-export.csv")
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["scenario_id", "scenario_name", "group", "itinerary_text"])
            for scen_id, groups in by_scenario.items():
                scen = scenarios.get(scen_id)
                if not scen:
                    continue
                for group, itin in groups.items():
                    parsed = json.loads(itin.parsed_itinerary)
                    text = format_itinerary_for_survey(parsed)
                    writer.writerow([scen_id, scen.name, group, text])

        summary_path = Path("data/survey-summary.json")
        summary = {}
        for scen_id, groups in by_scenario.items():
            scen = scenarios.get(scen_id, None)
            summary[scen_id] = {
                "scenario_name": scen.name if scen else scen_id,
                "itinerary_ids": {g: i.id for g, i in groups.items()},
            }
        summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2))

        print(f"Exported {len(itineraries)} itineraries to {output_path}")
        print(f"Survey summary saved to {summary_path}")


if __name__ == "__main__":
    asyncio.run(main())
