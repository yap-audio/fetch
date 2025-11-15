"""Unit tests for database layer."""

import pytest
from dotenv import load_dotenv
from database import get_intent, IntentNotFoundError, get_supabase_client

# Load environment variables for tests
load_dotenv()


def test_get_supabase_client():
    """Test that Supabase client can be initialized."""
    client = get_supabase_client()
    assert client is not None


def test_get_intent_success():
    """Test fetching a valid intent."""
    # Using the real test intent
    intent_id = "32ec0fba-931e-49b2-b4c2-02a1d6929a9c"
    
    intent = get_intent(intent_id)
    
    assert intent is not None
    assert "uuid" in intent
    assert "user_id" in intent
    assert "max_amount_usd" in intent
    assert "description" in intent
    assert intent["uuid"] == intent_id


def test_get_intent_not_found():
    """Test fetching a non-existent intent."""
    fake_intent_id = "00000000-0000-0000-0000-000000000000"
    
    with pytest.raises(IntentNotFoundError):
        get_intent(fake_intent_id)


def test_intent_has_required_fields():
    """Test that intent has all required fields."""
    intent_id = "32ec0fba-931e-49b2-b4c2-02a1d6929a9c"
    
    intent = get_intent(intent_id)
    
    # Check all required fields exist
    required_fields = ["uuid", "user_id", "max_amount_usd", "description", "status"]
    for field in required_fields:
        assert field in intent, f"Missing required field: {field}"
    
    # Check types
    assert isinstance(intent["max_amount_usd"], (int, float, str))
    assert isinstance(intent["description"], str)

