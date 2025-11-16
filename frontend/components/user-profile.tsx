'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { RefreshCw } from 'lucide-react';
import { supabase } from '@/lib/supabase';

interface UserProfileProps {
  walletAddress: string;
}

export function UserProfile({ walletAddress }: UserProfileProps) {
  const [balance, setBalance] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const truncateAddress = (address: string) => {
    if (address.length <= 10) return address;
    return `${address.slice(0, 6)}...${address.slice(-4)}`;
  };

  const fetchBalance = async (isRetry = false) => {
    if (!isRetry) {
      setLoading(true);
    }
    setError(null);
    
    try {
      const response = await fetch('/api/balance');
      const data = await response.json();

      if (response.ok) {
        setBalance(data.balance);
        setLoading(false);
      } else {
        // If rate limited or error, retry after 1 second
        console.log('Balance fetch failed, retrying in 1 second...');
        setTimeout(() => {
          fetchBalance(true);
        }, 1000);
      }
    } catch (err) {
      console.error('Error fetching balance:', err);
      // Retry on error too
      setTimeout(() => {
        fetchBalance(true);
      }, 1000);
    }
  };

  // Fetch balance on component mount
  useEffect(() => {
    fetchBalance();
  }, []);

  // Subscribe to realtime balance updates
  useEffect(() => {
    if (!walletAddress) return;

    const channel = supabase
      .channel(`balance-${walletAddress}`)
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'balances',
          filter: `id=eq.${walletAddress}`
        },
        (payload) => {
          if (payload.new && 'balance_usdc' in payload.new) {
            const newBalance = (payload.new as any).balance_usdc;
            setBalance(newBalance.toFixed(2));
          }
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [walletAddress]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Hi, TJ</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Wallet Address */}
        <div>
          <p className="text-sm font-medium text-muted-foreground mb-1">
            Wallet Address
          </p>
          <p className="text-sm font-mono break-all">
            {truncateAddress(walletAddress)}
          </p>
        </div>

        {/* Base Balance */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <p className="text-sm font-medium text-muted-foreground">
              Base Balance
            </p>
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6"
              onClick={() => fetchBalance(false)}
              disabled={loading}
            >
              <RefreshCw className={`h-3 w-3 ${loading ? 'animate-spin' : ''}`} />
            </Button>
          </div>
          
          {balance ? (
            <p className="text-lg font-semibold">${balance} USDC</p>
          ) : error ? (
            <p className="text-sm text-destructive">{error}</p>
          ) : (
            <p className="text-sm text-muted-foreground">
              Click refresh to load balance
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

