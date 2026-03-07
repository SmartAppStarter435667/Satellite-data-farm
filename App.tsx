import React from 'react';
import data from './data.json'; // Pythonが作ったデータを読み込む

const App = () => {
  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 p-4 md:p-8">
      <header className="max-w-6xl mx-auto mb-12 text-center">
        <h1 className="text-4xl font-bold text-cyan-400 mb-2">JAPAN SATELLITE PORTAL</h1>
        <p className="text-slate-400">47都道府県 衛星データ・リアルタイム監視</p>
      </header>

      <main className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {data.map((pref) => (
          <div key={pref.id} className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden hover:border-cyan-500 transition-all shadow-xl">
            <img src={pref.img} alt={pref.name} className="w-full h-48 object-cover" />
            <div className="p-5">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold">{pref.name}</h2>
                <span className={`px-3 py-1 rounded-full text-xs font-bold ${pref.ndvi > 0.4 ? 'bg-green-900 text-green-300' : 'bg-yellow-900 text-yellow-300'}`}>
                  NDVI: {pref.ndvi}
                </span>
              </div>
              <p className="text-sm text-slate-400 leading-relaxed">
                衛星画像から算出された植生指数は{pref.ndvi}です。現在の環境状況を分析中...
              </p>
              <button className="mt-4 w-full py-2 bg-slate-700 hover:bg-cyan-600 rounded-lg text-sm font-medium transition-colors">
                詳細データを見る
              </button>
            </div>
          </div>
        ))}
      </main>
    </div>
  );
};

export default App;
