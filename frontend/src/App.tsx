import React, { useState } from 'react';
import data from './data.json';

const App = () => {
  const [tab, setTab] = useState<'japan' | 'overseas' | 'about'>('japan');

  return (
    <div className="min-h-screen bg-black text-slate-200 font-sans selection:bg-emerald-500/30">
      {/* Navigation */}
      <nav className="fixed top-0 w-full z-50 bg-black/80 backdrop-blur-md border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-emerald-500 rounded-lg flex items-center justify-center font-black text-black text-xl italic">J</div>
            <h1 className="text-xl font-black tracking-tighter text-white uppercase italic">JAPAN SAT-EYE <span className="text-emerald-500 not-italic font-light text-xs tracking-widest ml-2">PRO</span></h1>
          </div>
          <div className="flex gap-4 md:gap-8">
            <TabBtn active={tab === 'japan'} label="国内" onClick={() => setTab('japan')} />
            <TabBtn active={tab === 'overseas'} label="海外" onClick={() => setTab('overseas')} />
            <TabBtn active={tab === 'about'} label="衛星について" onClick={() => setTab('about')} />
          </div>
        </div>
      </nav>

      <main className="pt-32 pb-20 max-w-7xl mx-auto px-6">
        {tab === 'about' ? (
          <AboutSection />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {data[tab].map((item: any) => (
              <div key={item.id} className="group bg-zinc-900 rounded-3xl overflow-hidden border border-white/5 hover:border-emerald-500/30 transition-all shadow-2xl">
                <div className="relative aspect-video">
                  <img src={item.img} className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110" alt={item.name} />
                  <div className="absolute top-4 right-4 bg-black/60 backdrop-blur px-3 py-1 rounded-full text-[10px] font-bold text-white tracking-widest">
                    {item.sat}
                  </div>
                  <div className="absolute bottom-4 left-4 text-[10px] text-white/70 font-mono bg-black/40 px-2 py-1 rounded">
                    観測日: {item.date}
                  </div>
                </div>
                <div className="p-8">
                  <h3 className="text-2xl font-bold mb-6 text-white">{item.name}</h3>
                  <div className="grid grid-cols-2 gap-4 mb-8">
                    <StatItem label="植生(NDVI)" val={item.ndvi} color="text-emerald-400" />
                    <StatItem label="地表温度" val={`${item.temp}℃`} color="text-orange-400" />
                  </div>
                  <div className="bg-emerald-500/5 border border-emerald-500/20 p-4 rounded-2xl relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-1 h-full bg-emerald-500"></div>
                    <p className="text-[10px] text-emerald-500 font-black uppercase mb-1 tracking-widest">Growth Analysis Report</p>
                    <p className="text-sm font-medium leading-relaxed">{item.ai}</p>
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

const TabBtn = ({ active, label, onClick }: any) => (
  <button onClick={onClick} className={`text-xs font-bold uppercase tracking-widest transition-all ${active ? 'text-emerald-400' : 'text-slate-500 hover:text-slate-200'}`}>
    {label}
  </button>
);

const StatItem = ({ label, val, color }: any) => (
  <div className="bg-white/5 p-3 rounded-xl">
    <p className="text-[9px] text-slate-500 font-bold uppercase tracking-widest mb-1">{label}</p>
    <p className={`text-xl font-mono font-bold ${color}`}>{val}</p>
  </div>
);

const AboutSection = () => (
  <div className="max-w-3xl mx-auto space-y-12">
    <section>
      <h2 className="text-4xl font-bold mb-6 text-white tracking-tight text-center">地球をスキャンする仕組み</h2>
      
      <p className="text-lg text-slate-400 leading-relaxed mb-6">
        当システムは、NASAとUSGSが運用する最新鋭の地球観測衛星「Landsat 8/9」から直接データを取得しています。
        衛星は地上約700kmの高さを時速約27,000kmで飛行しながら、目に見える光だけでなく「熱」や「赤外線」を精密に測定しています。
      </p>
    </section>
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
      <div className="bg-zinc-900 p-6 rounded-2xl border border-white/5">
        <h4 className="font-bold text-emerald-400 mb-2 uppercase tracking-widest text-xs">OLI (光学センサ)</h4>
        <p className="text-slate-400">植物の葉の反射特性を捉え、生育の良し悪しを数値化（NDVI）します。</p>
      </div>
      <div className="bg-zinc-900 p-6 rounded-2xl border border-white/5">
        <h4 className="font-bold text-orange-400 mb-2 uppercase tracking-widest text-xs">TIRS (熱赤外センサ)</h4>
        <p className="text-slate-400">地表面から放射される熱を捉え、農地の乾燥状態や異常高温を検知します。</p>
      </div>
    </div>
  </div>
);

export default App;
