import os
import re
from typing import Dict, Any
from google.genai import Client

class SchemaAgent:
    """Agent focused on database migration safety, schema drift, and SQL destructive statements."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.client = Client(api_key=self.api_key) if self.api_key else None

    def run(self, diff_text: str) -> Dict[str, Any]:
        findings = []

        # 1. Deterministic SQL / Schema destruction check
        destructive_drops = re.findall(r'DROP\s+(TABLE|COLUMN|DATABASE|INDEX)\s+(\w+)', diff_text, re.IGNORECASE)
        for target_type, target_name in destructive_drops:
            findings.append(f"[SCHEMA BREAK] Destructive statement detected: DROP {target_type.upper()} '{target_name}'")

        # 2. Gemini AI Schema Compatibility Assessment
        ai_insight = "Schema checks completed."
        if self.client:
            prompt = f"""
You are the Database & Schema Governance Sub-Agent for PullWard AI.
Review the following SQL or schema code diff for destructive or breaking migration risks:

Diff Snippet:
{diff_text[:2500]}

Deterministic Findings:
{findings if findings else "None"}

Provide a 2-sentence summary evaluating if this PR introduces backward-incompatible schema changes.
"""
            try:
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )
                ai_insight = response.text.strip()
            except Exception as e:
                ai_insight = f"AI Schema Analysis error: {str(e)}"

        return {
            "agent": "SchemaAgent",
            "schema_breaking_changes": len(findings) > 0,
            "findings": findings,
            "summary": ai_insight
        }


def analyze_schema_breaking_changes(diff_text: str) -> Dict[str, Any]:
    agent = SchemaAgent()
    return agent.run(diff_text)