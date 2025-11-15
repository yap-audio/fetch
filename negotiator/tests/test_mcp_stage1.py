"""Stage 1: Basic MCP integration test."""

import pytest
import os
from dotenv import load_dotenv
from payments import LocusMCPClient

load_dotenv()


@pytest.mark.asyncio
async def test_mcp_basic_call():
    """
    STAGE 1 TEST: Verify JSON-RPC MCP call works.
    
    Sends $0.10 from user wallet to buyer agent wallet.
    This validates:
    - MCP URL is correct
    - JSON-RPC format is correct  
    - API key authentication works
    - send_to_address tool exists
    """
    # Get user wallet API key
    user_api_key = os.getenv("USER_WALLET_API_KEY")
    buyer_address = os.getenv("BUYER_AGENT_WALLET_ADDRESS")
    
    if not user_api_key:
        pytest.skip("USER_WALLET_API_KEY not set")
    if not buyer_address:
        pytest.skip("BUYER_AGENT_WALLET_ADDRESS not set")
    
    # Create MCP client
    client = LocusMCPClient(user_api_key)
    
    # Send 10 cents to buyer
    result = await client.send_to_address(
        address=buyer_address,
        amount=0.10,
        memo="Stage 1: MCP validation test"
    )
    
    # Verify we got a result
    assert result is not None
    print(f"\n✅ MCP call successful!")
    print(f"   Amount: $0.10")
    print(f"   Recipient: {buyer_address}")
    print(f"   Result: {result}")


@pytest.mark.asyncio
async def test_mcp_get_balance():
    """Test getting payment context/balance."""
    user_api_key = os.getenv("USER_WALLET_API_KEY")
    
    if not user_api_key:
        pytest.skip("USER_WALLET_API_KEY not set")
    
    client = LocusMCPClient(user_api_key)
    
    result = await client.get_payment_context()
    
    assert result is not None
    print(f"\n✅ Payment context retrieved:")
    print(f"   {result}")

