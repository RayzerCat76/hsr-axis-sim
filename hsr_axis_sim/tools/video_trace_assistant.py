from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path

from hsr_axis_sim.tools.video_trace_models import (
    DeclaredAction,
    FrameRecord,
    VideoSourceMetadata,
    VideoTraceAssistantConfig,
)


DEFAULT_TEAM = ["那刻夏", "停云", "佩拉", "记忆主"]
DEFAULT_PREBATTLE = "佩拉秘技开怪"
DEFAULT_DECLARED_SEQUENCE = [
    DeclaredAction(1, "停云", "终结技"),
    DeclaredAction(2, "佩拉", "战技"),
    DeclaredAction(3, "记忆主", "战技"),
    DeclaredAction(4, "停云", "战技"),
    DeclaredAction(5, "佩拉", "终结技"),
    DeclaredAction(6, "那刻夏", "终结技"),
    DeclaredAction(7, "那刻夏", "普攻 + 额外战技"),
    DeclaredAction(8, "迷迷", "拉条那刻夏"),
    DeclaredAction(9, "那刻夏", "战技 + 额外战技"),
]


class FfmpegUnavailableError(RuntimeError):
    pass


def generate_timestamps(start: float, end: float, interval: float) -> list[float]:
    if interval <= 0:
        raise ValueError("interval must be greater than zero.")
    if end < start:
        raise ValueError("end must be greater than or equal to start.")

    timestamps: list[float] = []
    current = start
    epsilon = interval / 1000
    while current <= end + epsilon:
        timestamps.append(round(current, 3))
        current += interval
    return timestamps


def timestamp_label(timestamp: float) -> str:
    return f"{timestamp:05.1f}"


def frame_id_for_timestamp(timestamp: float) -> str:
    return f"t_{timestamp_label(timestamp)}"


def build_frame_records(
    timestamps: list[float],
    output_dir: Path,
) -> list[FrameRecord]:
    return [
        FrameRecord(
            frame_id=frame_id_for_timestamp(timestamp),
            timestamp_seconds=timestamp,
            timestamp_label=timestamp_label(timestamp),
            frame_path=Path("frames") / f"{frame_id_for_timestamp(timestamp)}.jpg",
        )
        for timestamp in timestamps
    ]


def extract_frames(
    video_path: Path,
    output_dir: Path,
    timestamps: list[float],
    extraction_mode: str = "batch",
    ffmpeg_timeout_seconds: float = 30,
) -> list[FrameRecord]:
    if shutil.which("ffmpeg") is None:
        raise FfmpegUnavailableError(
            "ffmpeg was not found on PATH. Install ffmpeg or provide it before extracting frames."
        )

    frames_dir = output_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    records = build_frame_records(timestamps, output_dir)
    if extraction_mode == "batch":
        _extract_frames_batch(
            video_path=video_path,
            output_dir=output_dir,
            records=records,
            interval=_infer_interval(timestamps),
            timeout=ffmpeg_timeout_seconds,
        )
    elif extraction_mode == "per_frame":
        _extract_frames_per_frame(
            video_path=video_path,
            output_dir=output_dir,
            records=records,
            timeout=ffmpeg_timeout_seconds,
        )
    else:
        raise ValueError(f"Unknown extraction mode: {extraction_mode!r}.")
    validate_extracted_frames(output_dir, records)
    return records


def _extract_frames_per_frame(
    video_path: Path,
    output_dir: Path,
    records: list[FrameRecord],
    timeout: float,
) -> None:
    for record in records:
        command = build_per_frame_ffmpeg_command(video_path, output_dir / record.frame_path, record)
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                f"ffmpeg failed for timestamp {record.timestamp_seconds}: {completed.stderr.strip()}"
            )


def _extract_frames_batch(
    video_path: Path,
    output_dir: Path,
    records: list[FrameRecord],
    interval: float,
    timeout: float,
) -> None:
    if not records:
        return
    with tempfile.TemporaryDirectory(prefix="hsr_axis_frames_") as tmp_dir_name:
        tmp_dir = Path(tmp_dir_name)
        command = build_batch_ffmpeg_command(
            video_path=video_path,
            tmp_dir=tmp_dir,
            start=records[0].timestamp_seconds,
            end=records[-1].timestamp_seconds,
            interval=interval,
        )
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if completed.returncode != 0:
            raise RuntimeError(f"ffmpeg batch extraction failed: {completed.stderr.strip()}")
        map_batch_frames_to_records(tmp_dir, output_dir, records)


def build_per_frame_ffmpeg_command(
    video_path: Path,
    output_path: Path,
    record: FrameRecord,
) -> list[str]:
    return [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-nostdin",
        "-y",
        "-ss",
        f"{record.timestamp_seconds:.3f}",
        "-i",
        str(video_path),
        "-frames:v",
        "1",
        "-update",
        "1",
        "-q:v",
        "2",
        str(output_path),
    ]


def build_batch_ffmpeg_command(
    video_path: Path,
    tmp_dir: Path,
    start: float,
    end: float,
    interval: float,
) -> list[str]:
    duration = max(0, end - start) + interval / 2
    fps = 1 / interval
    return [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-nostdin",
        "-y",
        "-ss",
        f"{start:.3f}",
        "-i",
        str(video_path),
        "-t",
        f"{duration:.3f}",
        "-vf",
        f"fps={fps:.8f}",
        "-q:v",
        "2",
        str(tmp_dir / "frame_%06d.jpg"),
    ]


def map_batch_frames_to_records(
    tmp_dir: Path,
    output_dir: Path,
    records: list[FrameRecord],
) -> None:
    generated = sorted(tmp_dir.glob("frame_*.jpg"))
    if len(generated) < len(records):
        raise RuntimeError(
            "ffmpeg batch extraction produced too few frames: "
            f"expected {len(records)}, got {len(generated)}."
        )
    frames_dir = output_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    for generated_path, record in zip(generated, records):
        shutil.copyfile(generated_path, output_dir / record.frame_path)


def validate_extracted_frames(output_dir: Path, records: list[FrameRecord]) -> None:
    missing = [
        str(record.frame_path)
        for record in records
        if not (output_dir / record.frame_path).exists()
    ]
    if missing:
        raise RuntimeError(
            f"Missing extracted frame(s): expected {len(records)}, missing {len(missing)}: {missing}"
        )


def _infer_interval(timestamps: list[float]) -> float:
    if len(timestamps) < 2:
        return 1
    return timestamps[1] - timestamps[0]


def write_frame_index_csv(path: Path, records: list[FrameRecord]) -> None:
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(
            [
                "frame_id",
                "timestamp_seconds",
                "timestamp_label",
                "frame_path",
                "annotation_status",
                "notes",
            ]
        )
        for record in records:
            writer.writerow(
                [
                    record.frame_id,
                    record.timestamp_seconds,
                    record.timestamp_label,
                    str(record.frame_path),
                    record.annotation_status,
                    record.notes,
                ]
            )


def write_trace_annotation_worksheet(
    path: Path,
    config: VideoTraceAssistantConfig,
    records: list[FrameRecord],
) -> None:
    lines = [
        f"# Trace Annotation Worksheet: {config.trace_name}",
        "",
        "## Source Metadata",
        f"- Platform: {config.source.platform}",
        f"- URL: {config.source.url}",
        f"- Title: {config.source.video_title}",
        f"- Uploader: {config.source.uploader}",
        f"- Notes: {config.source.notes}",
        "",
        "## Selected Video Range",
        f"- Start: {config.start:.3f}s",
        f"- End: {config.end:.3f}s",
        f"- Interval: {config.interval:.3f}s",
        "",
        "## Frame Index",
        "| Frame ID | Timestamp | Frame Path | Status | Notes |",
        "|---|---:|---|---|---|",
    ]
    for record in records:
        lines.append(
            f"| {record.frame_id} | {record.timestamp_label}s | "
            f"{record.frame_path} | {record.annotation_status} | {record.notes} |"
        )

    lines.extend(
        [
            "",
            "## Known Opening Sequence v0.3",
        ]
    )
    for action in config.declared_sequence:
        lines.append(f"{action.step}. {action.actor}{action.action}")

    lines.extend(
        [
            "",
            "## Human Action Table",
            "| step | video_timestamp | actor | action | target | sp_before | sp_after | energy_before | energy_after | hp_change | toughness_change | forced_rng | notes |",
            "|---:|---|---|---|---|---:|---:|---:|---:|---|---|---|---|",
        ]
    )
    for action in config.declared_sequence:
        lines.append(
            f"| {action.step} |  | {action.actor} | {action.action} |  |  |  |  |  |  |  |  |  |"
        )

    lines.extend(
        [
            "",
            "## Missing Fields Checklist",
            "- Exact targets for every action",
            "- Skill point values before and after each action",
            "- Energy values before and after each action",
            "- HP deltas",
            "- Toughness deltas",
            "- Forced RNG outcomes",
            "- Exact interrupt/current-turn/bonus-action semantics",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_draft_trace_json(
    path: Path,
    config: VideoTraceAssistantConfig,
    records: list[FrameRecord],
) -> None:
    data = {
        "name": config.trace_name,
        "status": "intake_draft",
        "replay_ready": False,
        "source": {
            "type": "manual_video_trace_video_assistant",
            "platform": config.source.platform,
            "url": config.source.url,
            "video_title": config.source.video_title,
            "uploader": config.source.uploader,
            "notes": config.source.notes,
        },
        "video_range": {
            "start": config.start,
            "end": config.end,
            "interval": config.interval,
        },
        "team_notes": list(config.team),
        "prebattle": config.prebattle,
        "declared_sequence": [asdict(action) for action in config.declared_sequence],
        "frames": [
            {
                "frame_id": record.frame_id,
                "timestamp_seconds": record.timestamp_seconds,
                "timestamp_label": record.timestamp_label,
                "frame_path": str(record.frame_path),
                "annotation_status": record.annotation_status,
                "notes": record.notes,
            }
            for record in records
        ],
        "steps": [
            {
                "step": action.step,
                "declared_actor": action.actor,
                "declared_action": action.action,
                "video_timestamp": "",
                "target": "unknown",
                "sp_before": None,
                "sp_after": None,
                "energy_before": None,
                "energy_after": None,
                "hp_change": None,
                "toughness_change": None,
                "forced_rng": {},
                "notes": "Requires human completion.",
            }
            for action in config.declared_sequence
        ],
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_readme(path: Path, config: VideoTraceAssistantConfig) -> None:
    lines = [
        f"# Video Trace Intake Package: {config.trace_name}",
        "",
        "This package was generated offline from a local video file.",
        "",
        "It is not replay-ready. Do not add `draft_trace.json` to the locked regression manifest.",
        "",
        "Generated files:",
        "- `frames/`: sampled video frames",
        "- `frame_index.csv`: frame timestamps and annotation status",
        "- `trace_annotation_worksheet.md`: human annotation worksheet",
        "- `draft_trace.json`: structured draft with placeholders",
        "",
        "Remaining work:",
        "- Fill targets",
        "- Fill SP, energy, HP, and toughness changes",
        "- Fill forced RNG outcomes",
        "- Confirm interrupt/current-turn/bonus-action semantics",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def generate_video_trace_package(
    config: VideoTraceAssistantConfig,
    extraction_mode: str = "batch",
    ffmpeg_timeout_seconds: float = 30,
) -> list[FrameRecord]:
    config.output_dir.mkdir(parents=True, exist_ok=True)
    timestamps = generate_timestamps(config.start, config.end, config.interval)
    records = extract_frames(
        config.video,
        config.output_dir,
        timestamps,
        extraction_mode=extraction_mode,
        ffmpeg_timeout_seconds=ffmpeg_timeout_seconds,
    )
    write_frame_index_csv(config.output_dir / "frame_index.csv", records)
    write_trace_annotation_worksheet(
        config.output_dir / "trace_annotation_worksheet.md",
        config,
        records,
    )
    write_draft_trace_json(config.output_dir / "draft_trace.json", config, records)
    write_readme(config.output_dir / "README.md", config)
    return records


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate an offline video trace intake package.")
    parser.add_argument("--video", required=True)
    parser.add_argument("--trace-name", required=True)
    parser.add_argument("--start", type=float, required=True)
    parser.add_argument("--end", type=float, required=True)
    parser.add_argument("--interval", type=float, required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--source-platform", required=True)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--video-title", required=True)
    parser.add_argument("--uploader", required=True)
    parser.add_argument("--notes", default="")
    parser.add_argument(
        "--extraction-mode",
        choices=["batch", "per_frame"],
        default="batch",
    )
    parser.add_argument("--ffmpeg-timeout-seconds", type=float, default=30)
    args = parser.parse_args(argv)

    config = VideoTraceAssistantConfig(
        video=Path(args.video),
        trace_name=args.trace_name,
        start=args.start,
        end=args.end,
        interval=args.interval,
        output_dir=Path(args.output_dir),
        source=VideoSourceMetadata(
            platform=args.source_platform,
            url=args.source_url,
            video_title=args.video_title,
            uploader=args.uploader,
            notes=args.notes,
        ),
        team=list(DEFAULT_TEAM),
        prebattle=DEFAULT_PREBATTLE,
        declared_sequence=list(DEFAULT_DECLARED_SEQUENCE),
    )
    try:
        records = generate_video_trace_package(
            config,
            extraction_mode=args.extraction_mode,
            ffmpeg_timeout_seconds=args.ffmpeg_timeout_seconds,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Generated video trace intake package at {config.output_dir} ({len(records)} frames).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
