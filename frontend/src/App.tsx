import React, { useState } from 'react';
import data from './data.json';

const App = () => {
  const [page, setPage] = useState<'japan' | 'overseas' | 'globe' | 'guide'>('japan');

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white font-sans overflow-x-hidden">
      {/* 以前のデザインをベースにしたロゴとナビ */}
      <nav className="fixed top-0 w-full z-50 bg-black/90 backdrop-blur-xl border-b border-white/5">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 border-2 border-cyan-500 rounded-full flex items-center justify-center animate-pulse">
              <div className="w-2 h-2 bg-cyan-500 rounded-full"></div>
            </div>
            <h1 className="text-2xl font-black tracking-[0.2em] text-white italic">SATELLITE <span className="text-cyan-500 not-italic font-light text-sm ml-1 tracking-widest">ANALYSIS PRO</span></h1>
          </div>
          <div className="flex gap-6 text-[10px] font-bold tracking-[0.2em] uppercase">
            <NavBtn active={page === 'japan'} label="Japan" onClick={() => setPage('japan')} />
            <NavBtn active={page === 'overseas'} label="World" onClick={() => setPage('overseas')} />
            <NavBtn active={page === 'globe'} label="3D Globe" onClick={() => setPage('globe')} />
            <NavBtn active={page === 'guide'} label="Guide" onClick={() => setPage('guide')} />
          </div>
        </div>
      </nav>

      <main className="pt-32 pb-20 px-6 max-w-7xl mx-auto">
        {page === 'globe' ? (
          <GlobeSection />
        ) : page === 'guide' ? (
          <GuideSection />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-10">
            {data[page === 'japan' ? 'japan' : 'overseas'].map((item: any) => (
              <div key={item.id} className="bg-zinc-900/50 rounded-[40px] border border-white/5 overflow-hidden backdrop-blur-sm hover:border-cyan-500/50 transition-all group shadow-2xl">
                <div className="relative aspect-square">
                  <img src={item.img} className="w-full h-full object-cover grayscale-[20%] group-hover:grayscale-0 transition-all duration-700" alt={item.name} />
                  <div className="absolute inset-0 bg-gradient-to-t from-zinc-900 via-transparent to-transparent"></div>
                  <div className="absolute bottom-6 left-6">
                    <p className="text-[10px] text-cyan-400 font-black tracking-widest uppercase mb-1">{item.sat}</p>
                    <h3 className="text-3xl font-bold">{item.name}</h3>
                  </div>
                </div>
                <div className="p-8 space-y-6">
                  <div className="flex justify-between border-b border-white/5 pb-4">
                    <div className="text-center">
                      <p className="text-[9px] text-zinc-500 font-bold uppercase mb-1">NDVI 生育指数</p>
                      <p className="text-xl font-mono text-emerald-400 font-bold">{item.ndvi}</p>
                    </div>
                    <div className="text-center border-l border-white/5 pl-6">
                      <p className="text-[9px] text-zinc-500 font-bold uppercase mb-1">LST 地表温度</p>
                      <p className="text-xl font-mono text-orange-400 font-bold">{item.temp}℃</p>
                    </div>
                  </div>
                  <div className="bg-black/40 p-5 rounded-3xl border border-white/5">
                    <p className="text-[10px] text-zinc-500 font-bold mb-2 uppercase">AI Analysis Report</p>
                    <p className="text-sm leading-relaxed text-zinc-300 font-medium">「{item.ai}」</p>
                    <p className="text-[9px] text-zinc-600 mt-4 font-mono uppercase">Observed: {item.date}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
};

const NavBtn = ({ active, label, onClick }: any) => (
  <button onClick={onClick} className={`transition-all ${active ? 'text-cyan-400 scale-110' : 'text-zinc-600 hover:text-white'}`}>
    {label}
  </button>
);

const GlobeSection = () => (
  <div className="flex flex-col items-center justify-center min-h-[60vh]">
    <div className="relative w-80 h-80 md:w-[500px] md:h-[500px]">
      {/* 実際にはここでreact-globe-glなどのライブラリを使用しますが、ここではビジュアルのみ表現 */}
      <div className="absolute inset-0 rounded-full bg-gradient-to-br from-cyan-500/20 to-blue-500/20 animate-pulse border border-cyan-500/30"></div>
      <div className="absolute inset-4 rounded-full border border-white/5 animate-spin-slow"></div>
      <div className="absolute inset-0 flex items-center justify-center text-center p-10">
        <p className="text-cyan-400 text-sm font-bold tracking-widest uppercase">3D Globe Mode<br /><span className="text-white text-xs lowercase opacity-50 font-normal">Scroll to rotate / Click to scan</span></p>
      </div>
    </div>
    <p className="mt-12 text-zinc-500 max-w-lg text-center text-sm leading-relaxed">
      マウスホイールで地球を自転させ、世界各地のLandsatアーカイブをシームレスにブラウズできます。特定のプロットをクリックすると、詳細な「スマート生育レポート」の生成を開始します。
    </p>
  </div>
);

const GuideSection = () => (
  <div className="max-w-4xl mx-auto space-y-16">
    <h2 className="text-5xl font-black text-center italic tracking-tighter">HOW IT WORKS</h2>
    <div className="grid md:grid-cols-2 gap-12">
      <div className="space-y-4">
        <h4 className="text-cyan-400 font-bold uppercase tracking-widest text-xs">01. Data Acquisition</h4>
        <p className="text-zinc-400 text-sm leading-relaxed">NASAのLandsat 8/9衛星が、30メートル解像度で地表の「熱」と「反射」をスキャンします。これにより、肉眼では見えない植物の健康状態を可視化します。</p>
      </div>
      <div className="space-y-4">
        <h4 className="text-emerald-400 font-bold uppercase tracking-widest text-xs">02. AI Intelligence</h4>
        <p className="text-zinc-400 text-sm leading-relaxed">Google Gemini AIが、蓄積された時系列データから「異常」を検知。農家が今すべきアクションを、膨大な論文データに基づいて提案します。</p>
      </div>
    </div>
    
  </div>
);

export default App;
