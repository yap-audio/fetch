import { notFound } from 'next/navigation';
import Image from 'next/image';
import Link from 'next/link';
import { supabase } from '@/lib/supabase';
import { Intent } from '@/lib/database.types';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ArrowLeft } from 'lucide-react';
import { NegotiationStream } from '@/components/negotiation-stream';

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
      <main className="container mx-auto px-4 py-8">
        <div className="max-w-5xl mx-auto space-y-8">
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

          {/* Negotiation Section */}
          <div>
            <h2 className="text-xl font-bold mb-4">Negotiation</h2>
            <NegotiationStream intentId={intent.uuid} />
          </div>
        </div>
      </main>
    </div>
  );
}

