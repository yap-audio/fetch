import { NextResponse } from 'next/server';

// USDC contract address on Base mainnet
const USDC_CONTRACT_ADDRESS = '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913';

export async function GET(request: Request) {
  const apiKey = process.env.ETHERSCAN_API_KEY;
  
  // Get address from query params or use user wallet as default
  const { searchParams } = new URL(request.url);
  const walletAddress = searchParams.get('address') || process.env.NEXT_PUBLIC_USER_WALLET_ADDRESS;

  if (!apiKey || !walletAddress) {
    return NextResponse.json(
      { error: 'Missing required environment variables' },
      { status: 500 }
    );
  }

  try {
    const url = `https://api.etherscan.io/v2/api?chainid=8453&module=account&action=tokenbalance&contractaddress=${USDC_CONTRACT_ADDRESS}&address=${walletAddress}&apikey=${apiKey}`;
    
    const response = await fetch(url);
    const data = await response.json();

    console.log('Etherscan API response:', JSON.stringify(data, null, 2));

    if (data.status === '1' && data.result) {
      // Convert USDC units to USDC (divide by 10^6, USDC has 6 decimals)
      const balanceInUsdc = Number(data.result) / 1_000_000;
      const formattedBalance = balanceInUsdc.toFixed(2);

      return NextResponse.json({
        balance: formattedBalance,
        balanceRaw: data.result,
      });
    } else {
      console.error('Etherscan API returned error:', data);
      return NextResponse.json(
        { error: data.message || data.result || 'Failed to fetch balance from Etherscan' },
        { status: 500 }
      );
    }
  } catch (error) {
    console.error('Error fetching balance:', error);
    return NextResponse.json(
      { error: 'Failed to fetch balance' },
      { status: 500 }
    );
  }
}

