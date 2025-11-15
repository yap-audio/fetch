import Image from 'next/image';
import Link from 'next/link';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Intent } from '@/lib/database.types';

interface IntentCardProps {
  intent: Intent;
}

export function IntentCard({ intent }: IntentCardProps) {
  const truncateDescription = (text: string, maxLength: number = 150) => {
    if (text.length <= maxLength) return text;
    return text.slice(0, maxLength).trim() + '...';
  };

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
    <Card className="overflow-hidden">
      <CardContent className="p-0">
        <div className="relative">
          {imageUrl ? (
            <div className="relative w-full aspect-video">
              <Image
                src={imageUrl}
                alt={intent.description}
                fill
                className="object-cover"
                sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
              />
            </div>
          ) : (
            <div className="w-full aspect-video bg-muted flex items-center justify-center">
              <span className="text-muted-foreground">No image</span>
            </div>
          )}
          
          {/* Status Badge - Bottom Right */}
          <div className="absolute bottom-3 right-3">
            <Badge variant={getStatusVariant(intent.status)} className="capitalize">
              {intent.status}
            </Badge>
          </div>
        </div>

        <div className="p-6 space-y-4">
          {/* Description */}
          <p className="text-sm text-muted-foreground">
            {truncateDescription(intent.description)}
          </p>

          {/* Budget */}
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-muted-foreground">Budget</span>
            <span className="text-lg font-semibold">
              ${Number(intent.max_amount_usd).toFixed(2)}
            </span>
          </div>

          {/* Fulfill Button */}
          <Link href={`/intent/${intent.uuid}`}>
            <Button className="w-full" size="lg">
              Fulfill
            </Button>
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}

