'use client';

import { useState, useEffect } from 'react';
import Image from 'next/image';
import { Intent } from '@/lib/database.types';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { NegotiationStream } from '@/components/negotiation-stream';
import { supabase } from '@/lib/supabase';

interface IntentDetailClientProps {
  initialIntent: Intent;
}

export function IntentDetailClient({ initialIntent }: IntentDetailClientProps) {
  const [intent, setIntent] = useState<Intent>(initialIntent);
  const [showNegotiation, setShowNegotiation] = useState(false);

  useEffect(() => {
    // Subscribe to realtime updates for this specific intent
    const channel = supabase
      .channel(`intent-${intent.uuid}`)
      .on(
        'postgres_changes',
        {
          event: 'UPDATE',
          schema: 'public',
          table: 'intents',
          filter: `uuid=eq.${intent.uuid}`
        },
        (payload) => {
          setIntent(payload.new as Intent);
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [intent.uuid]);

  const getImageUrl = (imageUuid: string | null) => {
    if (!imageUuid) return null;
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
    return `${supabaseUrl}/storage/v1/object/public/intent-images/${imageUuid}.png`;
  };

  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'live':
        return 'default';
      case 'completed':
      case 'fulfilled':
        return 'secondary';
      case 'cancelled':
        return 'destructive';
      default:
        return 'default';
    }
  };

  const imageUrl = getImageUrl(intent.image_uuid);

  return (
    <main className="container mx-auto px-4 py-8">
      <div className={`flex flex-col lg:flex-row gap-8 ${!showNegotiation ? 'justify-center' : ''}`}>
        {/* Intent Details - Main Content */}
        <div className={showNegotiation ? 'lg:w-1/3' : 'w-full max-w-5xl'}>
          <div className="space-y-8">
            {/* Intent Details Card */}
            <Card>
              <CardContent className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Image */}
                  <div className="relative">
                    {imageUrl ? (
                      <div className="relative w-full aspect-video rounded-lg overflow-hidden">
                        <Image
                          src={imageUrl}
                          alt={intent.description}
                          fill
                          className="object-cover"
                          sizes="(max-width: 768px) 100vw, 50vw"
                        />
                      </div>
                    ) : (
                      <div className="w-full aspect-video bg-muted rounded-lg flex items-center justify-center">
                        <span className="text-muted-foreground">No image</span>
                      </div>
                    )}
                  </div>

                  {/* Details */}
                  <div className="space-y-4">
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <h1 className="text-2xl font-bold">Intent Details</h1>
                        <Badge variant={getStatusVariant(intent.status)} className="capitalize">
                          {intent.status}
                        </Badge>
                      </div>
                    </div>

                    <div>
                      <h3 className="text-sm font-medium text-muted-foreground mb-1">
                        Description
                      </h3>
                      <p className="text-sm">{intent.description}</p>
                    </div>

                    <div>
                      <h3 className="text-sm font-medium text-muted-foreground mb-1">
                        Budget
                      </h3>
                      <p className="text-2xl font-bold">
                        ${Number(intent.max_amount_usd).toFixed(2)}
                      </p>
                    </div>

                    {intent.created_at && (
                      <div>
                        <h3 className="text-sm font-medium text-muted-foreground mb-1">
                          Created
                        </h3>
                        <p className="text-sm">
                          {new Date(intent.created_at).toLocaleDateString()}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Negotiation Button */}
            {!showNegotiation && (
              <div className="flex justify-center">
                <Button
                  size="lg"
                  onClick={() => setShowNegotiation(true)}
                >
                  Negotiate for me
                </Button>
              </div>
            )}
          </div>
        </div>

        {/* Negotiation Sidebar - Appears when negotiation starts */}
        {showNegotiation && (
          <aside className="w-full lg:w-2/3">
            <div className="lg:sticky lg:top-6">
              <NegotiationStream 
                intentId={intent.uuid}
                showInSidebar={true}
                onStart={() => setShowNegotiation(true)}
              />
            </div>
          </aside>
        )}
      </div>
    </main>
  );
}

