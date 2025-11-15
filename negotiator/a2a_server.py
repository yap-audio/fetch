#!/usr/bin/env python3
"""
A2A Server for Negotiation Agent.

Thin wrapper around existing NegotiationAgent that exposes A2A protocol interface.
"""

import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from a2a.utils import new_agent_text_message

from agent import NegotiationAgent
from database import get_intent


class NegotiationAgentExecutor(AgentExecutor):
    """A2A Agent Executor that wraps our existing NegotiationAgent."""
    
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Execute negotiation task."""
        # Get user input message
        message = context.get_user_input()
        
        # Extract metadata from context (metadata can be on message or context)
        metadata = context.metadata or (context.message.metadata if context.message and hasattr(context.message, 'metadata') else {})
        
        intent_id = metadata.get("intent_id") if metadata else None
        agent_type = metadata.get("agent_type", "buyer") if metadata else "buyer"
        
        if not intent_id:
            await event_queue.enqueue_event(
                new_agent_text_message(f"Error: intent_id required in metadata. Got metadata: {metadata}")
            )
            return
        
        # Use existing agent logic
        intent = get_intent(intent_id)
        agent = NegotiationAgent(intent, agent_type=agent_type)
        
        # Get response from agent
        full_response = ""
        async for chunk in agent.negotiate(message, []):
            if chunk["type"] == "final":
                full_response = chunk["content"]
                break
        
        # Send response via event queue
        await event_queue.enqueue_event(new_agent_text_message(full_response))
    
    async def cancel(
        self, 
        context: RequestContext, 
        event_queue: EventQueue
    ) -> None:
        """Handle cancellation (not implemented)."""
        raise Exception('Cancellation not supported')


if __name__ == "__main__":
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="Run A2A Negotiation Server")
    parser.add_argument("--port", type=int, default=8002, help="Port to run server on")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    args = parser.parse_args()
    
    # Define agent skill
    skill = AgentSkill(
        id='negotiate',
        name='Negotiation',
        description='Negotiates on behalf of buyer or seller for marketplace items',
        tags=['negotiation', 'marketplace'],
        examples=['negotiate this deal', 'make an offer']
    )
    
    # Define agent card
    agent_card = AgentCard(
        name='Negotiation Agent',
        description='Negotiates marketplace deals on behalf of buyers or sellers',
        url=f'http://{args.host}:{args.port}/',
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill]
    )
    
    # Create request handler with our executor
    request_handler = DefaultRequestHandler(
        agent_executor=NegotiationAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )
    
    # Create A2A server
    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler
    )
    
    print(f"Starting A2A Negotiation Server on {args.host}:{args.port}")
    
    try:
        uvicorn.run(server.build(), host=args.host, port=args.port)
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
        sys.exit(0)

