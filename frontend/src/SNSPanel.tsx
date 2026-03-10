import React, { useState, useEffect, useCallback } from 'react';
import { fetchComments, postComment, likeComment, deleteComment, type Comment } from './api';
import { supabase } from './supabase';
import type { Session } from '@supabase/supabase-js';

interface SNSPanelProps {
  farmId: string;
  farmName: string;
  session: Session | null;
}

/**
 * 農地ごとのSNSコメントパネル
 * - コメント一覧取得（MongoDB API経由）
 * - コメント投稿・いいね・削除
 * - ゲストは閲覧のみ、投稿はログイン必須
 */
const SNSPanel: React.FC<SNSPanelProps> = ({ farmId, farmName, session }) => {
  const [comments, setComments] = useState<Comment[]>([]);
  const [text, setText] = useState('');
  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState('');
  const [loading, setLoading] = useState(true);
  const [posting, setPosting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const PRESET_TAGS = ['水稲', '害虫', '施肥', '灌水', '気象', '収穫', '病気', 'その他'];

  // コメント読み込み
  const loadComments = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchComments(farmId);
      setComments(data);
    } catch (e: any) {
      setError('コメントの取得に失敗しました。バックエンドAPIが起動しているか確認してください。');
    } finally {
      setLoading(false);
    }
  }, [farmId]);

  useEffect(() => {
    loadComments();
  }, [loadComments]);

  // コメント投稿
  const handlePost = async () => {
    if (!session || !text.trim()) return;
    setPosting(true);
    setError(null);
    try {
      const userId = session.user.id;
      const userName = session.user.user_metadata?.display_name ?? session.user.email ?? '農家';
      const newComment = await postComment({
        farmId,
        userId,
        userName,
        text: text.trim(),
        tags,
      });
      setComments(prev => [newComment, ...prev]);
      setText('');
      setTags([]);
    } catch (e: any) {
      setError('投稿に失敗しました: ' + e.message);
    } finally {
      setPosting(false);
    }
  };

  // いいね
  const handleLike = async (commentId: string) => {
    try {
      const { likes } = await likeComment(commentId);
      setComments(prev => prev.map(c => c._id === commentId ? { ...c, likes } : c));
    } catch {}
  };

  // 削除
  const handleDelete = async (commentId: string) => {
    if (!session) return;
    if (!confirm('このコメントを削除しますか？')) return;
    try {
      await deleteComment(commentId, session.user.id);
      setComments(prev => prev.filter(c => c._id !== commentId));
    } catch {
      setError('削除に失敗しました（投稿者本人のみ削除可能）');
    }
  };

  // タグ追加
  const addTag = (tag: string) => {
    if (!tags.includes(tag) && tags.length < 5) {
      setTags(prev => [...prev, tag]);
    }
  };

  return (
    <div className="space-y-4">
      {/* ヘッダー */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold flex items-center gap-2">
          💬 {farmName}のコミュニティ
          <span className="bg-gray-700 text-[10px] px-2 py-0.5 rounded-full">
            {loading ? '...' : `${comments.length}件`}
          </span>
        </h3>
        <button onClick={loadComments} className="text-[10px] text-gray-500 hover:text-green-400">
          ↻ 更新
        </button>
      </div>

      {/* 投稿フォーム（ログイン時のみ） */}
      {session ? (
        <div className="bg-gray-800/60 rounded-xl p-4 border border-gray-700">
          <p className="text-[10px] text-green-400 font-bold mb-2">
            {session.user.user_metadata?.display_name ?? session.user.email} として投稿
          </p>
          
          {/* テキスト入力 */}
          <textarea
            value={text}
            onChange={e => setText(e.target.value)}
            placeholder="農地の様子・気になること・アドバイスなど..."
            maxLength={500}
            rows={3}
            className="w-full bg-gray-700 rounded-lg px-3 py-2 text-xs text-white placeholder-gray-500 border border-gray-600 focus:border-green-600 focus:outline-none resize-none mb-2"
          />
          
          {/* タグ選択 */}
          <div className="flex flex-wrap gap-1 mb-3">
            {PRESET_TAGS.map(tag => (
              <button key={tag}
                onClick={() => addTag(tag)}
                className={`px-2 py-0.5 rounded-full text-[10px] font-bold transition-all ${
                  tags.includes(tag)
                    ? 'bg-green-600 text-white'
                    : 'bg-gray-700 text-gray-400 hover:bg-gray-600'
                }`}>
                #{tag}
              </button>
            ))}
          </div>
          
          {/* 選択中タグ表示 */}
          {tags.length > 0 && (
            <div className="flex gap-1 mb-2">
              {tags.map(tag => (
                <span key={tag}
                  onClick={() => setTags(prev => prev.filter(t => t !== tag))}
                  className="bg-green-900/50 text-green-400 text-[10px] px-2 py-0.5 rounded-full cursor-pointer hover:line-through">
                  #{tag}
                </span>
              ))}
            </div>
          )}
          
          <div className="flex justify-between items-center">
            <span className="text-[10px] text-gray-600">{text.length}/500</span>
            <button
              onClick={handlePost}
              disabled={posting || !text.trim()}
              className="bg-green-600 hover:bg-green-500 disabled:bg-gray-700 disabled:text-gray-500 text-white text-xs font-bold px-4 py-2 rounded-lg transition-all"
            >
              {posting ? '投稿中...' : '投稿する'}
            </button>
          </div>
        </div>
      ) : (
        <div className="bg-gray-800/40 rounded-xl p-3 border border-gray-700 text-center">
          <p className="text-xs text-gray-400">コメントを投稿するにはログインが必要です</p>
        </div>
      )}

      {/* エラー表示 */}
      {error && (
        <div className="bg-red-900/20 border border-red-800 rounded-xl p-3 text-xs text-red-300">
          ⚠️ {error}
        </div>
      )}

      {/* コメント一覧 */}
      {loading ? (
        <div className="text-center py-8 text-gray-500 text-xs">読み込み中...</div>
      ) : comments.length === 0 ? (
        <div className="text-center py-8 text-gray-600 text-xs">
          まだコメントがありません。最初の投稿をしてみましょう！
        </div>
      ) : (
        <div className="space-y-2">
          {comments.map(comment => (
            <div key={comment._id} className="bg-gray-800 rounded-xl p-4 border border-gray-700">
              <div className="flex justify-between items-start mb-2">
                <div>
                  <span className="text-xs font-bold text-green-400">{comment.user_name}</span>
                  <span className="text-[10px] text-gray-600 ml-2">
                    {new Date(comment.created_at).toLocaleDateString('ja-JP', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  {/* いいね */}
                  <button
                    onClick={() => handleLike(comment._id)}
                    className="flex items-center gap-1 text-[10px] text-gray-500 hover:text-green-400 transition-colors"
                  >
                    👍 {comment.likes}
                  </button>
                  {/* 削除（本人のみ） */}
                  {session?.user.id === comment.user_id && (
                    <button
                      onClick={() => handleDelete(comment._id)}
                      className="text-[10px] text-gray-600 hover:text-red-400 transition-colors"
                    >
                      削除
                    </button>
                  )}
                </div>
              </div>
              
              <p className="text-xs text-gray-300 leading-relaxed mb-2">{comment.text}</p>
              
              {/* タグ */}
              {comment.tags.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {comment.tags.map(tag => (
                    <span key={tag} className="text-[9px] bg-gray-700 text-gray-400 px-2 py-0.5 rounded-full">
                      #{tag}
                    </span>
                  ))}
                </div>
              )}
              
              {/* 添付写真 */}
              {comment.photo_url && (
                <img src={comment.photo_url} alt="添付写真"
                  className="mt-2 w-full max-h-40 object-cover rounded-lg" />
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default SNSPanel;
