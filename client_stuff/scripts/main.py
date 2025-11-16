import asyncio

from mcp_agent.app import MCPApp
from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM

app = MCPApp(name="hello_world")

async def main():
    async with app.run():
        agent = Agent(
            name="money sender",
            instruction="Send $1 of USDC to this address 0xfb7d867d5f0d92c784aac2b7a9df17557c8bfc47",
            server_names=["locus-server"],
        )
        async with agent:
            llm = await agent.attach_llm(OpenAIAugmentedLLM)
            answer = await llm.generate_str("Please send the $1")
            print(answer)


if __name__ == "__main__":
    asyncio.run(main())