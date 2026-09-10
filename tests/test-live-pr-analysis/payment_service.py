"""
Payment Service Module (Modified Version in test branch)
"""

# ❌ 1. DELETED CLASS: PaymentGateway was completely removed!

class TransactionService:
    """Handles payments and refunds."""
    
    # ❌ 2. REDUCED PARAMETERS: Dropped 'currency' and 'auth_token'
    def process_payment(self, user_id: str, amount: float):
        """Processes customer payments."""
        print(f"Processing {amount} for user {user_id}")
        return True

    # ❌ 3. REMOVED FUNCTION: refund_transaction was completely deleted!
