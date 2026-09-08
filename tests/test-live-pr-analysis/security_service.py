"""
Security Vulnerability Test Module for PullWard AI
"""

# ==============================================================================
# 1. EXPOSED SECRETS & CREDENTIALS
# ==============================================================================

# ❌ Exposed Google API Key
GOOGLE_GEMINI_KEY = "AIzaSyD-FakeTestGeminiKey1234567890"

# ❌ Exposed GitHub Personal Access Token
GITHUB_PAT_TOKEN = "ghp_FakeGitHubPersonalAccessToken123456"

# ❌ Exposed RSA Private Key Block
SSH_PRIVATE_KEY = """
-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEA0Y3y...[FAKE_PRIVATE_KEY]...
-----END RSA PRIVATE KEY-----
"""

# ❌ Hardcoded Generic API Secret
STRIPE_SECRET_KEY = "sk_live_9876543210abcdefghij"


# ==============================================================================
# 2. DANGEROUS EXECUTION CALLS & INJECTION RISKS
# ==============================================================================

def execute_dynamic_calculation(user_math_string: str):
    """❌ Unsafe execution: eval() call"""
    return eval(user_math_string)


def execute_admin_script(untrusted_code: str):
    """❌ Unsafe execution: exec() call"""
    exec(untrusted_code)


def get_user_by_id(db_conn, user_id: str):
    """❌ Potential SQL Injection: Raw string concatenation"""
    query = "SELECT * FROM users WHERE id = " + user_id
    return db_conn.execute(query)
