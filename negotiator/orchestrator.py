#!/usr/bin/env python3
"""
Orchestrator for agent-to-agent negotiations.

Manages conversation between buyer and seller agents via HTTP.
"""

import asyncio
import json
import httpx
import sys
from typing import Dict, List, Optional, Tuple, Any
from database import get_intent

# Import A2A SDK (optional dependency for A2A protocol support)
try:
    from a2a.client import A2AClient, A2ACardResolver
    from a2a.types import MessageSendParams, SendMessageRequest
    from uuid import uuid4
    import httpx as httpx_module
    A2A_AVAILABLE = True
except ImportError:
    A2A_AVAILABLE = False


class NegotiationOrchestrator:
    """Coordinates negotiations between buyer and seller agents."""
    
    def __init__(
        self,
        buyer_url: str = "http://localhost:8000",
        seller_url: str = "http://localhost:8001",
        timeout: float = 120.0,
        protocol: str = "http"
    ):
        """
        Initialize orchestrator.
        
        Args:
            buyer_url: URL of buyer agent service
            seller_url: URL of seller agent service
            timeout: Timeout for HTTP requests
            protocol: Communication protocol ("http" or "a2a")
        """
        self.buyer_url = buyer_url
        self.seller_url = seller_url
        self.timeout = timeout
        self.protocol = protocol
    
    async def call_agent(
        self,
        url: str,
        agent_type: str,
        intent_id: str,
        message: str,
        conversation_history: List[Dict[str, str]]
    ) -> Tuple[str, str, Optional[Dict[str, Any]]]:
        """
        Call an agent and get its response (HTTP or A2A based on protocol).
        
        Returns:
            Tuple of (full_response, decision, payment_result)
        """
        if self.protocol == "a2a":
            response, decision = await self._call_agent_a2a(url, agent_type, intent_id, message, conversation_history)
            return response, decision, None  # A2A doesn't return payments yet
        else:
            return await self._call_agent_http(url, agent_type, intent_id, message, conversation_history)
    
    async def _call_agent_http(
        self,
        url: str,
        agent_type: str,
        intent_id: str,
        message: str,
        conversation_history: List[Dict[str, str]]
    ) -> Tuple[str, str, Optional[Dict[str, Any]]]:
        """Call agent via HTTP/SSE."""
        payload = {
            "intent_id": intent_id,
            "seller_message": message,
            "conversation_history": conversation_history,
            "agent_type": agent_type
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            full_response = ""
            decision = "continue"
            payment_result = None
            
            async with client.stream("POST", f"{url}/negotiate", json=payload) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = json.loads(line[6:])
                        
                        if data["type"] == "text":
                            full_response += data["content"]
                        elif data["type"] == "final":
                            decision = data["decision"]
                            payment_result = data.get("payment_result")
            
            return full_response, decision, payment_result
    
    async def _call_agent_a2a(
        self,
        url: str,
        agent_type: str,
        intent_id: str,
        message: str,
        conversation_history: List[Dict[str, str]]
    ) -> Tuple[str, str]:
        """Call agent via A2A protocol."""
        if not A2A_AVAILABLE:
            raise ImportError("a2a-sdk not installed. Install with: uv add a2a-sdk")
        
        async with httpx_module.AsyncClient(timeout=self.timeout) as httpx_client:
            # Resolve agent card
            resolver = A2ACardResolver(
                httpx_client=httpx_client,
                base_url=url
            )
            
            agent_card = await resolver.get_agent_card()
            
            # Create A2A client
            client = A2AClient(
                httpx_client=httpx_client,
                agent_card=agent_card
            )
            
            # Build message payload with metadata on the message
            send_message_payload = {
                'message': {
                    'role': 'user',
                    'parts': [
                        {'kind': 'text', 'text': message}
                    ],
                    'messageId': uuid4().hex,
                    'metadata': {
                        'intent_id': intent_id,
                        'agent_type': agent_type
                    }
                }
            }
            
            request = SendMessageRequest(
                id=str(uuid4()),
                params=MessageSendParams(**send_message_payload)
            )
            
            # Send message
            response = await client.send_message(request)
            
            # Extract response text
            full_response = ""
            if hasattr(response, 'root') and hasattr(response.root, 'result'):
                result = response.root.result
                if hasattr(result, 'parts'):
                    for part in result.parts:
                        if hasattr(part, 'root') and hasattr(part.root, 'text'):
                            full_response += part.root.text
            
            # Extract decision from response text
            decision = "continue"
            if "DECISION: ACCEPT" in full_response.upper():
                decision = "accept"
            elif "DECISION: REJECT" in full_response.upper():
                decision = "reject"
            
            return full_response, decision
    
    async def run_negotiation(
        self,
        intent_id: str,
        max_rounds: int = 10,
        verbose: bool = True
    ) -> Dict[str, any]:
        """
        Run a full negotiation between buyer and seller.
        
        Args:
            intent_id: UUID of the intent to negotiate
            max_rounds: Maximum number of negotiation rounds
            verbose: Print negotiation progress
            
        Returns:
            Dict with negotiation results
        """
        # Load intent
        intent = get_intent(intent_id)
        
        if verbose:
            print("\n" + "="*70)
            print("🤝 AGENT-TO-AGENT NEGOTIATION")
            print("="*70)
            print(f"\nIntent: {intent['description'][:100]}...")
            print(f"Max Budget: ${intent['max_amount_usd']}")
            print(f"Seller Minimum: ${float(intent['max_amount_usd']) * 0.65:.2f}")
            print("\n" + "="*70)
        
        conversation_history = []
        
        # Seller initiates with an offer
        initial_offer = float(intent['max_amount_usd']) * 1.2  # Start 20% above max
        
        if verbose:
            print(f"\n💼 SELLER: Opening offer - ${initial_offer:.2f}")
        
        for round_num in range(max_rounds):
            if verbose:
                print(f"\n{'─'*70}")
                print(f"Round {round_num + 1}")
                print(f"{'─'*70}")
            
            # Determine who speaks this round
            if round_num == 0:
                # Seller starts
                current_speaker = "seller"
                current_url = self.seller_url
                message = f"I'm offering this item for ${initial_offer:.2f}"
            elif len(conversation_history) % 2 == 0:
                # Seller's turn
                current_speaker = "seller"
                current_url = self.seller_url
                # Get buyer's last message
                message = conversation_history[-1]["content"]
            else:
                # Buyer's turn
                current_speaker = "buyer"
                current_url = self.buyer_url
                # Get seller's last message
                message = conversation_history[-1]["content"]
            
            # Get agent response
            if verbose:
                print(f"\n{current_speaker.upper()} thinking...")
            
            response, decision, payment_result = await self.call_agent(
                current_url,
                current_speaker,
                intent_id,
                message,
                conversation_history
            )
            
            if verbose:
                print(f"\n{current_speaker.upper()}: {response[:200]}{'...' if len(response) > 200 else ''}")
                print(f"\nDecision: {decision.upper()}")
                if payment_result:
                    print(f"💳 Payment executed: {payment_result}")
            
            # Add to history with payment result
            conversation_entry = {
                "role": current_speaker,
                "content": response
            }
            if payment_result:
                conversation_entry["payment_result"] = payment_result
            
            conversation_history.append(conversation_entry)
            
            # Check if negotiation is complete
            if decision == "accept":
                if verbose:
                    print("\n" + "="*70)
                    print("✅ DEAL REACHED!")
                    print("="*70)
                
                return {
                    "status": "success",
                    "outcome": "accepted",
                    "rounds": round_num + 1,
                    "conversation": conversation_history,
                    "final_decision_by": current_speaker
                }
            
            elif decision == "reject":
                if verbose:
                    print("\n" + "="*70)
                    print("❌ NEGOTIATION FAILED")
                    print("="*70)
                
                return {
                    "status": "failed",
                    "outcome": "rejected",
                    "rounds": round_num + 1,
                    "conversation": conversation_history,
                    "final_decision_by": current_speaker
                }
        
        # Max rounds reached
        if verbose:
            print("\n" + "="*70)
            print("⏱️  MAX ROUNDS REACHED - NO DEAL")
            print("="*70)
        
        return {
            "status": "timeout",
            "outcome": "max_rounds_reached",
            "rounds": max_rounds,
            "conversation": conversation_history
        }


async def main():
    """Main entry point for orchestrator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run agent-to-agent negotiation")
    parser.add_argument("--intent-id", required=True, help="Intent UUID to negotiate")
    parser.add_argument("--buyer-url", default="http://localhost:8000", help="Buyer service URL")
    parser.add_argument("--seller-url", default="http://localhost:8001", help="Seller service URL")
    parser.add_argument("--max-rounds", type=int, default=10, help="Maximum negotiation rounds")
    parser.add_argument("--quiet", action="store_true", help="Suppress verbose output")
    parser.add_argument("--protocol", default="http", choices=["http", "a2a"], help="Protocol to use (http or a2a)")
    
    args = parser.parse_args()
    
    orchestrator = NegotiationOrchestrator(
        buyer_url=args.buyer_url,
        seller_url=args.seller_url,
        protocol=args.protocol
    )
    
    result = await orchestrator.run_negotiation(
        intent_id=args.intent_id,
        max_rounds=args.max_rounds,
        verbose=not args.quiet
    )
    
    print(f"\n\nFinal Result: {result['status']}")
    print(f"Outcome: {result['outcome']}")
    print(f"Rounds: {result['rounds']}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Negotiation cancelled")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

