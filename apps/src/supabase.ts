import { createClient } from '@supabase/supabase-js';

// Vite の環境変数（VITE_ プレフィックス必須）
const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL as string;
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY as string;

if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
  console.warn('[supabase] 環境変数が未設定です。.env.local を確認してください。');
}

export const supabase = createClient(
  SUPABASE_URL ?? 'https://placeholder.supabase.co',
  SUPABASE_ANON_KEY ?? 'placeholder'
);

// =============================================
// 型定義
// =============================================
export interface UserProfile {
  id: string;
  email: string;
  display_name: string | null;
  prefecture: string | null;
  avatar_url: string | null;
}

export interface PrefectureCache {
  prefecture_id: string;
  prefecture_name: string;
  lat: number;
  lon: number;
  ndvi: number | null;
  temp_celsius: number | null;
  vis_url: string | null;
  radar_url: string | null;
  ai_advice: string | null;
  satellite_date: string | null;
  updated_at: string;
}

// =============================================
// ヘルパー関数
// =============================================

/** Supabase Auth: 現在のセッションを取得 */
export async function getSession() {
  const { data } = await supabase.auth.getSession();
  return data.session;
}

/** Supabase Auth: ユーザープロフィールを取得 */
export async function getUserProfile(userId: string): Promise<UserProfile | null> {
  const { data, error } = await supabase
    .from('users')
    .select('*')
    .eq('auth_id', userId)
    .single();
  if (error) return null;
  return data as UserProfile;
}

/** prefecture_cache から全データ取得（フロントの初期データソース） */
export async function fetchAllPrefectures(): Promise<PrefectureCache[]> {
  const { data, error } = await supabase
    .from('prefecture_cache')
    .select('*')
    .order('updated_at', { ascending: false });
  if (error) {
    console.error('[supabase] prefecture_cache fetch error:', error.message);
    return [];
  }
  return data as PrefectureCache[];
}

/** 写真をSupabase Storageにアップロードし公開URLを返す */
export async function uploadFarmPhoto(file: File, userId: string): Promise<string | null> {
  const ext = file.name.split('.').pop() ?? 'jpg';
  const path = `${userId}/${Date.now()}.${ext}`;
  const { error } = await supabase.storage
    .from('farm-photos')
    .upload(path, file, { upsert: false });
  if (error) {
    console.error('[supabase] upload error:', error.message);
    return null;
  }
  const { data } = supabase.storage.from('farm-photos').getPublicUrl(path);
  return data.publicUrl;
}
