"""Database layer for accessing Supabase intents."""

import os
from typing import Dict, Any, Optional
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
        - tx_buyer_to_seller_id, tx_buyer_to_user_id (Base tx hashes)
        
    Raises:
        IntentNotFoundError: If intent doesn't exist
    """
    client = get_supabase_client()
    
    response = client.table("intents").select("*").eq("uuid", intent_id).execute()
    
    if not response.data or len(response.data) == 0:
        raise IntentNotFoundError(f"Intent {intent_id} not found")
    
    return response.data[0]


def update_intent_with_transactions(
    intent_id: str,
    tx_buyer_to_seller: Optional[str] = None,
    tx_buyer_to_user: Optional[str] = None
) -> Any:
    """
    Update intent with Base blockchain transaction hashes.
    
    Args:
        intent_id: Intent UUID
        tx_buyer_to_seller: Base tx hash for buyer→seller payment
        tx_buyer_to_user: Base tx hash for buyer→user refund
        
    Returns:
        Supabase response
    """
    client = get_supabase_client()
    
    updates = {}
    if tx_buyer_to_seller:
        updates["tx_buyer_to_seller_id"] = tx_buyer_to_seller
    if tx_buyer_to_user:
        updates["tx_buyer_to_user_id"] = tx_buyer_to_user
    
    if updates:
        return client.table("intents").update(updates).eq("uuid", intent_id).execute()
    return None


def mark_intent_complete(
    intent_id: str,
    tx_buyer_to_seller: Optional[str] = None,
    tx_buyer_to_user: Optional[str] = None
) -> Any:
    """
    Mark intent as complete and store transaction hashes.
    
    Args:
        intent_id: Intent UUID
        tx_buyer_to_seller: Base tx hash for buyer→seller payment
        tx_buyer_to_user: Base tx hash for buyer→user refund
        
    Returns:
        Supabase response
    """
    client = get_supabase_client()
    
    # Use "completed" instead of "complete" for the enum
    updates = {"status": "completed"}
    
    if tx_buyer_to_seller:
        updates["tx_buyer_to_seller_id"] = tx_buyer_to_seller
    if tx_buyer_to_user:
        updates["tx_buyer_to_user_id"] = tx_buyer_to_user
    
    return client.table("intents").update(updates).eq("uuid", intent_id).execute()


def create_test_intent(
    user_id: str,
    description: str,
    max_amount: float
) -> str:
    """
    Create a test intent in Supabase.
    
    Args:
        user_id: User UUID
        description: Item description
        max_amount: Maximum budget in USD
        
    Returns:
        New intent UUID
    """
    import uuid
    
    client = get_supabase_client()
    
    intent_id = str(uuid.uuid4())
    
    result = client.table("intents").insert({
        "uuid": intent_id,
        "user_id": user_id,
        "max_amount_usd": max_amount,
        "description": description,
        "status": "live"
    }).execute()
    
    return intent_id

