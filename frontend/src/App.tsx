import React from 'react';
import data from './data.json';

const App = () => {
  return (
    <div className="min-h-screen bg-[#f5f5f7] text-[#1d1d1f] font-sans selection:bg-blue-200">
      
      {/* すりガラス風のナビゲーションバー */}
      <nav className="sticky top-0 z-50 bg-white/70 backdrop-blur-lg border-b border-black/5">
        <div className="max-w-[1200px] mx-auto px-6 py-4 flex items-center justify-between">
          <span className="text-xl font-semibold tracking-tight">SatMonitor <span className="text-blue-500">Pro</span></span>
          <div className="text-sm font-medium text-[#86868b] hidden sm:block">Earth Observation Data</div>
        </div>
      </nav>

      {/* ヒーローセクション（大きな見出し） */}
      <header className="text-center pt-24 pb-16 px-4">
        <h1 className="text-4xl md:text-6xl font-semibold tracking-tighter mb-5 text-[#1d1d1f]">
          日本の「今」を、宇宙から。
        </h1>
        <p className="text-lg md:text-xl text-[#86868b] font-medium tracking-tight max-w-2xl mx-auto leading-relaxed">
          最先端のSentinel-2衛星データとGemini AIが、<br className="hidden md:block" />
          全国の環境変化や農作物の状況をリアルタイムで分析します。
        </p>
      </header>

      {/* データカードのグリッド */}
      <main className="max-w-[1200px] mx-auto px-6 pb-32 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        {data.map((p: any) => (
          <div key={p.id} className="bg-white rounded-[28px] overflow-hidden shadow-[0_8px_30px_rgb(0,0,0,0.04)] transition-all duration-300 hover:shadow-[0_8px_30px_rgb(0,0,0,0.08)] hover:-translate-y-1 flex flex-col">
            
            {/* 画像セクション */}
            <div className="relative aspect-[4/3] bg-gray-100 overflow-hidden">
              <img src={p.img} className="w-full h-full object-cover" alt={p.name} />
              <div className="absolute bottom-4 right-4 bg-white/90 backdrop-blur-md px-3 py-1.5 rounded-full text-xs font-semibold text-[#1d1d1f] shadow-sm">
                {p.date}
              </div>
            </div>
            
            {/* コンテンツセクション */}
            <div className="p-8 flex-grow flex flex-col">
              <h2 className="text-3xl font-semibold tracking-tight mb-8">{p.name}</h2>
              
              {/* 4つの指標（シンプルで洗練された表示） */}
              <div className="grid grid-cols-2 gap-y-6 gap-x-4 mb-8">
                <StatCard label="植生指数 (NDVI)" val={p.ndvi} color="text-green-600" />
                <StatCard label="水指数 (NDWI)" val={p.ndwi} color="text-blue-600" />
                <StatCard label="地表温度" val={`${p.temp}℃`} color="text-orange-500" />
                <StatCard label="雲量" val={`${p.cloud}%`} color="text-[#86868b]" />
              </div>

              {/* AI分析セクション */}
              <div className="mt-auto bg-[#f5f5f7] p-5 rounded-2xl">
                <div className="flex items-center gap-2 mb-2">
                  <svg className="w-4 h-4 text-blue-500" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z" />
                  </svg>
                  <span className="text-xs font-bold text-[#1d1d1f] uppercase tracking-wider">AI Insight</span>
                </div>
                <p className="text-sm text-[#1d1d1f] leading-relaxed font-medium">
                  {p.ai}
                </p>
              </div>

            </div>
          </div>
        ))}
      </main>
    </div>
  );
};

// 小さな指標カードコンポーネント
const StatCard = ({ label, val, color }: any) => (
  <div className="flex flex-col">
    <span className="text-[11px] font-bold text-[#86868b] uppercase tracking-wider mb-1">{label}</span>
    <span className={`text-2xl font-semibold tracking-tight ${color}`}>{val}</span>
  </div>
);

export default App;
