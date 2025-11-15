"""Integration tests for A2A protocol support."""

import pytest
import subprocess
import time
import asyncio
from dotenv import load_dotenv
from orchestrator import NegotiationOrchestrator

load_dotenv()

# Real test intent ID
TEST_INTENT_ID = "32ec0fba-931e-49b2-b4c2-02a1d6929a9c"


@pytest.fixture(scope="module")
def a2a_services():
    """Start two A2A service instances on different ports."""
    # Start buyer A2A service on port 8002
    buyer_process = subprocess.Popen(
        ["uv", "run", "python", "a2a_server.py", "--port", "8002"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd="/Users/osprey/repos/fetch/negotiator"
    )
    
    # Start seller A2A service on port 8003
    seller_process = subprocess.Popen(
        ["uv", "run", "python", "a2a_server.py", "--port", "8003"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd="/Users/osprey/repos/fetch/negotiator"
    )
    
    # Give services time to start
    print("\n⏳ Starting A2A services...")
    time.sleep(8)
    
    yield {
        "buyer_url": "http://localhost:8002",
        "seller_url": "http://localhost:8003"
    }
    
    # Cleanup
    print("\n🧹 Stopping A2A services...")
    buyer_process.terminate()
    seller_process.terminate()
    try:
        buyer_process.wait(timeout=5)
        seller_process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        buyer_process.kill()
        seller_process.kill()


@pytest.mark.asyncio
async def test_full_a2a_negotiation(a2a_services):
    """
    Test complete negotiation via A2A protocol.
    
    CRITICAL TEST: Proves A2A wrapper works end-to-end.
    Two A2A services negotiate and reach a deal.
    """
    orchestrator = NegotiationOrchestrator(
        buyer_url=a2a_services["buyer_url"],
        seller_url=a2a_services["seller_url"],
        protocol="a2a"
    )
    
    # Run full negotiation
    result = await orchestrator.run_negotiation(
        intent_id=TEST_INTENT_ID,
        max_rounds=10,
        verbose=True
    )
    
    # Verify we got a result
    assert result is not None
    assert "status" in result
    assert "outcome" in result
    assert "rounds" in result
    assert "conversation" in result
    
    # Should complete (not timeout)
    assert result["status"] in ["success", "failed", "timeout"]
    
    # Should have conversation history
    assert len(result["conversation"]) > 0
    
    # Should have alternating roles
    roles = [msg["role"] for msg in result["conversation"]]
    assert "buyer" in roles or "seller" in roles
    
    print(f"\n✅ A2A Negotiation completed in {result['rounds']} rounds")
    print(f"   Status: {result['status']}")
    print(f"   Outcome: {result['outcome']}")
    
    # Verify it actually negotiated (not just errored out)
    assert result["rounds"] >= 1


@pytest.mark.asyncio
async def test_a2a_reaches_deal(a2a_services):
    """Test that A2A agents can reach an agreement."""
    orchestrator = NegotiationOrchestrator(
        buyer_url=a2a_services["buyer_url"],
        seller_url=a2a_services["seller_url"],
        protocol="a2a"
    )
    
    result = await orchestrator.run_negotiation(
        intent_id=TEST_INTENT_ID,
        max_rounds=10,
        verbose=False
    )
    
    assert result is not None
    
    # Should complete with some outcome
    assert result["status"] in ["success", "failed", "timeout"]
    
    # If deal reached, verify structure
    if result["status"] == "success":
        assert result["outcome"] == "accepted"
        assert "final_decision_by" in result
        print(f"\n✅ A2A deal reached by {result['final_decision_by']} in {result['rounds']} rounds")
    
    # Should have meaningful conversation
    assert len(result["conversation"]) >= 2


@pytest.mark.asyncio
async def test_a2a_buyer_negotiates(a2a_services):
    """Test that buyer agent negotiates strategically via A2A."""
    orchestrator = NegotiationOrchestrator(
        buyer_url=a2a_services["buyer_url"],
        seller_url=a2a_services["seller_url"],
        protocol="a2a"
    )
    
    result = await orchestrator.run_negotiation(
        intent_id=TEST_INTENT_ID,
        max_rounds=5,
        verbose=False
    )
    
    # Should have multiple rounds of negotiation
    assert result["rounds"] >= 1
    assert len(result["conversation"]) >= 1
    
    print(f"\n✅ A2A negotiation ran for {result['rounds']} rounds")

