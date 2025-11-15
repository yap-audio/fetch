"""Interactive demo of the negotiation agent."""

import asyncio
import json
import httpx
from database import get_intent
from dotenv import load_dotenv

load_dotenv()

# Real test intent ID
TEST_INTENT_ID = "32ec0fba-931e-49b2-b4c2-02a1d6929a9c"


async def run_negotiation(seller_message: str, conversation_history=None):
    """Run a single negotiation round."""
    url = "http://localhost:8000/negotiate"
    
    payload = {
        "intent_id": TEST_INTENT_ID,
        "seller_message": seller_message,
        "conversation_history": conversation_history or []
    }
    
    print(f"\n{'='*60}")
    print(f"🤝 SELLER: {seller_message}")
    print(f"{'='*60}")
    print("🤖 AGENT: ", end="", flush=True)
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        full_response = ""
        decision = None
        
        async with client.stream("POST", url, json=payload) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    
                    if data["type"] == "text":
                        print(data["content"], end="", flush=True)
                        full_response += data["content"]
                    elif data["type"] == "final":
                        decision = data["decision"]
                    elif data["type"] == "error":
                        print(f"\n❌ ERROR: {data['content']}")
                        return None, None
        
        print()  # New line after response
        
        if decision:
            decision_emoji = {
                "accept": "✅",
                "reject": "❌",
                "continue": "💬"
            }
            print(f"\n{decision_emoji.get(decision, '❓')} DECISION: {decision.upper()}")
        
        return full_response, decision


async def main():
    """Run an interactive negotiation demo."""
    print("="*60)
    print("🎯 NEGOTIATION AGENT DEMO")
    print("="*60)
    
    # Load intent details
    try:
        intent = get_intent(TEST_INTENT_ID)
        print(f"\n📋 Buyer's Intent:")
        print(f"   Item: {intent['description']}")
        print(f"   Max Budget: ${intent['max_amount_usd']}")
    except Exception as e:
        print(f"\n❌ Could not load intent: {e}")
        print("Make sure the database is set up correctly!")
        return
    
    print("\n" + "="*60)
    print("Starting negotiation scenarios...")
    print("="*60)
    
    # Scenario 1: High offer (should reject or counter)
    print("\n\n📍 SCENARIO 1: Seller offers way above budget")
    await asyncio.sleep(1)
    response1, decision1 = await run_negotiation(
        f"I have this item and can sell it to you for ${float(intent['max_amount_usd']) * 3:.2f}"
    )
    
    if decision1 == "continue":
        # Continue negotiation
        await asyncio.sleep(2)
        print("\n\n📍 SCENARIO 1 (continued): Seller responds")
        await run_negotiation(
            "Okay, how about half off then?",
            conversation_history=[
                {"role": "seller", "content": f"I have this item and can sell it to you for ${float(intent['max_amount_usd']) * 3:.2f}"},
                {"role": "buyer", "content": response1}
            ]
        )
    
    await asyncio.sleep(3)
    
    # Scenario 2: Reasonable offer
    print("\n\n📍 SCENARIO 2: Seller offers at 60% of budget")
    await run_negotiation(
        f"I can offer this to you for ${float(intent['max_amount_usd']) * 0.6:.2f}"
    )
    
    await asyncio.sleep(3)
    
    # Scenario 3: Great deal
    print("\n\n📍 SCENARIO 3: Seller offers well below budget")
    await run_negotiation(
        f"How about ${float(intent['max_amount_usd']) * 0.3:.2f}?"
    )
    
    print("\n\n" + "="*60)
    print("✨ Demo complete!")
    print("="*60)


if __name__ == "__main__":
    print("\n⚠️  Make sure the server is running: python main.py")
    print("⚠️  Press Ctrl+C to cancel if needed\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Demo cancelled by user")
    except httpx.ConnectError:
        print("\n\n❌ Could not connect to server!")
        print("   Make sure to run: python main.py")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")

