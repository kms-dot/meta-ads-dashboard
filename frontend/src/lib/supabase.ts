import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Missing Supabase environment variables');
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

// 타입 정의
export interface Ad {
  id: string;
  category: string;
  advertiser: string;
  ad_id: string | null;
  ad_text: string | null;
  thumbnail_url: string | null;
  video_url: string | null;
  media_type: string;
  platforms: string[];
  ad_library_url: string;
  days_live: number;
  start_date: string | null;
  impression_text: string | null;
  is_active: boolean;
  query: string | null;
  collected_at: string;
  last_checked: string;
  rank: number | null;
  crawl_date: string | null;
}

export interface AdStats {
  total_ads: number;
  unique_advertisers: number;
  avg_days_live: number;
  video_ads: number;
  image_ads: number;
}
