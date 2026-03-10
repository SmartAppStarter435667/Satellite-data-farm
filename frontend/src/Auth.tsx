import React, { useState, useEffect } from 'react';
import { supabase } from './supabase';
import type { Session } from '@supabase/supabase-js';

interface AuthProps {
  onLogin: (session: Session) => void;
}

/**
 * シンプルなサインアップ/ログインUI
 * Supabase Auth（メール+パスワード）を使用
 */
const Auth: React.FC<AuthProps> = ({ onLogin }) => {
  const [mode, setMode] = useState<'login' | 'signup'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'error' | 'success'; text: string } | null>(null);

  // 既存セッションチェック
  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      if (data.session) onLogin(data.session);
    });
    const { data: listener } = supabase.auth.onAuthStateChange((_event, session) => {
      if (session) onLogin(session);
    });
    return () => listener.subscription.unsubscribe();
  }, [onLogin]);

  const handleSubmit = async () => {
    setLoading(true);
    setMessage(null);
    try {
      if (mode === 'signup') {
        const { data, error } = await supabase.auth.signUp({
          email,
          password,
          options: { data: { display_name: displayName } },
        });
        if (error) throw error;
        if (data.user && !data.session) {
          setMessage({ type: 'success', text: '確認メールを送信しました。メールのリンクをクリックしてください。' });
        }
      } else {
        const { error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) throw error;
      }
    } catch (e: any) {
      setMessage({ type: 'error', text: e.message ?? 'エラーが発生しました' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center p-4">
      <div className="w-full max-w-sm bg-gray-900 rounded-3xl border border-gray-800 overflow-hidden">
        {/* ヘッダー */}
        <div className="bg-gradient-to-r from-green-900/40 to-blue-900/40 p-6 text-center">
          <div className="text-4xl mb-2">🛰️</div>
          <h1 className="text-xl font-black text-white">
            <span className="text-green-400">SATELLITE</span>
            <span className="text-gray-300 font-light"> PRO</span>
          </h1>
          <p className="text-xs text-gray-400 mt-1">次世代農地監視SaaS</p>
        </div>

        <div className="p-6">
          {/* タブ切替 */}
          <div className="flex bg-gray-800 rounded-xl p-1 mb-5">
            {(['login', 'signup'] as const).map(m => (
              <button key={m} onClick={() => setMode(m)}
                className={`flex-1 py-2 rounded-lg text-xs font-bold transition-all ${
                  mode === m ? 'bg-green-600 text-white' : 'text-gray-400 hover:text-white'
                }`}>
                {m === 'login' ? 'ログイン' : '新規登録'}
              </button>
            ))}
          </div>

          {/* フォーム */}
          <div className="space-y-3">
            {mode === 'signup' && (
              <div>
                <label className="text-[10px] text-gray-500 font-bold uppercase block mb-1">表示名（農家名）</label>
                <input
                  value={displayName}
                  onChange={e => setDisplayName(e.target.value)}
                  placeholder="例: 田中農園"
                  className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-sm text-white placeholder-gray-600 focus:border-green-600 focus:outline-none"
                />
              </div>
            )}
            <div>
              <label className="text-[10px] text-gray-500 font-bold uppercase block mb-1">メールアドレス</label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="farmer@example.com"
                className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-sm text-white placeholder-gray-600 focus:border-green-600 focus:outline-none"
              />
            </div>
            <div>
              <label className="text-[10px] text-gray-500 font-bold uppercase block mb-1">パスワード</label>
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="8文字以上"
                className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-sm text-white placeholder-gray-600 focus:border-green-600 focus:outline-none"
              />
            </div>
          </div>

          {/* メッセージ */}
          {message && (
            <div className={`mt-4 p-3 rounded-xl text-xs ${
              message.type === 'error' ? 'bg-red-900/30 border border-red-800 text-red-300' : 'bg-green-900/30 border border-green-800 text-green-300'
            }`}>
              {message.text}
            </div>
          )}

          {/* 送信ボタン */}
          <button
            onClick={handleSubmit}
            disabled={loading || !email || !password}
            className="w-full mt-5 bg-green-600 hover:bg-green-500 disabled:bg-gray-700 disabled:text-gray-500 text-white font-bold py-3 rounded-xl text-sm transition-all"
          >
            {loading ? '処理中...' : mode === 'login' ? 'ログイン' : '新規登録'}
          </button>

          {/* ゲスト利用 */}
          <p className="text-center text-[10px] text-gray-600 mt-3">
            ※ ゲストとして閲覧のみ可能です。コメント投稿には登録が必要です。
          </p>
        </div>
      </div>
    </div>
  );
};

export default Auth;
