import { supabase } from '@/lib/supabase';
import { UserProfile } from '@/components/user-profile';
import { AgentProfile } from '@/components/agent-profile';
import { IntentsListRealtime } from '@/components/intents-list-realtime';
import { Intent } from '@/lib/database.types';

export const dynamic = 'force-dynamic';

export default async function Home() {
  const walletAddress = process.env.NEXT_PUBLIC_USER_WALLET_ADDRESS || '';
  const buyerWallet = process.env.NEXT_PUBLIC_BUYER_AGENT_WALLET_ADDRESS || '';
  const sellerWallet = process.env.NEXT_PUBLIC_SELLER_AGENT_WALLET_ADDRESS || '';

  // Fetch intents from Supabase
  const { data: intents, error } = await supabase
    .from('intents')
    .select('*')
    .order('created_at', { ascending: false })
    .returns<Intent[]>();

  if (error) {
    console.error('Error fetching intents:', error);
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b">
        <div className="container mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold">Hi, TJ</h1>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="flex flex-col lg:flex-row gap-8">
          {/* Intents Grid - Main Content */}
          <div className="flex-1">
            <IntentsListRealtime initialIntents={intents || []} />
          </div>

          {/* Wallets Sidebar */}
          <aside className="w-full lg:w-80 space-y-6">
            <UserProfile walletAddress={walletAddress} />
            <AgentProfile agentName="Buyer Agent" walletAddress={buyerWallet} />
            <AgentProfile agentName="Seller Agent" walletAddress={sellerWallet} />
          </aside>
        </div>
      </main>
    </div>
  );
}
