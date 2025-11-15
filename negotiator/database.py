"""Database layer for accessing Supabase intents."""

import os
from typing import Dict, Any
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()


class IntentNotFoundError(Exception):
    """Raised when an intent is not found in the database."""
    pass


def get_supabase_client() -> Client:
    """Initialize and return Supabase client."""
    # Support both naming conventions
    url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not url or not key:
        raise ValueError("SUPABASE_URL (or NEXT_PUBLIC_SUPABASE_URL) and SUPABASE_SERVICE_ROLE_KEY must be set")
    
    return create_client(url, key)


def get_intent(intent_id: str) -> Dict[str, Any]:
    """
    Fetch an intent by ID from Supabase.
    
    Args:
        intent_id: UUID of the intent to fetch
        
    Returns:
        Dict containing intent data with keys:
        - uuid, user_id, taker_id, max_amount_usd, description, status
        
    Raises:
        IntentNotFoundError: If intent doesn't exist
    """
    client = get_supabase_client()
    
    response = client.table("intents").select("*").eq("uuid", intent_id).execute()
    
    if not response.data or len(response.data) == 0:
        raise IntentNotFoundError(f"Intent {intent_id} not found")
    
    return response.data[0]

