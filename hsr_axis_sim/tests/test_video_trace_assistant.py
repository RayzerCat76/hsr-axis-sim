import csv
import json
from pathlib import Path

from hsr_axis_sim.tools import video_trace_assistant as assistant
from hsr_axis_sim.tools.video_trace_models import (
    DeclaredAction,
    VideoSourceMetadata,
    VideoTraceAssistantConfig,
)


def make_config(tmp_path):
    return VideoTraceAssistantConfig(
        video=Path("data/video_trace_sources/sample1.mov"),
        trace_name="real_video_trace_001_botu_dilemma_3_4_floor12_side1_opening",
        start=0,
        end=1,
        interval=0.5,
        output_dir=tmp_path,
        source=VideoSourceMetadata(
            platform="bilibili",
            url="https://www.bilibili.com/video/BV1CXtVzaEQB",
            video_title="【3.4博徒困境】全网首发！0+1风套那刻夏逆属性2金0t砂金！",
            uploader="unknown",
            notes="Opening sequence only; intake draft; not replay-ready.",
        ),
        team=["那刻夏", "停云", "佩拉", "记忆主"],
        prebattle="佩拉秘技开怪",
        declared_sequence=[
            DeclaredAction(1, "停云", "终结技"),
            DeclaredAction(2, "佩拉", "战技"),
        ],
    )


def test_timestamp_generation():
    assert assistant.generate_timestamps(0, 1, 0.5) == [0, 0.5, 1.0]


def test_opening_timestamp_generation_count():
    timestamps = assistant.generate_timestamps(0, 16, 0.5)

    assert len(timestamps) == 33
    assert timestamps[0] == 0
    assert timestamps[-1] == 16


def test_csv_writer(tmp_path):
    records = assistant.build_frame_records([0, 0.5], tmp_path)

    assistant.write_frame_index_csv(tmp_path / "frame_index.csv", records)

    with (tmp_path / "frame_index.csv").open(encoding="utf-8", newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))
    assert rows[0]["frame_id"] == "t_000.0"
    assert rows[0]["frame_path"] == "frames/t_000.0.jpg"
    assert rows[0]["annotation_status"] == "pending"


def test_worksheet_writer(tmp_path):
    config = make_config(tmp_path)
    records = assistant.build_frame_records([0], tmp_path)

    assistant.write_trace_annotation_worksheet(
        tmp_path / "trace_annotation_worksheet.md",
        config,
        records,
    )

    content = (tmp_path / "trace_annotation_worksheet.md").read_text(encoding="utf-8")
    assert "## Source Metadata" in content
    assert "## Known Opening Sequence v0.3" in content
    assert "step | video_timestamp | actor | action | target" in content
    assert "Missing Fields Checklist" in content


def test_draft_trace_json_fields(tmp_path):
    config = make_config(tmp_path)
    records = assistant.build_frame_records([0], tmp_path)

    assistant.write_draft_trace_json(tmp_path / "draft_trace.json", config, records)
    data = json.loads((tmp_path / "draft_trace.json").read_text(encoding="utf-8"))

    assert data["status"] == "intake_draft"
    assert data["replay_ready"] is False
    assert data["source"]["platform"] == "bilibili"
    assert data["declared_sequence"][0]["actor"] == "停云"
    assert data["steps"][0]["target"] == "unknown"


def test_ffmpeg_missing_error(tmp_path):
    original_which = assistant.shutil.which
    assistant.shutil.which = lambda name: None
    try:
        try:
            assistant.extract_frames(Path("missing.mov"), tmp_path, [0])
        except assistant.FfmpegUnavailableError as exc:
            assert "ffmpeg was not found" in str(exc)
        else:
            raise AssertionError("Expected FfmpegUnavailableError.")
    finally:
        assistant.shutil.which = original_which


def test_batch_records_use_deterministic_output_names(tmp_path):
    records = assistant.build_frame_records(assistant.generate_timestamps(0, 1, 0.5), tmp_path)

    assert [str(record.frame_path) for record in records] == [
        "frames/t_000.0.jpg",
        "frames/t_000.5.jpg",
        "frames/t_001.0.jpg",
    ]


def test_batch_frame_mapping_copies_temp_frames_to_timestamp_names(tmp_path):
    tmp_frames = tmp_path / "tmp_frames"
    output_dir = tmp_path / "output"
    tmp_frames.mkdir()
    for index in range(1, 4):
        (tmp_frames / f"frame_{index:06d}.jpg").write_bytes(f"fake-{index}".encode())
    records = assistant.build_frame_records([0, 0.5, 1.0], output_dir)

    assistant.map_batch_frames_to_records(tmp_frames, output_dir, records)

    assert (output_dir / "frames" / "t_000.0.jpg").read_bytes() == b"fake-1"
    assert (output_dir / "frames" / "t_000.5.jpg").read_bytes() == b"fake-2"
    assert (output_dir / "frames" / "t_001.0.jpg").read_bytes() == b"fake-3"


def test_batch_frame_mapping_reports_too_few_frames(tmp_path):
    tmp_frames = tmp_path / "tmp_frames"
    output_dir = tmp_path / "output"
    tmp_frames.mkdir()
    (tmp_frames / "frame_000001.jpg").write_bytes(b"fake")
    records = assistant.build_frame_records([0, 0.5], output_dir)

    try:
        assistant.map_batch_frames_to_records(tmp_frames, output_dir, records)
    except RuntimeError as exc:
        assert "expected 2, got 1" in str(exc)
    else:
        raise AssertionError("Expected too-few-frames error.")


def test_per_frame_ffmpeg_command_is_hardened(tmp_path):
    record = assistant.build_frame_records([0], tmp_path)[0]

    command = assistant.build_per_frame_ffmpeg_command(
        Path("sample.mov"),
        tmp_path / record.frame_path,
        record,
    )

    assert "-nostdin" in command
    assert "-loglevel" in command
    assert "error" in command
    assert "-update" in command
    assert "1" in command


def test_batch_ffmpeg_command_uses_single_fps_extraction(tmp_path):
    command = assistant.build_batch_ffmpeg_command(
        video_path=Path("sample.mov"),
        tmp_dir=tmp_path,
        start=0,
        end=16,
        interval=0.5,
    )

    assert "-nostdin" in command
    assert "-vf" in command
    assert "fps=2.00000000" in command
    assert str(tmp_path / "frame_%06d.jpg") in command


def test_cli_accepts_extraction_mode_and_timeout():
    # This test avoids pytest fixtures so the local lightweight harness can run it.
    import tempfile

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        captured = {}
        original_generate = assistant.generate_video_trace_package

        def fake_generate(config, extraction_mode="batch", ffmpeg_timeout_seconds=30):
            captured["extraction_mode"] = extraction_mode
            captured["timeout"] = ffmpeg_timeout_seconds
            return []

        assistant.generate_video_trace_package = fake_generate
        try:
            result = assistant.main(
                [
                    "--video",
                    "data/video_trace_sources/sample1.mov",
                    "--trace-name",
                    "trace",
                    "--start",
                    "0",
                    "--end",
                    "1",
                    "--interval",
                    "0.5",
                    "--output-dir",
                    str(temp_path),
                    "--source-platform",
                    "bilibili",
                    "--source-url",
                    "https://www.bilibili.com/video/BV1CXtVzaEQB",
                    "--video-title",
                    "title",
                    "--uploader",
                    "unknown",
                    "--extraction-mode",
                    "per_frame",
                    "--ffmpeg-timeout-seconds",
                    "12",
                ]
            )
        finally:
            assistant.generate_video_trace_package = original_generate

    assert result == 0
    assert captured == {"extraction_mode": "per_frame", "timeout": 12}


def test_existing_regression_manifest_is_not_changed():
    manifest = json.loads(Path("hsr_axis_sim/data/regression_manifest.json").read_text())

    manual_paths = [entry["path"] for entry in manifest["groups"]["manual"]]

    assert manual_paths == [
        "hsr_axis_sim/data/manual_video_traces/samples/manual_video_trace_sample_mvp.json"
    ]
