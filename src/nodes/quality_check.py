"""QualityCheckNode — validates the generated script before output."""

from __future__ import annotations

import json
import logging

from langchain_openai import ChatOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import settings
from src.models.script import QualityReport
from src.models.state import AgentState
from src.prompts.script import QUALITY_SYSTEM, QUALITY_USER

logger = logging.getLogger(__name__)


def _build_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=0.2,
        max_tokens=2048,
    )


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30))
def _evaluate_script(llm: ChatOpenAI, script_json: str) -> dict:
    """Ask the LLM to evaluate the script quality."""
    user = QUALITY_USER.format(script_json=script_json)
    response = llm.invoke([
        {"role": "system", "content": QUALITY_SYSTEM},
        {"role": "user", "content": user},
    ])
    raw = response.content.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
    return json.loads(raw)


def quality_check_node(state: AgentState) -> dict:
    """LangGraph node: evaluate script quality."""
    script = state.get("final_script")
    logger.info("🔍 QualityCheckNode — evaluating script …")

    if script is None:
        return {
            "quality_passed": False,
            "quality_feedback": "No script to evaluate.",
            "error": "No script available for quality check.",
        }

    llm = _build_llm()
    script_json = json.dumps(script.model_dump(), indent=2)

    try:
        raw = _evaluate_script(llm, script_json)
    except Exception as exc:
        logger.exception("Quality check failed")
        return {
            "quality_passed": False,
            "quality_feedback": f"Quality check error: {exc}",
            "error": str(exc),
        }

    report = QualityReport(
        passed=raw.get("passed", False),
        overall_score=float(raw.get("overall_score", 0)),
        retention_estimate=float(raw.get("retention_estimate", 0)),
        feedback=raw.get("feedback", ""),
        issues=raw.get("issues", []),
    )

    # Attach report to the script
    script.quality_report = report

    logger.info(
        "✅ Quality check: %s (score=%.0f, retention=%.0f%%)",
        "PASSED" if report.passed else "FAILED",
        report.overall_score,
        report.retention_estimate * 100,
    )

    return {
        "final_script": script,
        "quality_passed": report.passed,
        "quality_feedback": report.feedback,
        "error": "",
    }
