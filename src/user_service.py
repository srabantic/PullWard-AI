"""
User Service Module
"""

# BEFORE (Original API Contract):
# def authenticate_and_fetch_profile(user_id: str, auth_token: str, include_roles: bool = False):

# AFTER (Breaking Change: 'auth_token' parameter was removed!):
def authenticate_and_fetch_profile(user_id: str, include_roles: bool = False):
    """
    Fetches user profile. 
    BREAKING CHANGE: Removed required parameter 'auth_token'.
    """
    print(f"Fetching profile for user: {user_id}")
    return {"user_id": user_id, "status": "active"}


def delete_user_account(user_id: str):
    """Deletes user account."""
    return {"user_id": user_id, "deleted": True}