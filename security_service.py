"""
Security Vulnerability Test Module for PullWard AI
"""

# ==============================================================================
# 1. EXPOSED SECRETS & CREDENTIALS
# ==============================================================================

# ❌ Exposed Google API Key
GOOGLE_GEMINI_KEY = "AIzaSyD-FakeTestGeminiKey1234567890"

# ❌ Hardcoded Generic API Secret
STRIPE_SECRET_KEY = "sk_live_9876543210abcdefghij"

# ==============================================================================
# 2. DANGEROUS EXECUTION CALLS & INJECTION RISKS
# ==============================================================================
def execute_admin_script(untrusted_code: str):
    """❌ Unsafe execution: exec() call"""
    exec(untrusted_code)
