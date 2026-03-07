import React, { useState } from 'react';
import data from './data.json';

const App = () => {
  const [activeTab, setActiveTab] = useState<'japan' | 'globe' | 'about'>('japan');

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      {/* 1. レスポンシブ・ヘッダー */}
      <nav className="fixed top-0 w-full z-50 bg-white/90 backdrop-blur-md border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <h1 className="text-xl font-black tracking-tighter text-blue-600">SATELLITE <span className="text-slate-400 font-light">PRO</span></h1>
          
          {/* PC向けメニュー */}
          <div className="hidden md:flex gap-8 text-xs font-bold uppercase tracking-widest">
            <button onClick={() => setActiveTab('japan')} className={activeTab === 'japan' ? 'text-blue-600' : 'text-slate-400'}>JAPAN</button>
            <button onClick={() => setActiveTab('globe')} className={activeTab === 'globe' ? 'text-blue-600' : 'text-slate-400'}>GLOBE</button>
            <button onClick={() => setActiveTab('about')} className={activeTab === 'about' ? 'text-blue-600' : 'text-slate-400'}>ABOUT</button>
          </div>
        </div>
        
        {/* スマホ向け横スクロールメニュー */}
        <div className="md:hidden flex overflow-x-auto border-t border-slate-100 bg-white px-2 py-3 gap-4 no-scrollbar">
          <MobileNavBtn active={activeTab === 'japan'} label="国内データ" onClick={() => setActiveTab('japan')} />
          <MobileNavBtn active={activeTab === 'globe'} label="仮想地球" onClick={() => setActiveTab('globe')} />
          <MobileNavBtn active={activeTab === 'about'} label="衛星解説" onClick={() => setActiveTab('about')} />
        </div>
      </nav>

      <main className="pt-32 pb-20 max-w-7xl mx-auto px-4">
        {activeTab === 'japan' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {data.japan.map((item: any) => (
              <div key={item.id} className="bg-white rounded-3xl overflow-hidden shadow-sm border border-slate-200">
                <div className="p-5 border-b border-slate-100 flex justify-between items-center">
                  <h3 className="font-bold text-lg">{item.name}</h3>
                  <span className="text-[10px] bg-slate-100 px-2 py-1 rounded-full font-mono">{item.date}</span>
                </div>
                
                {/* 衛星画像の切り替え表示 */}
                <div className="grid grid-cols-2 gap-px bg-slate-200">
                  <div className="bg-white p-2">
                    <p className="text-[9px] font-bold text-slate-400 uppercase mb-1">Landsat 8/9 (可視光)</p>
                    <img src={item.images.visible} className="w-full aspect-square object-cover rounded-lg" alt="visible" />
                  </div>
                  <div className="bg-white p-2">
                    <p className="text-[9px] font-bold text-slate-400 uppercase mb-1">Sentinel-1 (レーダー)</p>
                    <img src={item.images.radar} className="w-full aspect-square object-cover rounded-lg grayscale" alt="radar" />
                  </div>
                </div>

                <div className="p-6 space-y-4">
                  <div className="flex gap-4">
                    <StatBox label="植生指数(NDVI)" val={item.metrics.ndvi} source="Landsat 8" />
                    <StatBox label="地表温度" val={`${item.metrics.temp}℃`} source="Landsat 8" />
                  </div>
                  <div className="bg-blue-50 p-4 rounded-2xl border border-blue-100">
                    <p className="text-[10px] text-blue-500 font-bold uppercase mb-1">AI 営農アドバイス</p>
                    <p className="text-sm font-medium">{item.ai}</p>
                  </div>
                  <p className="text-[9px] text-slate-400 text-right">気象データ提供: ひまわり8号 ({item.metrics.update})</p>
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'globe' && <GlobeSection />}
        {activeTab === 'about' && <AboutSection />}
      </main>
    </div>
  );
};

const MobileNavBtn = ({ active, label, onClick }: any) => (
  <button onClick={onClick} className={`whitespace-nowrap px-4 py-1.5 rounded-full text-xs font-bold transition-all ${active ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-500'}`}>
    {label}
  </button>
);

const StatBox = ({ label, val, source }: any) => (
  <div className="flex-1">
    <p className="text-[9px] text-slate-400 font-bold uppercase">{label}</p>
    <p className="text-xl font-black text-slate-800">{val}</p>
    <p className="text-[8px] text-slate-300 font-mono">Source: {source}</p>
  </div>
);

const GlobeSection = () => (
  <div className="flex flex-col items-center py-10">
    <h2 className="text-2xl font-bold mb-4">仮想地球ブラウザ</h2>
    <div className="relative w-72 h-72 md:w-96 md:h-96 rounded-full bg-slate-900 shadow-2xl overflow-hidden border-4 border-white">
      {/* 3D地球のシミュレーション */}
      <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/world-map.png')] opacity-30 animate-scroll-bg"></div>
      <div className="absolute inset-0 bg-gradient-to-tr from-blue-900/50 to-transparent"></div>
      <div className="absolute inset-0 flex items-center justify-center text-center p-6">
        <p className="text-white text-[10px] font-bold tracking-widest uppercase">
          [スマホ対応]<br />スワイプで地球を回転させ、<br />観測地点をタップしてください
        </p>
      </div>
    </div>
    <p className="mt-8 text-slate-400 text-sm max-w-xs text-center leading-relaxed font-medium">
      ※現在はシミュレーションモードです。B2B版では個別の農地境界(BBox)をこの地球上にマッピングします。
    </p>
  </div>
);

const AboutSection = () => (
  <div className="max-w-2xl mx-auto space-y-12">
    <SatelliteIntro 
      name="Landsat 8/9" 
      tag="光学・熱赤外衛星"
      desc="NASAが運用。農作物の健康状態（NDVI）や、地面の温度を非常に精密に測る「農業の目」です。"
    />
    
    <SatelliteIntro 
      name="Sentinel-1" 
      tag="レーダー衛星(SAR)"
      desc="欧州が運用。マイクロ波を使うため、雲があっても夜間でも地表を観測可能。梅雨時期の生育監視に必須です。"
    />
    
    <SatelliteIntro 
      name="ひまわり 8号/9号" 
      tag="静止気象衛星"
      desc="日本が運用。約10分ごとに更新されるため、リアルタイムの気象変化や日照時間を正確に把握します。"
    />
    
  </div>
);

const SatelliteIntro = ({ name, tag, desc }: any) => (
  <div className="border-l-4 border-blue-500 pl-6 py-2">
    <p className="text-xs font-bold text-blue-500 uppercase tracking-widest">{tag}</p>
    <h3 className="text-2xl font-black mb-2">{name}</h3>
    <p className="text-slate-600 text-sm leading-relaxed">{desc}</p>
  </div>
);

export default App;
