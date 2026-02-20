"""ScriptGenerationNode — writes the full script from the outline."""

from __future__ import annotations

import json
import logging

from langchain_openai import ChatOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import settings
from src.models.script import FinalScript, ScriptSection
from src.models.state import AgentState
from src.prompts.script import SCRIPT_SYSTEM, SCRIPT_USER

logger = logging.getLogger(__name__)


def _build_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=0.7,
        max_tokens=8192,
    )


def _sample_tweets(state: AgentState, max_samples: int = 15) -> str:
    """Pick the highest-signal tweets as paraphrased reference for the LLM."""
    tweets = state.get("tweets_filtered", [])
    top = sorted(tweets, key=lambda t: t.engagement_score, reverse=True)[:max_samples]
    lines = []
    for t in top:
        lines.append(
            f"- @{t.author.username} ({t.author.followers_count:,} followers, "
            f"cred={t.credibility_score:.0f}): \"{t.text[:200]}\""
        )
    return "\n".join(lines) if lines else "(no sample tweets available)"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30))
def _generate_script(llm: ChatOpenAI, outline_json: str, narratives_json: str, samples: str) -> dict:
    """Ask the LLM to write the full script."""
    user = SCRIPT_USER.format(
        outline_json=outline_json,
        narratives_json=narratives_json,
        sample_tweets=samples,
    )
    response = llm.invoke([
        {"role": "system", "content": SCRIPT_SYSTEM},
        {"role": "user", "content": user},
    ])
    raw = response.content.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
    return json.loads(raw)


def script_generation_node(state: AgentState) -> dict:
    """LangGraph node: generate the full script."""
    outline = state.get("script_outline")
    narratives = state.get("dominant_narratives", [])
    logger.info("🎬 ScriptGenerationNode — writing full script …")

    if outline is None:
        return {"final_script": None, "error": "No outline available for script generation."}

    llm = _build_llm()
    outline_json = json.dumps(outline.model_dump(), indent=2)
    narratives_json = json.dumps([n.model_dump() for n in narratives], indent=2)
    samples = _sample_tweets(state)

    try:
        raw = _generate_script(llm, outline_json, narratives_json, samples)
    except Exception as exc:
        logger.exception("Script generation failed")
        return {"final_script": None, "error": f"Script generation error: {exc}"}

    sections = [
        ScriptSection(
            section_name=s.get("section_name", ""),
            timestamp=s.get("timestamp", ""),
            content=s.get("content", ""),
            stage_direction=s.get("stage_direction", ""),
        )
        for s in raw.get("sections", [])
    ]

    full_text = "\n\n".join(s.content for s in sections if s.content)

    script = FinalScript(
        title=raw.get("title", outline.title),
        thumbnail_text=raw.get("thumbnail_text", outline.thumbnail_hook),
        description=raw.get("description", ""),
        tags=raw.get("tags", []),
        estimated_duration_minutes=float(raw.get("estimated_duration_minutes", 10.0)),
        sections=sections,
        full_text=full_text,
    )

    logger.info("✅ Script generated: '%s' (~%.1f min)", script.title, script.estimated_duration_minutes)
    return {"final_script": script, "error": ""}
