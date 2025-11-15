"""Locus MCP payment integration via JSON-RPC."""

import os
import httpx
from typing import Dict, Any, Optional


class LocusMCPClient:
    """Simple JSON-RPC client for Locus MCP server."""
    
    def __init__(self, api_key: str):
        """
        Initialize MCP client.
        
        Args:
            api_key: Locus API key (locus_...)
        """
        self.api_key = api_key
        base_url = os.getenv("LOCUS_MCP_URL", "https://mcp.paywithlocus.com")
        self.mcp_url = f"{base_url}/mcp" if not base_url.endswith("/mcp") else base_url
        self.request_id = 0
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call MCP tool via JSON-RPC 2.0.
        
        Args:
            tool_name: MCP tool name (e.g., "send_to_address")
            arguments: Tool arguments dict
            
        Returns:
            Tool result from MCP server
            
        Raises:
            Exception: If MCP returns error
        """
        self.request_id += 1
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.mcp_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                },
                json={
                    "jsonrpc": "2.0",
                    "id": self.request_id,
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": arguments
                    }
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"MCP HTTP error: {response.status_code} - {response.text}")
            
            # MCP returns SSE format - parse it
            response_text = response.text
            
            # Extract JSON from SSE format (data: {...})
            import json
            result_data = None
            
            for line in response_text.split('\n'):
                if line.startswith('data: '):
                    json_str = line[6:]  # Remove 'data: ' prefix
                    try:
                        result_data = json.loads(json_str)
                        break
                    except json.JSONDecodeError:
                        continue
            
            if not result_data:
                raise Exception(f"Could not parse MCP response: {response_text[:200]}")
            
            if "error" in result_data:
                raise Exception(f"MCP tool error: {result_data['error']}")
            
            return result_data.get("result", {})
    
    async def send_to_address(
        self,
        address: str,
        amount: float,
        memo: str
    ) -> Dict[str, Any]:
        """
        Send USDC to wallet address via Locus MCP.
        
        Args:
            address: Recipient wallet address (0x...)
            amount: Amount in USDC
            memo: Payment description
            
        Returns:
            MCP result with transaction details
        """
        return await self.call_tool(
            "send_to_address",
            {
                "address": address,
                "amount": amount,
                "memo": memo
            }
        )
    
    async def get_payment_context(self) -> Dict[str, Any]:
        """Get wallet balance and payment context."""
        return await self.call_tool("get_payment_context", {})

