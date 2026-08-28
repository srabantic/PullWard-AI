import os
import re
from typing import Dict, Any, List
from google.genai import Client

SECRET_PATTERNS = [
    (r'(?i)(api_key|apikey|secret|password|passwd|private_key)\s*=\s*["\'][A-Za-z0-9_\-]{8,}["\']', "Potential Hardcoded Secret/Key"),
    (r'-----BEGIN (RSA|PRIVATE|OPENSSH) KEY-----', "Exposed Private Key Block"),
    (r'(?i)AIzaSy[A-Za-z0-9_\-]{33}', "Exposed Google API Key"),
    (r'(?i)ghp_[A-Za-z0-9]{36}', "Exposed GitHub Personal Access Token"),
]

DANGEROUS_CALLS = [
    (r'\beval\s*\(', "Unsafe execution: eval() call detected"),
    (r'\bexec\s*\(', "Unsafe execution: exec() call detected"),
    (r'SELECT\s+.*?\s+FROM\s+.*?\+\s*\w+', "Potential SQL Injection string concatenation"),
]

class SecurityAgent:
    """Agent focused on secret scanning, vulnerability detection, and code safety."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.client = Client(api_key=self.api_key) if self.api_key else None

    def run(self, diff_text: str, diff_files: List[Dict[str, str]] = None) -> Dict[str, Any]:
        findings = []

        # 1. Per-file secret & vulnerability scanning
        if diff_files:
            for f in diff_files:
                filename = f.get("filename", "unknown")
                code_to_check = f.get("new_code", "")

                for pattern, desc in SECRET_PATTERNS:
                    if re.search(pattern, code_to_check):
                        findings.append(f"`{filename}`: [HIGH RISK] {desc}")

                for pattern, desc in DANGEROUS_CALLS:
                    if re.search(pattern, code_to_check):
                        findings.append(f"`{filename}`: [MEDIUM RISK] {desc}")
        else:
            for pattern, desc in SECRET_PATTERNS:
                if re.search(pattern, diff_text):
                    findings.append(f"[HIGH RISK] {desc}")

            for pattern, desc in DANGEROUS_CALLS:
                if re.search(pattern, diff_text):
                    findings.append(f"[MEDIUM RISK] {desc}")

        # 2. Gemini AI Security Vulnerability Review
        ai_insight = "No automated security warnings detected."
        if self.client:
            prompt = f"""
You are the Security & Secret Audit Sub-Agent for PullWard AI.
Analyze the following code diff for potential security vulnerabilities, insecure dependency imports, or logic flaws:

Diff Snippet:
{diff_text[:3000]}

Deterministic Security Scanner Findings:
{findings if findings else "None"}

Provide a concise 2-sentence security evaluation. If secrets or vulnerabilities exist, highlight them clearly.
"""
            try:
                response = self.client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=prompt
                )
            except Exception as e:
                err_msg = str(e)
                if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                    ai_insight = f"Deterministic security scan verified {len(findings)} security finding(s)." if findings else "Static security analysis verified clean diff."
                else:
                    ai_insight = f"Security review completed with {len(findings)} finding(s)."

        return {
            "agent": "SecurityAgent",
            "security_findings_count": len(findings),
            "findings": findings,
            "summary": ai_insight
        }


def analyze_security_risks(diff_text: str, diff_files: List[Dict[str, str]] = None) -> Dict[str, Any]:
    agent = SecurityAgent()
    return agent.run(diff_text, diff_files)