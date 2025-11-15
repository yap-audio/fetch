'use client';

import { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

interface NegotiationStreamProps {
  intentId: string;
  onStart?: () => void;
  onComplete?: (outcome: string) => void;
  showInSidebar?: boolean;
}

interface Message {
  role: 'seller' | 'buyer';
  content: string;
  decision?: string;
  round: number;
  timestamp: number;
}

interface SystemMessage {
  type: 'system';
  content: string;
  timestamp: number;
}

export function NegotiationStream({ intentId, onStart, onComplete, showInSidebar = false }: NegotiationStreamProps) {
  const [isNegotiating, setIsNegotiating] = useState(false);
  const [messages, setMessages] = useState<(Message | SystemMessage)[]>([]);
  const [thinking, setThinking] = useState<'seller' | 'buyer' | null>(null);
  const [outcome, setOutcome] = useState<string | null>(null);
  const [rounds, setRounds] = useState(0);
  const [error, setError] = useState<string | null>(null);
  
  const chatScrollRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    chatScrollRef.current?.scrollTo({
      top: chatScrollRef.current.scrollHeight,
      behavior: 'smooth'
    });
  }, [messages]);

  const startNegotiation = () => {
    setIsNegotiating(true);
    setMessages([{
      type: 'system',
      content: 'Starting negotiation...',
      timestamp: Date.now()
    }]);
    setOutcome(null);
    setError(null);
    setThinking(null);
    onStart?.();

    const eventSource = new EventSource(`/api/negotiate/${intentId}`);
    eventSourceRef.current = eventSource;

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.type === 'start') {
          setRounds(data.maxRounds);
        } else if (data.type === 'seller' || data.type === 'buyer') {
          if (data.phase === 'thinking') {
            setThinking(data.type);
            // Add a new message placeholder only if the last message isn't from this agent in this round
            setMessages(prev => {
              const last = prev[prev.length - 1];
              if (last && 'role' in last && last.role === data.type && last.round === data.round) {
                // Already have a message for this agent/round, don't add another
                return prev;
              }
              return [...prev, {
                role: data.type,
                content: '',
                round: data.round,
                timestamp: Date.now()
              }];
            });
          } else if (data.phase === 'response') {
            setThinking(null);
            // Update the last message with new content
            setMessages(prev => {
              const last = prev[prev.length - 1];
              if (last && 'role' in last && last.role === data.type) {
                return [
                  ...prev.slice(0, -1),
                  { ...last, content: last.content + data.content }
                ];
              }
              return prev;
            });
          } else if (data.phase === 'decision') {
            setThinking(null);
            // Update the last message with the decision
            setMessages(prev => {
              const last = prev[prev.length - 1];
              if (last && 'role' in last && last.role === data.type) {
                const updated = [
                  ...prev.slice(0, -1),
                  { ...last, decision: data.decision }
                ];
                
                // Add decision as system message if not 'continue'
                if (data.decision !== 'continue') {
                  updated.push({
                    type: 'system',
                    content: `${data.type === 'seller' ? 'Seller' : 'Buyer'} decided to ${data.decision}`,
                    timestamp: Date.now()
                  });
                }
                
                // Add payment information if present (buyer only)
                if (data.payment_result) {
                  const payment = data.payment_result;
                  
                  if (payment.seller_payment) {
                    updated.push({
                      type: 'system',
                      content: `💰 Payment sent to seller: $${payment.amount_paid?.toFixed(2) || 'N/A'} USDC`,
                      timestamp: Date.now()
                    });
                  }
                  
                  if (payment.user_refund) {
                    updated.push({
                      type: 'system',
                      content: `💵 Refund sent to user: $${payment.amount_refunded?.toFixed(2) || 'N/A'} USDC`,
                      timestamp: Date.now()
                    });
                  }
                  
                  if (payment.error) {
                    updated.push({
                      type: 'system',
                      content: `⚠️ Payment error: ${payment.error}`,
                      timestamp: Date.now()
                    });
                  }
                }
                
                return updated;
              }
              return prev;
            });
          }
        } else if (data.type === 'complete') {
          setOutcome(data.outcome);
          setRounds(data.rounds);
          setIsNegotiating(false);
          
          // Add completion message
          const outcomeText = data.outcome === 'accepted' 
            ? `✅ Deal reached! Completed in ${data.rounds} round${data.rounds !== 1 ? 's' : ''}`
            : data.outcome === 'rejected'
            ? `❌ No deal. Negotiation ended in ${data.rounds} round${data.rounds !== 1 ? 's' : ''}`
            : `⏱️ Max rounds reached (${data.rounds})`;
          
          setMessages(prev => [...prev, {
            type: 'system',
            content: outcomeText,
            timestamp: Date.now()
          }]);
          
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

  // Auto-start if in sidebar mode
  useEffect(() => {
    if (showInSidebar && !isNegotiating && messages.length === 0) {
      startNegotiation();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [showInSidebar]);

  return (
    <div className="space-y-4">
      {!showInSidebar && !isNegotiating && messages.length === 0 && (
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

      {/* Chat-style conversation */}
      {(showInSidebar || messages.length > 0) && (
        <Card className="h-full">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Negotiation</span>
              {thinking && (
                <Badge variant="outline">
                  {thinking === 'seller' ? 'You' : 'Buyer'} thinking...
                </Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div
              ref={chatScrollRef}
              className={`space-y-4 overflow-y-auto pr-4 ${showInSidebar ? 'h-[calc(100vh-250px)]' : 'max-h-[600px]'}`}
            >
              {messages.map((msg, idx) => {
                if ('type' in msg && msg.type === 'system') {
                  return (
                    <div key={idx} className="flex justify-center">
                      <Badge variant="secondary" className="text-xs">
                        {msg.content}
                      </Badge>
                    </div>
                  );
                }
                
                const message = msg as Message;
                const isSeller = message.role === 'seller';
                
                return (
                  <div
                    key={idx}
                    className={`flex ${isSeller ? 'justify-end' : 'justify-start'}`}
                  >
                    <div className={`max-w-[80%] ${isSeller ? 'items-end' : 'items-start'} flex flex-col gap-1`}>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-medium text-muted-foreground">
                          {isSeller ? 'You (Seller)' : 'Buyer'}
                        </span>
                        {message.decision && message.decision !== 'continue' && (
                          <Badge variant="outline" className="text-xs">
                            {message.decision}
                          </Badge>
                        )}
                      </div>
                      <div
                        className={`p-3 rounded-lg ${
                          isSeller
                            ? 'bg-primary text-primary-foreground'
                            : 'bg-muted'
                        }`}
                      >
                        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {isNegotiating && (
        <div className="flex justify-center">
          <Button variant="outline" onClick={stopNegotiation}>
            Stop Negotiation
          </Button>
        </div>
      )}
    </div>
  );
}

