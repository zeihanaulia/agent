#!/usr/bin/env python3
"""Tests for the agent-based project specification parser.

The specs exercised here call into `flow_parse_intent._parse_project_spec_content`, which is the
core project-spec parser responsible for building a structured `ProjectSpec` from Markdown input.
These tests document what the parser is expected to return so we can detect regressions when the
LLM-driven path or fallback heuristics change."""

import sys  # noqa: E402
from pathlib import Path  # noqa: E402

# Ensure the `scripts/coding_agent` package is importable
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scripts" / "coding_agent"))  # noqa: E402
sys.path.insert(0, str(ROOT))  # noqa: E402

from flow_parse_intent import _parse_project_spec_content  # noqa: E402  # type: ignore[import]
from tests.utils.markdown_helpers import extract_markdown_sections  # noqa: E402


SPEC_PATH = ROOT / "dataset" / "spec" / "crypto-monitoring-system.md"


def load_crypto_spec() -> str:
    """Load the crypto monitoring project specification."""
    with open(SPEC_PATH, "r", encoding="utf-8") as f:
        return f.read()


def test_agent_parser_parses_crypto_spec() -> None:
    """The agent-based parser should parse the comprehensive crypto spec. Expected outcome:
    a `ProjectSpec` instance with core metadata populated and no crashes when the LLM parser falls
    back to heuristics."""

    content = load_crypto_spec()
    spec = _parse_project_spec_content(content)

    assert spec.project_name and spec.project_name != "Unknown"
    assert spec.language.lower() in {"java", "python", "typescript"}
    assert spec.framework
    baseline_deps = spec.dependencies.get("baseline")
    assert baseline_deps is None or isinstance(baseline_deps, list)
    assert isinstance(spec.workflow_guidelines, list)
    assert isinstance(spec.architecture_notes, dict)


def test_markdown_helper_extracts_sections() -> None:
    """Helper should split markdown into sections keyed by headers."""

    simple_spec = """
# Test Project

## 🧠 project overview
name: crypto-monitoring-system
purpose: Monitoring platform

## 🧭 architecture notes
layering: Hexagonal
"""

    sections = extract_markdown_sections(simple_spec)
    assert "## 🧠 project overview" in sections
    assert "## 🧭 architecture notes" in sections
    assert sections["## 🧠 project overview"].startswith("name:")