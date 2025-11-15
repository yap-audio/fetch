import { notFound } from 'next/navigation';
import Link from 'next/link';
import { supabase } from '@/lib/supabase';
import { Intent } from '@/lib/database.types';
import { Button } from '@/components/ui/button';
import { ArrowLeft } from 'lucide-react';
import { IntentDetailClient } from '@/components/intent-detail-client';

export const dynamic = 'force-dynamic';

interface IntentPageProps {
  params: Promise<{ id: string }>;
}

export default async function IntentPage({ params }: IntentPageProps) {
  const { id } = await params;
  
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
          <Link href="/">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Dashboard
            </Button>
          </Link>
        </div>
      </header>

      {/* Main Content */}
      <IntentDetailClient intent={intent} />
    </div>
  );
}

