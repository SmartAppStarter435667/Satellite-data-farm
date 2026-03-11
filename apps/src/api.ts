/**
 * SATELLITE PRO - バックエンドAPIクライアント
 * Render.com上のFastAPIへのリクエストをまとめる
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

// =============================================
// 型定義
// =============================================
export interface NDVIData {
  ndvi: number;
  temp: number | null;
  vis_url: string;
  radar_url: string;
  date: string;
  ai: string;
  bbox: { west: number; east: number; south: number; north: number };
}

export interface PhotoAnalysisResult {
  success: boolean;
  lat?: number;
  lon?: number;
  matched_prefecture?: { id: string; name: string; lat: number; lon: number };
  distance_km?: number;
  error?: string;
}

export interface Comment {
  _id: string;
  farm_id: string;
  user_id: string;
  user_name: string;
  text: string;
  photo_url: string | null;
  likes: number;
  tags: string[];
  created_at: string;
}

// =============================================
// フェッチユーティリティ
// =============================================
async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`API ${path} failed (${res.status}): ${err}`);
  }
  return res.json() as Promise<T>;
}

// =============================================
// NDVI API
// =============================================
export async function fetchNDVI(prefId: string): Promise<NDVIData> {
  return apiFetch<NDVIData>(`/api/ndvi/${prefId}`);
}

export async function fetchBBoxNDVI(lat: number, lon: number, radiusM = 3000): Promise<NDVIData> {
  return apiFetch<NDVIData>(`/api/bbox?lat=${lat}&lon=${lon}&radius_m=${radiusM}`);
}

// =============================================
// 写真解析 API
// =============================================
export async function analyzePhoto(file: File): Promise<PhotoAnalysisResult> {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${API_BASE}/api/photo/analyze`, {
    method: 'POST',
    body: form,
  });
  if (!res.ok) throw new Error('Photo analysis failed');
  return res.json();
}

// =============================================
// SNS（コメント）API  ← MongoDB経由
// =============================================

/** 農地のコメント一覧取得 */
export async function fetchComments(farmId: string): Promise<Comment[]> {
  return apiFetch<Comment[]>(`/api/sns/comments?farm_id=${farmId}`);
}

/** コメント投稿 */
export async function postComment(params: {
  farmId: string;
  userId: string;
  userName: string;
  text: string;
  photoUrl?: string;
  tags?: string[];
}): Promise<Comment> {
  return apiFetch<Comment>('/api/sns/comments', {
    method: 'POST',
    body: JSON.stringify({
      farm_id: params.farmId,
      user_id: params.userId,
      user_name: params.userName,
      text: params.text,
      photo_url: params.photoUrl ?? null,
      tags: params.tags ?? [],
    }),
  });
}

/** コメントにいいね */
export async function likeComment(commentId: string): Promise<{ likes: number }> {
  return apiFetch<{ likes: number }>(`/api/sns/comments/${commentId}/like`, {
    method: 'POST',
  });
}

/** コメント削除 */
export async function deleteComment(commentId: string, userId: string): Promise<void> {
  await apiFetch<void>(`/api/sns/comments/${commentId}?user_id=${userId}`, {
    method: 'DELETE',
  });
}

// =============================================
// ヘルスチェック
// =============================================
export async function checkApiHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/`, { signal: AbortSignal.timeout(5000) });
    return res.ok;
  } catch {
    return false;
  }
}
