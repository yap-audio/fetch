"""FastAPI service for negotiation agent."""

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, field_validator
from typing import List, Dict, Optional, Literal, Any
import json
import asyncio
import httpx
import os

from database import get_intent, IntentNotFoundError
from agent import NegotiationAgent

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
    return {"status": "ok", "service": "negotiation-agent"}


@app.post("/negotiate")
async def negotiate(request: NegotiateRequest):
    """
    Negotiate on behalf of a buyer or seller.
    
    Streams responses via Server-Sent Events (SSE).
    
    Args:
        request: Negotiation request with agent_type ("buyer" or "seller")
    """
    # Validate agent_type
    if request.agent_type not in ["buyer", "seller"]:
        raise HTTPException(status_code=400, detail="agent_type must be 'buyer' or 'seller'")
    
    # Fetch intent from database
    try:
        intent_data = get_intent(request.intent_id)
    except IntentNotFoundError:
        raise HTTPException(status_code=404, detail=f"Intent {request.intent_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    # Create negotiation agent with specified type
    agent = NegotiationAgent(intent_data, agent_type=request.agent_type)
    
    # Stream responses
    async def event_generator():
        """Generate SSE events from agent responses."""
        try:
            async for chunk in agent.negotiate(
                seller_message=request.seller_message,
                conversation_history=request.conversation_history
            ):
                # Format as SSE
                data = json.dumps(chunk)
                yield f"data: {data}\n\n"
                
                # Small delay for better streaming UX
                await asyncio.sleep(0.01)
        except Exception as e:
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

