'use client';

import { useState, useEffect } from 'react';
import { supabase } from '@/lib/supabase';

interface BalanceDisplaySimpleProps {
  walletAddress: string;
  label: string;
}

export function BalanceDisplaySimple({ walletAddress, label }: BalanceDisplaySimpleProps) {
  const [balance, setBalance] = useState<string>('...');

  // Fetch initial balance
  useEffect(() => {
    const fetchBalance = async () => {
      try {
        const response = await fetch(`/api/balance?address=${walletAddress}`);
        const data = await response.json();
        if (response.ok) {
          setBalance(data.balance);
        }
      } catch (err) {
        console.error('Error fetching balance:', err);
      }
    };
    
    fetchBalance();
  }, [walletAddress]);

  // Subscribe to realtime balance updates
  useEffect(() => {
    if (!walletAddress) return;

    const channel = supabase
      .channel(`balance-simple-${walletAddress}`)
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
    <span>
      <span className="font-medium">{label}</span> ${balance}
    </span>
  );
}

