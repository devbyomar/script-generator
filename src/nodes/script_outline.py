"""ScriptOutlineNode — generates the script outline from narratives."""

from __future__ import annotations

import json
import logging

from langchain_openai import ChatOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import settings
from src.models.script import ScriptOutline, ScriptSection
from src.models.state import AgentState
from src.prompts.script import OUTLINE_SYSTEM, OUTLINE_USER

logger = logging.getLogger(__name__)


def _build_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=0.5,
        max_tokens=4096,
    )


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30))
def _generate_outline(llm: ChatOpenAI, narratives_json: str, target_minutes: int) -> dict:
    """Ask the LLM to produce a structured outline."""
    user = OUTLINE_USER.format(
        narratives_json=narratives_json,
        target_minutes=target_minutes,
    )
    response = llm.invoke([
        {"role": "system", "content": OUTLINE_SYSTEM},
        {"role": "user", "content": user},
    ])
    raw = response.content.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
    return json.loads(raw)


def script_outline_node(state: AgentState) -> dict:
    """LangGraph node: create script outline."""
    narratives = state.get("dominant_narratives", [])
    logger.info("📝 ScriptOutlineNode — building outline from %d narratives …", len(narratives))

    if not narratives:
        return {"script_outline": None, "error": "No narratives available for outline."}

    llm = _build_llm()
    narratives_json = json.dumps(
        [n.model_dump() for n in narratives], indent=2
    )

    try:
        raw = _generate_outline(llm, narratives_json, settings.script_target_minutes)
    except Exception as exc:
        logger.exception("Outline generation failed")
        return {"script_outline": None, "error": f"Outline error: {exc}"}

    sections = [
        ScriptSection(
            section_name=s.get("section_name", "Untitled"),
            timestamp=s.get("timestamp", ""),
            content=s.get("content_notes", ""),
            stage_direction=s.get("stage_direction", ""),
        )
        for s in raw.get("sections", [])
    ]

    outline = ScriptOutline(
        title=raw.get("title", "Untitled Video"),
        thumbnail_hook=raw.get("thumbnail_hook", ""),
        target_minutes=raw.get("target_minutes", settings.script_target_minutes),
        sections=sections,
        narratives_used=raw.get("narratives_used", []),
    )

    logger.info("✅ Outline created: '%s' (%d sections)", outline.title, len(sections))
    return {"script_outline": outline, "error": ""}
