"""FastAPI service for negotiation agent."""

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, field_validator
from typing import List, Dict, Optional, Literal
import json
import asyncio

from database import get_intent, IntentNotFoundError
from agent import NegotiationAgent

app = FastAPI(title="Negotiation Agent API")


class NegotiateRequest(BaseModel):
    """Request model for negotiation endpoint."""
    intent_id: str
    seller_message: str
    conversation_history: Optional[List[Dict[str, str]]] = None
    agent_type: Literal["buyer", "seller"] = "buyer"


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

