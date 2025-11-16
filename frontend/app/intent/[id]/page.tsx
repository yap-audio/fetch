import { notFound } from 'next/navigation';
import Link from 'next/link';
import { supabase } from '@/lib/supabase';
import { Intent } from '@/lib/database.types';
import { Button } from '@/components/ui/button';
import { ArrowLeft } from 'lucide-react';
import { IntentDetailClient } from '@/components/intent-detail-client';
import { BalanceDisplaySimple } from '@/components/balance-display-simple';

export const dynamic = 'force-dynamic';

interface IntentPageProps {
  params: Promise<{ id: string }>;
}

export default async function IntentPage({ params }: IntentPageProps) {
  const { id } = await params;
  
  const walletAddress = process.env.NEXT_PUBLIC_USER_WALLET_ADDRESS || '';
  const buyerWallet = process.env.NEXT_PUBLIC_BUYER_AGENT_WALLET_ADDRESS || '';
  const sellerWallet = process.env.NEXT_PUBLIC_SELLER_AGENT_WALLET_ADDRESS || '';
  
  // Fetch intent from Supabase
  const response = await supabase
    .from('intents')
    .select('*')
    .eq('uuid', id)
    .single();

  const intent = response.data as Intent | null;
  const error = response.error;

  if (error || !intent) {
    notFound();
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <Link href="/">
              <Button variant="ghost" size="sm">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Dashboard
              </Button>
            </Link>
            
            {/* Wallet Balances */}
            <div className="flex items-center gap-4 text-sm">
              <BalanceDisplaySimple walletAddress={walletAddress} label="TJ" />
              <span className="text-muted-foreground">|</span>
              <BalanceDisplaySimple walletAddress={buyerWallet} label="Buyer Agent" />
              <span className="text-muted-foreground">|</span>
              <BalanceDisplaySimple walletAddress={sellerWallet} label="Seller Agent" />
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <IntentDetailClient initialIntent={intent} />
    </div>
  );
}

