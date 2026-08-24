from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class VideoSourceMetadata:
    platform: str
    url: str
    video_title: str
    uploader: str
    notes: str = ""


@dataclass
class FrameRecord:
    frame_id: str
    timestamp_seconds: float
    timestamp_label: str
    frame_path: Path
    annotation_status: str = "pending"
    notes: str = ""


@dataclass
class DeclaredAction:
    step: int
    actor: str
    action: str
    notes: str = ""


@dataclass
class VideoTraceAssistantConfig:
    video: Path
    trace_name: str
    start: float
    end: float
    interval: float
    output_dir: Path
    source: VideoSourceMetadata
    team: list[str] = field(default_factory=list)
    prebattle: str = ""
    declared_sequence: list[DeclaredAction] = field(default_factory=list)
