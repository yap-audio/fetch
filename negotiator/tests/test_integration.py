"""Integration tests for full negotiation flow."""

import pytest
import asyncio
from dotenv import load_dotenv
from httpx import AsyncClient
from main import app
from database import get_intent

# Load environment variables for tests
load_dotenv()


# Real test intent ID
TEST_INTENT_ID = "32ec0fba-931e-49b2-b4c2-02a1d6929a9c"


@pytest.mark.asyncio
async def test_health_check():
    """Test that the API is up and running."""
    async with AsyncClient(base_url="http://localhost:8000", timeout=30.0) as client:
        response = await client.get("/")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_negotiate_endpoint_exists():
    """Test that negotiate endpoint exists."""
    async with AsyncClient(base_url="http://localhost:8000", timeout=120.0) as client:
        # Send a request (it will process, but we just check it doesn't 404)
        response = await client.post(
            "/negotiate",
            json={
                "intent_id": TEST_INTENT_ID,
                "seller_message": "Test message",
                "agent_type": "buyer"
            }
        )
        # Should not be 404 (200 for streaming response)
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_negotiate_seller_agent():
    """Test negotiation with seller agent type."""
    async with AsyncClient(base_url="http://localhost:8000", timeout=120.0) as client:
        response = await client.post(
            "/negotiate",
            json={
                "intent_id": TEST_INTENT_ID,
                "seller_message": "I'd like to buy this for $10,000",
                "agent_type": "seller"
            }
        )
        # Should work with seller agent type
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_negotiate_invalid_intent():
    """Test negotiation with invalid intent ID."""
    async with AsyncClient(base_url="http://localhost:8000", timeout=30.0) as client:
        response = await client.post(
            "/negotiate",
            json={
                "intent_id": "00000000-0000-0000-0000-000000000000",
                "seller_message": "I can offer it for $100"
            }
        )
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_full_negotiation_high_offer():
    """Test negotiation with a high offer (should reject or counter)."""
    async with AsyncClient(base_url="http://localhost:8000", timeout=120.0) as client:
        # First, get the intent to know the budget
        intent = get_intent(TEST_INTENT_ID)
        max_budget = float(intent["max_amount_usd"])
        
        # Offer way above budget
        high_offer = max_budget * 3
        
        async with client.stream(
            "POST",
            "/negotiate",
            json={
                "intent_id": TEST_INTENT_ID,
                "seller_message": f"I can offer this for ${high_offer:.2f}"
            }
        ) as response:
            assert response.status_code == 200
            
            # Collect some events
            event_count = 0
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    event_count += 1
                    if event_count >= 3:  # Just verify we get multiple events
                        break
            
            assert event_count >= 3


@pytest.mark.asyncio
async def test_full_negotiation_reasonable_offer():
    """Test negotiation with a reasonable offer."""
    async with AsyncClient(base_url="http://localhost:8000", timeout=120.0) as client:
        # Get the intent
        intent = get_intent(TEST_INTENT_ID)
        max_budget = float(intent["max_amount_usd"])
        
        # Offer at 50% of budget (reasonable)
        reasonable_offer = max_budget * 0.5
        
        async with client.stream(
            "POST",
            "/negotiate",
            json={
                "intent_id": TEST_INTENT_ID,
                "seller_message": f"I can sell this for ${reasonable_offer:.2f}"
            }
        ) as response:
            assert response.status_code == 200
            
            # Verify we get streaming events
            event_count = 0
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    event_count += 1
                    if event_count >= 3:
                        break
            
            assert event_count >= 3


def test_intent_data_accessible():
    """Test that we can access the test intent data."""
    intent = get_intent(TEST_INTENT_ID)
    
    assert intent is not None
    assert "max_amount_usd" in intent
    assert "description" in intent
    
    print(f"\nTest Intent Details:")
    print(f"  Description: {intent['description']}")
    print(f"  Max Budget: ${intent['max_amount_usd']}")

