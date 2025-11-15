"""Tests for seller-initiated negotiation via /initiate endpoint."""

import pytest
import subprocess
import time
import os
import httpx
from dotenv import load_dotenv
from database import get_intent
from agent import NegotiationAgent
from main import generate_opening_pitch

load_dotenv()

# Real test intent ID
TEST_INTENT_ID = "32ec0fba-931e-49b2-b4c2-02a1d6929a9c"


@pytest.mark.asyncio
async def test_generate_opening_pitch():
    """Test seller can generate opening sales pitch."""
    intent = get_intent(TEST_INTENT_ID)
    seller_agent = NegotiationAgent(intent, agent_type="seller")
    
    pitch = await generate_opening_pitch(seller_agent, intent)
    
    # Verify pitch exists and has meaningful content
    assert len(pitch) > 50
    
    # Should mention the item (motorcycle)
    assert any(word in pitch.lower() for word in ["ninja", "zx-6r", "kawasaki", "motorcycle", "bike"])
    
    # Should have a price or ask for interest
    assert "$" in pitch or "price" in pitch.lower() or "interested" in pitch.lower()
    
    print(f"\n✅ Generated pitch ({len(pitch)} chars): {pitch[:100]}...")


@pytest.fixture(scope="module")
def initiate_services():
    """Start buyer and seller services for initiate endpoint tests."""
    # Start buyer service on port 9001
    buyer_proc = subprocess.Popen(
        ["uv", "run", "python", "main.py", "--port", "9001"],
        cwd="/Users/osprey/repos/fetch/negotiator",
        env={**os.environ},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Start seller service on port 9000 with buyer URL
    seller_env = {**os.environ, "BUYER_AGENT_URL": "http://localhost:9001"}
    seller_proc = subprocess.Popen(
        ["uv", "run", "python", "main.py", "--port", "9000"],
        cwd="/Users/osprey/repos/fetch/negotiator",
        env=seller_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Give services time to start
    print("\n⏳ Starting buyer and seller services...")
    time.sleep(6)
    
    yield {
        "seller_url": "http://localhost:9000",
        "buyer_url": "http://localhost:9001"
    }
    
    # Cleanup
    print("\n🧹 Stopping services...")
    buyer_proc.terminate()
    seller_proc.terminate()
    try:
        buyer_proc.wait(timeout=5)
        seller_proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        buyer_proc.kill()
        seller_proc.kill()


@pytest.mark.asyncio
async def test_initiate_endpoint_exists(initiate_services):
    """Test /initiate endpoint exists and responds."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{initiate_services['seller_url']}/initiate",
            json={"intent_id": TEST_INTENT_ID, "agent_type": "seller"}
        )
        
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_initiate_calls_buyer(initiate_services):
    """
    Test /initiate generates pitch and contacts buyer.
    
    CRITICAL TEST: Proves seller can initiate and buyer responds.
    """
    async with httpx.AsyncClient(timeout=90.0) as client:
        response = await client.post(
            f"{initiate_services['seller_url']}/initiate",
            json={"intent_id": TEST_INTENT_ID, "agent_type": "seller"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify seller generated pitch
        assert "seller_pitch" in data
        assert len(data["seller_pitch"]) > 50
        
        # Verify buyer responded  
        assert "buyer_response" in data
        assert len(data["buyer_response"]) > 50
        
        # Verify decision captured
        assert "buyer_decision" in data
        assert data["buyer_decision"] in ["accept", "reject", "continue"]
        
        print(f"\n✅ Seller initiated negotiation:")
        print(f"   Pitch length: {len(data['seller_pitch'])} chars")
        print(f"   Response length: {len(data['buyer_response'])} chars")
        print(f"   Buyer decision: {data['buyer_decision']}")


@pytest.mark.asyncio
async def test_seller_initiated_creates_conversation(initiate_services):
    """Test that seller initiation creates proper conversation flow."""
    async with httpx.AsyncClient(timeout=90.0) as client:
        response = await client.post(
            f"{initiate_services['seller_url']}/initiate",
            json={"intent_id": TEST_INTENT_ID}
        )
        
        data = response.json()
        
        # Both agents should have spoken
        assert "seller_pitch" in data
        assert "buyer_response" in data
        
        # Responses should be different (agents actually talking)
        assert data["seller_pitch"] != data["buyer_response"]
        
        # Buyer should show buying interest
        buyer_text = data["buyer_response"].lower()
        assert any(word in buyer_text for word in ["budget", "price", "offer", "interested", "$"])
        
        print(f"\n✅ Conversation created:")
        print(f"   Seller: {data['seller_pitch'][:80]}...")
        print(f"   Buyer: {data['buyer_response'][:80]}...")


@pytest.mark.asyncio
async def test_initiate_invalid_intent(initiate_services):
    """Test /initiate with invalid intent ID."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{initiate_services['seller_url']}/initiate",
            json={"intent_id": "00000000-0000-0000-0000-000000000000"}
        )
        
        assert response.status_code == 404

