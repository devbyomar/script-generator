"""Script output models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ScriptSection(BaseModel):
    """One section of the final YouTube script."""

    section_name: str          # e.g. "Pattern Interrupt Hook"
    timestamp: str             # e.g. "0:00–0:20"
    content: str               # Spoken word content
    stage_direction: str = ""  # Visual / tone cues for the creator


class ScriptOutline(BaseModel):
    """High-level outline produced before full script generation."""

    title: str
    thumbnail_hook: str
    target_minutes: int = 10
    sections: list[ScriptSection] = Field(default_factory=list)
    narratives_used: list[str] = Field(default_factory=list)


class QualityReport(BaseModel):
    """Output of the quality-check node."""

    passed: bool
    overall_score: float              # 0-100
    retention_estimate: float         # 0-1
    feedback: str
    issues: list[str] = Field(default_factory=list)


class FinalScript(BaseModel):
    """The complete, ready-to-record script."""

    title: str
    thumbnail_text: str
    description: str
    tags: list[str] = Field(default_factory=list)
    estimated_duration_minutes: float = 10.0
    sections: list[ScriptSection] = Field(default_factory=list)
    full_text: str = ""                # Concatenated spoken text
    quality_report: QualityReport | None = None

    def render(self) -> str:
        """Return a formatted, human-readable script."""
        lines: list[str] = []
        lines.append(f"TITLE: {self.title}")
        lines.append(f"THUMBNAIL: {self.thumbnail_text}")
        lines.append(f"ESTIMATED DURATION: {self.estimated_duration_minutes:.1f} min")
        lines.append("")
        lines.append("=" * 72)
        for sec in self.sections:
            lines.append(f"\n## {sec.section_name}  [{sec.timestamp}]")
            if sec.stage_direction:
                lines.append(f"   🎬 {sec.stage_direction}")
            lines.append("")
            lines.append(sec.content)
            lines.append("")
        lines.append("=" * 72)
        lines.append(f"\nDESCRIPTION:\n{self.description}")
        lines.append(f"\nTAGS: {', '.join(self.tags)}")
        return "\n".join(lines)
