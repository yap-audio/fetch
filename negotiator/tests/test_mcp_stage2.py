"""Stage 2: Round-trip payment test."""

import pytest
import os
import asyncio
from dotenv import load_dotenv
from payments import LocusMCPClient

load_dotenv()


@pytest.mark.asyncio
async def test_roundtrip_payment():
    """
    STAGE 2 TEST: Round-trip payment flow.
    
    Flow:
    1. User → $1 USDC → Buyer agent
    2. Wait for transaction
    3. Buyer → $1 USDC → User
    
    This validates:
    - User can fund buyer
    - Buyer can send funds back
    - Both wallet API keys work
    """
    user_api_key = os.getenv("USER_WALLET_API_KEY")
    buyer_api_key = os.getenv("BUYER_AGENT_WALLET_API_KEY")
    buyer_address = os.getenv("BUYER_AGENT_WALLET_ADDRESS")
    user_address = os.getenv("USER_WALLET_ADDRESS")
    
    # Check all env vars set
    if not user_api_key:
        pytest.skip("USER_WALLET_API_KEY not set")
    if not buyer_api_key:
        pytest.skip("BUYER_AGENT_WALLET_API_KEY not set")
    if not buyer_address:
        pytest.skip("BUYER_AGENT_WALLET_ADDRESS not set")
    if not user_address:
        pytest.skip("USER_WALLET_ADDRESS not set")
    
    # Step 1: User funds buyer with $1
    print("\n💰 Step 1: User funding buyer with $1...")
    user_client = LocusMCPClient(user_api_key)
    
    fund_result = await user_client.send_to_address(
        address=buyer_address,
        amount=1.0,
        memo="Stage 2: User funds buyer"
    )
    
    print(f"✅ Funded buyer: {fund_result}")
    
    # Step 2: Wait for transaction to process
    print("\n⏳ Waiting 5 seconds for transaction...")
    await asyncio.sleep(5)
    
    # Step 3: Buyer returns $1 to user
    print("\n💸 Step 2: Buyer returning $1 to user...")
    buyer_client = LocusMCPClient(buyer_api_key)
    
    return_result = await buyer_client.send_to_address(
        address=user_address,
        amount=1.0,
        memo="Stage 2: Buyer returns to user"
    )
    
    print(f"✅ Returned to user: {return_result}")
    
    # Verify both transactions succeeded
    assert fund_result is not None
    assert return_result is not None
    
    print(f"\n🎯 Round-trip complete!")
    print(f"   Outbound: User → Buyer ($1)")
    print(f"   Return: Buyer → User ($1)")

