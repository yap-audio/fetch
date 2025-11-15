'use client';

import { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

interface NegotiationStreamProps {
  intentId: string;
  onStart?: () => void;
  onComplete?: (outcome: string) => void;
}

interface Message {
  role: 'seller' | 'buyer';
  content: string;
  decision?: string;
  round: number;
}

export function NegotiationStream({ intentId, onStart, onComplete }: NegotiationStreamProps) {
  const [isNegotiating, setIsNegotiating] = useState(false);
  const [sellerMessages, setSellerMessages] = useState<Message[]>([]);
  const [buyerMessages, setBuyerMessages] = useState<Message[]>([]);
  const [currentSellerContent, setCurrentSellerContent] = useState('');
  const [currentBuyerContent, setCurrentBuyerContent] = useState('');
  const [sellerThinking, setSellerThinking] = useState(false);
  const [buyerThinking, setBuyerThinking] = useState(false);
  const [outcome, setOutcome] = useState<string | null>(null);
  const [rounds, setRounds] = useState(0);
  const [error, setError] = useState<string | null>(null);
  
  const sellerScrollRef = useRef<HTMLDivElement>(null);
  const buyerScrollRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    sellerScrollRef.current?.scrollTo({
      top: sellerScrollRef.current.scrollHeight,
      behavior: 'smooth'
    });
  }, [sellerMessages, currentSellerContent]);

  useEffect(() => {
    buyerScrollRef.current?.scrollTo({
      top: buyerScrollRef.current.scrollHeight,
      behavior: 'smooth'
    });
  }, [buyerMessages, currentBuyerContent]);

  const startNegotiation = () => {
    setIsNegotiating(true);
    setSellerMessages([]);
    setBuyerMessages([]);
    setCurrentSellerContent('');
    setCurrentBuyerContent('');
    setOutcome(null);
    setError(null);
    onStart?.();

    const eventSource = new EventSource(`/api/negotiate/${intentId}`);
    eventSourceRef.current = eventSource;

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.type === 'start') {
          // Negotiation started
          setRounds(data.maxRounds);
        } else if (data.type === 'seller') {
          if (data.phase === 'thinking') {
            setSellerThinking(true);
            setCurrentSellerContent('');
          } else if (data.phase === 'response') {
            setSellerThinking(false);
            setCurrentSellerContent(prev => prev + data.content);
          } else if (data.phase === 'decision') {
            setSellerThinking(false);
            setSellerMessages(prev => [
              ...prev,
              {
                role: 'seller',
                content: currentSellerContent,
                decision: data.decision,
                round: data.round
              }
            ]);
            setCurrentSellerContent('');
          }
        } else if (data.type === 'buyer') {
          if (data.phase === 'thinking') {
            setBuyerThinking(true);
            setCurrentBuyerContent('');
          } else if (data.phase === 'response') {
            setBuyerThinking(false);
            setCurrentBuyerContent(prev => prev + data.content);
          } else if (data.phase === 'decision') {
            setBuyerThinking(false);
            setBuyerMessages(prev => [
              ...prev,
              {
                role: 'buyer',
                content: currentBuyerContent,
                decision: data.decision,
                round: data.round
              }
            ]);
            setCurrentBuyerContent('');
          }
        } else if (data.type === 'complete') {
          setOutcome(data.outcome);
          setRounds(data.rounds);
          setIsNegotiating(false);
          eventSource.close();
          onComplete?.(data.outcome);
        } else if (data.type === 'error') {
          setError(data.content);
          setIsNegotiating(false);
          eventSource.close();
        }
      } catch (e) {
        console.error('Error parsing SSE data:', e);
      }
    };

    eventSource.onerror = () => {
      setError('Connection error');
      setIsNegotiating(false);
      eventSource.close();
    };
  };

  const stopNegotiation = () => {
    eventSourceRef.current?.close();
    setIsNegotiating(false);
  };

  const getOutcomeBadge = () => {
    if (!outcome) return null;
    
    const variants = {
      accepted: 'default',
      rejected: 'destructive',
      max_rounds_reached: 'secondary'
    } as const;

    const labels = {
      accepted: '✅ Deal Reached!',
      rejected: '❌ No Deal',
      max_rounds_reached: '⏱️ Max Rounds Reached'
    } as const;

    return (
      <Badge variant={variants[outcome as keyof typeof variants] || 'secondary'} className="text-lg py-2 px-4">
        {labels[outcome as keyof typeof labels] || outcome}
      </Badge>
    );
  };

  return (
    <div className="space-y-4">
      {!isNegotiating && !outcome && (
        <div className="flex justify-center">
          <Button
            size="lg"
            onClick={startNegotiation}
            disabled={isNegotiating}
          >
            Negotiate for me
          </Button>
        </div>
      )}

      {error && (
        <Card className="border-destructive">
          <CardContent className="pt-6">
            <p className="text-destructive">Error: {error}</p>
          </CardContent>
        </Card>
      )}

      {(isNegotiating || sellerMessages.length > 0 || buyerMessages.length > 0) && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Seller Column */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Seller Agent</span>
                {sellerThinking && (
                  <Badge variant="outline">Thinking...</Badge>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div
                ref={sellerScrollRef}
                className="space-y-4 max-h-[600px] overflow-y-auto pr-4"
              >
                {sellerMessages.map((msg, idx) => (
                  <div key={idx} className="p-4 bg-muted rounded-lg">
                    <div className="flex items-start justify-between mb-2">
                      <span className="text-sm font-medium">Round {msg.round}</span>
                      {msg.decision && (
                        <Badge variant="outline" className="text-xs">
                          {msg.decision}
                        </Badge>
                      )}
                    </div>
                    <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                  </div>
                ))}
                {currentSellerContent && (
                  <div className="p-4 bg-muted rounded-lg">
                    <p className="text-sm whitespace-pre-wrap">{currentSellerContent}</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Buyer Column */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Buyer Agent</span>
                {buyerThinking && (
                  <Badge variant="outline">Thinking...</Badge>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div
                ref={buyerScrollRef}
                className="space-y-4 max-h-[600px] overflow-y-auto pr-4"
              >
                {buyerMessages.map((msg, idx) => (
                  <div key={idx} className="p-4 bg-muted rounded-lg">
                    <div className="flex items-start justify-between mb-2">
                      <span className="text-sm font-medium">Round {msg.round}</span>
                      {msg.decision && (
                        <Badge variant="outline" className="text-xs">
                          {msg.decision}
                        </Badge>
                      )}
                    </div>
                    <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                  </div>
                ))}
                {currentBuyerContent && (
                  <div className="p-4 bg-muted rounded-lg">
                    <p className="text-sm whitespace-pre-wrap">{currentBuyerContent}</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {outcome && (
        <div className="flex flex-col items-center gap-4 py-8">
          {getOutcomeBadge()}
          <p className="text-muted-foreground">
            Completed in {rounds} round{rounds !== 1 ? 's' : ''}
          </p>
          {isNegotiating && (
            <Button variant="outline" onClick={stopNegotiation}>
              Stop Negotiation
            </Button>
          )}
        </div>
      )}
    </div>
  );
}

