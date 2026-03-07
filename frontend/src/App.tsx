import React, { useState } from 'react';
import data from './data.json';

const App = () => {
  const [tab, setTab] = useState<'japan' | 'overseas'>('japan');

  return (
    <div className="min-h-screen bg-[#F5F5F7] text-[#1D1D1F] font-sans">
      {/* Navigation (Apple Style) */}
      <nav className="sticky top-0 z-50 bg-white/80 backdrop-blur-xl border-b border-black/5">
        <div className="max-w-5xl mx-auto px-6 h-14 flex items-center justify-between">
          <h1 className="text-xl font-bold tracking-tight">衛星お天気ポータル</h1>
          <div className="flex gap-6">
            <button onClick={() => setTab('japan')} className={`text-sm font-medium transition-colors ${tab === 'japan' ? 'text-blue-600' : 'text-gray-500 hover:text-black'}`}>日本国内</button>
            <button onClick={() => setTab('overseas')} className={`text-sm font-medium transition-colors ${tab === 'overseas' ? 'text-blue-600' : 'text-gray-500 hover:text-black'}`}>海外主要都市</button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <header className="max-w-5xl mx-auto px-6 pt-16 pb-8">
        <p className="text-blue-600 font-bold mb-2 uppercase tracking-widest text-xs">Real-time Satellite Insights</p>
        <h2 className="text-4xl md:text-5xl font-bold tracking-tight mb-4">
          {tab === 'japan' ? '日本の大地を見守る' : '世界の今を宇宙から俯瞰する'}
        </h2>
      </header>

      {/* Grid Layout */}
      <main className="max-w-5xl mx-auto px-6 pb-24 grid grid-cols-1 md:grid-cols-2 gap-6">
        {data[tab].map((item: any) => (
          <div key={item.id} className="bg-white rounded-3xl p-6 shadow-sm border border-black/5 flex flex-col gap-6">
            <div className="flex justify-between items-start">
              <div>
                <h3 className="text-2xl font-bold">{item.name}</h3>
                <p className="text-xs text-gray-400 font-mono mt-1">観測日: {item.date}</p>
              </div>
              <div className="bg-blue-50 text-blue-600 px-3 py-1 rounded-full text-xs font-bold">
                {item.temp}℃
              </div>
            </div>

            <div className="aspect-video rounded-2xl overflow-hidden bg-gray-100">
              <img src={item.img} className="w-full h-full object-cover" alt={item.name} />
            </div>

            {/* お天気ニュース風 AI要約 */}
            <div className="bg-[#F5F5F7] p-4 rounded-2xl border-l-4 border-blue-500">
              <p className="text-sm leading-relaxed font-medium">
                「{item.ai}」
              </p>
            </div>

            {/* 天気予報のような指標表示 */}
            <div className="grid grid-cols-3 gap-2">
              <WeatherIcon label="植物の元気" val={item.ndvi > 0.5 ? "満点" : "良好"} sub={`指数:${item.ndvi}`} />
              <WeatherIcon label="水資源" val={item.ndwi > 0 ? "豊富" : "乾燥"} sub={`指数:${item.ndwi}`} />
              <WeatherIcon label="観測精度" val={item.cloud < 20 ? "快晴" : "曇り"} sub={`雲:${item.cloud}%`} />
            </div>
          </div>
        ))}
      </main>
    </div>
  );
};

const WeatherIcon = ({ label, val, sub }: any) => (
  <div className="text-center p-2">
    <p className="text-[10px] text-gray-400 font-bold mb-1 uppercase tracking-tighter">{label}</p>
    <p className="text-sm font-bold">{val}</p>
    <p className="text-[9px] text-gray-400 font-mono">{sub}</p>
  </div>
);

export default App;
