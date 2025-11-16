'use client';

import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabase';
import { Intent } from '@/lib/database.types';
import { IntentCard } from '@/components/intent-card';

interface IntentsListRealtimeProps {
  initialIntents: Intent[];
}

export function IntentsListRealtime({ initialIntents }: IntentsListRealtimeProps) {
  const [intents, setIntents] = useState<Intent[]>(initialIntents);

  useEffect(() => {
    // Subscribe to realtime changes
    const channel = supabase
      .channel('intents-changes')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'intents'
        },
        (payload) => {
          if (payload.eventType === 'INSERT') {
            setIntents((current) => [payload.new as Intent, ...current]);
          } else if (payload.eventType === 'UPDATE') {
            setIntents((current) =>
              current.map((intent) =>
                intent.uuid === (payload.new as Intent).uuid
                  ? (payload.new as Intent)
                  : intent
              )
            );
          } else if (payload.eventType === 'DELETE') {
            setIntents((current) =>
              current.filter((intent) => intent.uuid !== (payload.old as Intent).uuid)
            );
          }
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, []);

  return (
    <>
      {intents && intents.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {intents.map((intent) => (
            <IntentCard key={intent.uuid} intent={intent} />
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <p className="text-muted-foreground">No intents found</p>
        </div>
      )}
    </>
  );
}

