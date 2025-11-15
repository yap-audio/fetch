import { supabase } from '@/lib/supabase';
import { IntentCard } from '@/components/intent-card';
import { UserProfile } from '@/components/user-profile';
import { Intent } from '@/lib/database.types';

export const dynamic = 'force-dynamic';

export default async function Home() {
  const walletAddress = process.env.NEXT_PUBLIC_USER_WALLET_ADDRESS || '';

  // Fetch intents from Supabase
  const { data: intents, error } = await supabase
    .from('intents')
    .select('*')
    .order('created_at', { ascending: false })
    .returns<Intent[]>();

  if (error) {
    console.error('Error fetching intents:', error);
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b">
        <div className="container mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold">Hi, TJ</h1>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="flex flex-col lg:flex-row gap-8">
          {/* Intents Grid - Main Content */}
          <div className="flex-1">
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
          </div>

          {/* User Profile Sidebar */}
          <aside className="w-full lg:w-80">
            <UserProfile walletAddress={walletAddress} />
          </aside>
        </div>
      </main>
    </div>
  );
}
