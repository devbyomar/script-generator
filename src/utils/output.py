"""File-output helpers."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from src.models.script import FinalScript

logger = logging.getLogger(__name__)


def save_script(script: FinalScript, output_dir: str = "output") -> Path:
    """Save a FinalScript to the output directory as .txt and .json."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    slug = script.title[:50].replace(" ", "_").lower()

    # Human-readable
    txt_path = out / f"{ts}_{slug}.txt"
    txt_path.write_text(script.render(), encoding="utf-8")
    logger.info("Script saved → %s", txt_path)

    # Machine-readable
    json_path = out / f"{ts}_{slug}.json"
    json_path.write_text(script.model_dump_json(indent=2), encoding="utf-8")
    logger.info("JSON saved  → %s", json_path)

    return txt_path
