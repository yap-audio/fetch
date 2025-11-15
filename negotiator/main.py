"""FastAPI service for negotiation agent."""

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, field_validator
from typing import List, Dict, Optional, Literal, Any
import json
import asyncio
import httpx
import os
import logging

from database import get_intent, IntentNotFoundError, update_intent_with_transactions
from agent import NegotiationAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import transaction tracker (optional)
try:
    from transaction_tracker import TransactionTracker
    TRACKER_AVAILABLE = True
except ImportError:
    TRACKER_AVAILABLE = False

app = FastAPI(title="Negotiation Agent API")


class NegotiateRequest(BaseModel):
    """Request model for negotiation endpoint."""
    intent_id: str
    seller_message: str
    conversation_history: Optional[List[Dict[str, str]]] = None
    agent_type: Literal["buyer", "seller"] = "buyer"


class InitiateRequest(BaseModel):
    """Request model for initiate endpoint."""
    intent_id: str
    agent_type: Literal["seller"] = "seller"  # Only sellers initiate


@app.get("/")
async def root():
    """Health check endpoint."""
    service_name = os.getenv("SERVICE_NAME", "unknown")
    return {
        "status": "ok",
        "service": "negotiation-agent",
        "service_name": service_name
    }


@app.post("/negotiate")
async def negotiate(request: NegotiateRequest):
    """
    Negotiate on behalf of a buyer or seller.
    
    Streams responses via Server-Sent Events (SSE).
    
    Args:
        request: Negotiation request with agent_type ("buyer" or "seller")
    """
    logger.info(f"📥 /negotiate called - agent_type: {request.agent_type}, intent_id: {request.intent_id}")
    logger.info(f"   Message length: {len(request.seller_message)}, History length: {len(request.conversation_history or [])}")
    
    # Validate agent_type
    if request.agent_type not in ["buyer", "seller"]:
        logger.error(f"❌ Invalid agent_type: {request.agent_type}")
        raise HTTPException(status_code=400, detail="agent_type must be 'buyer' or 'seller'")
    
    # Fetch intent from database
    try:
        logger.info(f"🔍 Fetching intent {request.intent_id} from database...")
        intent_data = get_intent(request.intent_id)
        logger.info(f"✅ Intent found: ${intent_data.get('max_amount_usd')} - {intent_data.get('description')[:50]}...")
    except IntentNotFoundError:
        logger.error(f"❌ Intent {request.intent_id} not found")
        raise HTTPException(status_code=404, detail=f"Intent {request.intent_id} not found")
    except Exception as e:
        logger.error(f"❌ Database error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    # Create negotiation agent with specified type
    logger.info(f"🤖 Creating {request.agent_type} agent...")
    agent = NegotiationAgent(intent_data, agent_type=request.agent_type)
    logger.info(f"✅ Agent created, starting negotiation stream...")
    
    # Stream responses
    async def event_generator():
        """Generate SSE events from agent responses."""
        try:
            chunk_count = 0
            async for chunk in agent.negotiate(
                seller_message=request.seller_message,
                conversation_history=request.conversation_history
            ):
                chunk_count += 1
                # Format as SSE
                data = json.dumps(chunk)
                yield f"data: {data}\n\n"
                
                # Log every 10th chunk and final messages
                if chunk_count % 10 == 0 or chunk.get("type") == "final":
                    logger.info(f"📤 Chunk {chunk_count}: type={chunk.get('type')}, decision={chunk.get('decision', 'N/A')}")
                
                # Small delay for better streaming UX
                await asyncio.sleep(0.01)
            logger.info(f"✅ Negotiation stream completed ({chunk_count} chunks)")
        except Exception as e:
            logger.error(f"❌ Error in event_generator: {str(e)}")
            error_data = json.dumps({
                "type": "error",
                "content": str(e),
                "is_final": True
            })
            yield f"data: {error_data}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


async def generate_opening_pitch(agent: NegotiationAgent, intent_data: Dict[str, Any]) -> str:
    """
    Generate opening sales pitch for seller agent.
    
    Args:
        agent: Seller agent instance
        intent_data: Intent data for context
        
    Returns:
        Opening pitch text from seller
    """
    prompt = (
        "You're a seller with this item. Generate an engaging opening message "
        "to a potential buyer to start the negotiation. Introduce the item, "
        "highlight its value, and make an initial offer. Be professional and persuasive."
    )
    
    full_pitch = ""
    async for chunk in agent.negotiate(prompt, []):
        if chunk["type"] == "final":
            full_pitch = chunk["content"]
            break
    
    return full_pitch


@app.post("/initiate")
async def initiate_negotiation(request: InitiateRequest):
    """
    Initiate a negotiation (seller generates pitch and contacts buyer).
    
    Flow:
    1. Seller agent generates opening pitch
    2. Sends pitch to buyer agent (via BUYER_AGENT_URL)
    3. Returns buyer's response
    
    Returns:
        {
          "seller_pitch": "...",
          "buyer_response": "...",
          "buyer_decision": "continue|accept|reject"
        }
    """
    # Get intent
    try:
        intent_data = get_intent(request.intent_id)
    except IntentNotFoundError:
        raise HTTPException(status_code=404, detail=f"Intent {request.intent_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    # Create seller agent
    seller_agent = NegotiationAgent(intent_data, agent_type="seller")
    
    # Generate opening pitch
    opening_pitch = await generate_opening_pitch(seller_agent, intent_data)
    
    # Get buyer URL from environment
    buyer_url = os.getenv("BUYER_AGENT_URL")
    if not buyer_url:
        raise HTTPException(
            status_code=500, 
            detail="BUYER_AGENT_URL not configured. Set environment variable."
        )
    
    # Send to buyer agent
    async with httpx.AsyncClient(timeout=120.0) as client:
        buyer_response_text = ""
        buyer_decision = "continue"
        
        try:
            async with client.stream(
                "POST",
                f"{buyer_url}/negotiate",
                json={
                    "intent_id": request.intent_id,
                    "seller_message": opening_pitch,
                    "agent_type": "buyer"
                }
            ) as response:
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Buyer agent returned {response.status_code}"
                    )
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = json.loads(line[6:])
                        if data["type"] == "final":
                            buyer_response_text = data["content"]
                            buyer_decision = data["decision"]
        except httpx.ConnectError:
            raise HTTPException(
                status_code=500,
                detail=f"Could not connect to buyer agent at {buyer_url}"
            )
    
    return {
        "seller_pitch": opening_pitch,
        "buyer_response": buyer_response_text,
        "buyer_decision": buyer_decision
    }


@app.get("/intent/{intent_id}/transactions")
async def get_intent_transactions_endpoint(intent_id: str):
    """
    Get Base blockchain transaction hashes for an intent.
    
    Returns transaction hashes and Basescan links.
    """
    try:
        intent = get_intent(intent_id)
    except IntentNotFoundError:
        raise HTTPException(status_code=404, detail=f"Intent {intent_id} not found")
    
    tx_seller = intent.get("tx_buyer_to_seller_id")
    tx_user = intent.get("tx_buyer_to_user_id")
    
    return {
        "intent_id": intent_id,
        "tx_buyer_to_seller": tx_seller,
        "tx_buyer_to_user": tx_user,
        "basescan_links": {
            "seller_payment": f"https://basescan.org/tx/{tx_seller}" if tx_seller else None,
            "user_refund": f"https://basescan.org/tx/{tx_user}" if tx_user else None
        }
    }


@app.post("/intent/{intent_id}/update-transactions")
async def manually_update_transactions(intent_id: str):
    """
    Manually trigger transaction hash update from Etherscan.
    
    Buyer service only.
    """
    if not TRACKER_AVAILABLE:
        raise HTTPException(status_code=501, detail="Transaction tracker not available")
    
    # Only allow on buyer service
    service_name = os.getenv("SERVICE_NAME", "").lower()
    if service_name == "seller":
        raise HTTPException(status_code=403, detail="Only buyer service can update transactions")
    
    # Query Etherscan for latest transactions
    tracker = TransactionTracker()
    tx_hashes = await tracker.get_latest_payment_txs()
    
    # Update database
    result = update_intent_with_transactions(
        intent_id,
        tx_hashes["tx_buyer_to_seller"],
        tx_hashes["tx_buyer_to_user"]
    )
    
    return {
        "updated": True,
        "intent_id": intent_id,
        "transactions": tx_hashes,
        "basescan_links": {
            "seller_payment": f"https://basescan.org/tx/{tx_hashes['tx_buyer_to_seller']}" if tx_hashes["tx_buyer_to_seller"] else None,
            "user_refund": f"https://basescan.org/tx/{tx_hashes['tx_buyer_to_user']}" if tx_hashes["tx_buyer_to_user"] else None
        }
    }


if __name__ == "__main__":
    import uvicorn
    import sys
    
    # Parse port from command line arguments
    port = 8000
    for i, arg in enumerate(sys.argv):
        if arg == "--port" and i + 1 < len(sys.argv):
            port = int(sys.argv[i + 1])
            break
    
    print(f"Starting negotiation service on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)

