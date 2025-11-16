import asyncio
import os
from dotenv import load_dotenv
from src.locus import LocusMCPClient

load_dotenv()

async def main():
    api_key = os.getenv('LOCUS_API_KEY')
    if not api_key:
        raise ValueError("LOCUS_API_KEY not found in environment variables")
    client = LocusMCPClient(api_key=api_key)
    result = await client.send_to_address(address='0xfb7d867d5f0d92c784aac2b7a9df17557c8bfc47', amount=0.5, memo='hi ty')
    print(result)

if __name__ == "__main__":
    asyncio.run(main())