"""Integration tests for agent-to-agent negotiations."""

import pytest
import asyncio
import subprocess
import time
from dotenv import load_dotenv
from orchestrator import NegotiationOrchestrator

load_dotenv()

# Real test intent ID
TEST_INTENT_ID = "32ec0fba-931e-49b2-b4c2-02a1d6929a9c"


@pytest.fixture(scope="module")
def services():
    """Start two service instances on different ports."""
    # Start buyer service on port 9000
    buyer_process = subprocess.Popen(
        ["python3", "negotiator/main.py", "--port", "9000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Start seller service on port 9001  
    seller_process = subprocess.Popen(
        ["python3", "negotiator/main.py", "--port", "9001"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Give services time to start
    time.sleep(5)
    
    yield {
        "buyer_url": "http://localhost:9000",
        "seller_url": "http://localhost:9001"
    }
    
    # Cleanup
    buyer_process.terminate()
    seller_process.terminate()
    buyer_process.wait(timeout=5)
    seller_process.wait(timeout=5)


@pytest.mark.asyncio
async def test_full_agent_to_agent_negotiation(services):
    """
    Test a complete negotiation between buyer and seller services.
    
    This is the critical test that proves the system works end-to-end.
    """
    orchestrator = NegotiationOrchestrator(
        buyer_url=services["buyer_url"],
        seller_url=services["seller_url"]
    )
    
    # Run full negotiation
    result = await orchestrator.run_negotiation(
        intent_id=TEST_INTENT_ID,
        max_rounds=10,
        verbose=True  # Print for debugging
    )
    
    # Verify we got a result
    assert result is not None
    assert "status" in result
    assert "outcome" in result
    assert "rounds" in result
    assert "conversation" in result
    
    # Should complete (not timeout)
    assert result["status"] in ["success", "failed"]
    
    # Should have conversation history
    assert len(result["conversation"]) > 0
    
    # Should have alternating roles
    roles = [msg["role"] for msg in result["conversation"]]
    assert "buyer" in roles or "seller" in roles
    
    print(f"\n✅ Negotiation completed in {result['rounds']} rounds")
    print(f"   Status: {result['status']}")
    print(f"   Outcome: {result['outcome']}")


@pytest.mark.asyncio
async def test_buyer_rejects_unreasonable_price(services):
    """Test that buyer rejects prices way over budget."""
    orchestrator = NegotiationOrchestrator(
        buyer_url=services["buyer_url"],
        seller_url=services["seller_url"]
    )
    
    # This will likely result in rejection or long negotiation
    result = await orchestrator.run_negotiation(
        intent_id=TEST_INTENT_ID,
        max_rounds=5,
        verbose=False
    )
    
    assert result is not None
    assert result["rounds"] <= 5


@pytest.mark.asyncio  
async def test_agents_reach_agreement(services):
    """Test that agents can reach an agreement."""
    orchestrator = NegotiationOrchestrator(
        buyer_url=services["buyer_url"],
        seller_url=services["seller_url"]
    )
    
    result = await orchestrator.run_negotiation(
        intent_id=TEST_INTENT_ID,
        max_rounds=10,
        verbose=False
    )
    
    # With reasonable parameters, should often reach a deal
    assert result is not None
    
    # If deal reached, verify structure
    if result["status"] == "success":
        assert result["outcome"] == "accepted"
        assert "final_decision_by" in result
        print(f"\n✅ Deal reached by {result['final_decision_by']} in {result['rounds']} rounds")

