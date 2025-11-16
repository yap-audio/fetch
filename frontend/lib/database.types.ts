export type Database = {
  public: {
    Tables: {
      intents: {
        Row: {
          uuid: string;
          user_id: string;
          taker_id: string | null;
          max_amount_usd: number;
          description: string;
          status: 'live' | 'completed' | 'cancelled' | 'fulfilled';
          created_at: string | null;
          updated_at: string | null;
          image_uuid: string | null;
          tx_buyer_to_seller_id: string | null;
          tx_buyer_to_user_id: string | null;
        };
        Insert: {
          uuid?: string;
          user_id: string;
          taker_id?: string | null;
          max_amount_usd: number;
          description: string;
          status?: 'live' | 'completed' | 'cancelled' | 'fulfilled';
          created_at?: string | null;
          updated_at?: string | null;
          image_uuid?: string | null;
          tx_buyer_to_seller_id?: string | null;
          tx_buyer_to_user_id?: string | null;
        };
        Update: {
          uuid?: string;
          user_id?: string;
          taker_id?: string | null;
          max_amount_usd?: number;
          description?: string;
          status?: 'live' | 'completed' | 'cancelled' | 'fulfilled';
          created_at?: string | null;
          updated_at?: string | null;
          image_uuid?: string | null;
          tx_buyer_to_seller_id?: string | null;
          tx_buyer_to_user_id?: string | null;
        };
      };
      balances: {
        Row: {
          id: string;
          balance_usdc: number;
        };
        Insert: {
          id: string;
          balance_usdc: number;
        };
        Update: {
          id?: string;
          balance_usdc?: number;
        };
      };
    };
  };
};

export type Intent = Database['public']['Tables']['intents']['Row'];

