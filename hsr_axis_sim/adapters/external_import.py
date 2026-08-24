from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from hsr_axis_sim.adapters.source_models import (
    ImportReport,
    RawExternalCharacter,
)
from hsr_axis_sim.sim.data_schema import CharacterSpec, validate_effect_spec


def load_raw_external_character(path: str | Path) -> RawExternalCharacter:
    with Path(path).open(encoding="utf-8") as raw_file:
        return RawExternalCharacter.from_dict(json.load(raw_file))


def normalize_external_character(
    raw: RawExternalCharacter,
) -> tuple[dict[str, Any], ImportReport]:
    report = ImportReport(
        source=raw.source,
        source_character_id=raw.source_character_id,
        normalized_id=raw.normalized_id,
    )

    normalized = {
        "id": raw.normalized_id,
        "name": raw.name,
        "team": raw.team,
        "element": raw.element,
        "path": raw.path,
        "metadata": {
            "imported_from": raw.source,
            "source_version": raw.source_version,
            "source_character_id": raw.source_character_id,
            "importer_task": "HSR-AXIS-001Q",
        },
        "base_stats": raw.base_stats.to_normalized_dict(),
        "skills": [],
        "triggers": [],
    }

    for note_index, note in enumerate(raw.unparsed_notes):
        report.add_warning(
            "unparsed_note",
            str(note),
            path=f"unparsed_notes[{note_index}]",
        )

    for skill_index, raw_skill in enumerate(raw.skills):
        effects = _valid_effects(
            raw_skill.effects,
            report,
            path_prefix=f"skills[{skill_index}].effects",
        )
        normalized["skills"].append(
            {
                "id": raw_skill.id,
                "name": raw_skill.name,
                "skill_type": raw_skill.skill_type,
                "target_type": raw_skill.target_type,
                "sp_delta": raw_skill.sp_delta,
                "energy_delta": raw_skill.energy_delta,
                "ends_turn": raw_skill.ends_turn,
                "effects": effects,
            }
        )
    report.skills_imported = len(normalized["skills"])

    for trigger_index, raw_trigger in enumerate(raw.triggers):
        effects = _valid_effects(
            raw_trigger.effects,
            report,
            path_prefix=f"triggers[{trigger_index}].effects",
        )
        normalized["triggers"].append(
            {
                "id": raw_trigger.id,
                "owner_id": raw_trigger.owner_id,
                "event_type": raw_trigger.event_type,
                "condition": dict(raw_trigger.condition),
                "effects": effects,
                "max_triggers_per_action": raw_trigger.max_triggers_per_action,
                "enabled": raw_trigger.enabled,
            }
        )

    CharacterSpec.from_dict(normalized)
    return normalized, report


def write_normalized_character(
    raw_path: str | Path,
    output_path: str | Path,
) -> ImportReport:
    raw = load_raw_external_character(raw_path)
    normalized, report = normalize_external_character(raw)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as output_file:
        json.dump(normalized, output_file, indent=2)
        output_file.write("\n")
    return report


def _valid_effects(
    effects: list[dict[str, Any]],
    report: ImportReport,
    path_prefix: str,
) -> list[dict[str, Any]]:
    valid_effects: list[dict[str, Any]] = []
    for effect_index, effect in enumerate(effects):
        try:
            validate_effect_spec(effect)
        except ValueError as exc:
            report.add_warning(
                "unsupported_effect",
                str(exc),
                path=f"{path_prefix}[{effect_index}]",
            )
            continue
        valid_effects.append(dict(effect))
    return valid_effects


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Normalize an offline external-style character fixture."
    )
    parser.add_argument("--input", required=True, help="Raw external fixture JSON path.")
    parser.add_argument("--output", required=True, help="Normalized character JSON path.")
    args = parser.parse_args(argv)

    report = write_normalized_character(args.input, args.output)
    print(f"source: {report.source}")
    print(f"source_character_id: {report.source_character_id}")
    print(f"normalized_id: {report.normalized_id}")
    print(f"skills_imported: {report.skills_imported}")
    print(f"warnings: {len(report.warnings)}")
    for warning in report.warnings:
        location = f" at {warning.path}" if warning.path else ""
        print(f"- {warning.code}{location}: {warning.message}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
