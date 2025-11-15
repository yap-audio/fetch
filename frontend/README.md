# Seller Frontend Dashboard

A clean, minimal Next.js dashboard for sellers to view and fulfill intents from the hackathon demo.

## Features

- **Intent Display**: View all intents with images, descriptions, budgets, and status badges
- **User Profile**: Shows TJ's wallet address and USDC balance on Base (via Etherscan API)
- **Manual Balance Refresh**: Click the refresh icon to update the wallet balance on demand
- **Responsive Design**: Works on mobile and desktop with shadcn/ui components

## Tech Stack

- **Next.js 16** with App Router and TypeScript
- **shadcn/ui** for clean, accessible components
- **Supabase** for intent data storage
- **Etherscan API** for Base blockchain balance queries
- **Tailwind CSS** for styling

## Getting Started

### Prerequisites

All environment variables are already configured in `.env`:
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `NEXT_PUBLIC_USER_WALLET_ADDRESS`
- `ETHERSCAN_API_KEY`

### Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the dashboard.

### Production Build

```bash
npm run build
npm start
```

## Project Structure

```
frontend/
├── app/
│   ├── api/balance/route.ts   # Etherscan balance API endpoint
│   ├── layout.tsx              # Root layout
│   └── page.tsx                # Main dashboard page
├── components/
│   ├── intent-card.tsx         # Intent display card
│   ├── user-profile.tsx        # User profile sidebar
│   └── ui/                     # shadcn/ui components
└── lib/
    ├── supabase.ts             # Supabase client
    └── database.types.ts       # TypeScript types for Supabase tables
```

## Key Components

### IntentCard
Displays each intent with:
- Image from Supabase storage
- Truncated description
- Budget (max_amount_usd)
- Status badge (bottom right)
- Fulfill button (no action yet)

### UserProfile
Sidebar component showing:
- Greeting: "Hi, TJ"
- Truncated wallet address
- USDC balance on Base with manual refresh button

### Balance API
Server-side API route at `/api/balance`:
- Queries Etherscan API for Base mainnet (chain ID 8453)
- Fetches USDC token balance (6 decimals)
- Uses USDC contract address on Base: `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`
- Returns balance formatted as USD
- Keeps API key secure on the server

## Notes

- No authentication required (public demo)
- All intents are fetched from Supabase on page load
- Balance is only fetched on manual refresh (not auto-refreshed)
- Images are served from Supabase storage bucket `intent-images`
