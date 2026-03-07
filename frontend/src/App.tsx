import React from 'react';
import data from './data.json';

const App = () => (
  <div className="min-h-screen bg-[#050505] text-slate-100 p-4 md:p-8">
    <header className="max-w-6xl mx-auto mb-10 border-b border-white/10 pb-6 text-center md:text-left">
      <h1 className="text-3xl font-black tracking-tighter text-cyan-400">JAPAN SAT-MONITOR <span className="text-white">AI</span></h1>
    </header>
    
    <main className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {data.map((p: any) => (
        <div key={p.id} className="bg-zinc-900 rounded-3xl overflow-hidden border border-white/5 hover:border-cyan-500/30 transition-all flex flex-col">
          <div className="relative aspect-video">
            <img src={p.img} className="w-full h-full object-cover" alt={p.name} />
            <div className="absolute top-3 right-3 bg-black/70 backdrop-blur-md px-2 py-1 rounded text-[10px] font-mono">
              {p.date}
            </div>
          </div>
          
          <div className="p-6 flex-grow flex flex-col">
            <h2 className="text-2xl font-bold mb-4">{p.name}</h2>
            
            <div className="grid grid-cols-2 gap-3 mb-6">
              <StatCard label="植生(NDVI)" val={p.ndvi} color="text-emerald-400" />
              <StatCard label="水域(NDWI)" val={p.ndwi} color="text-blue-400" />
              <StatCard label="地表温度" val={`${p.temp}℃`} color="text-orange-400" />
              <StatCard label="雲量" val={`${p.cloud}%`} color="text-slate-400" />
            </div>

            <div className="mt-auto bg-cyan-500/5 border border-cyan-500/20 p-4 rounded-xl">
              <div className="flex items-center gap-2 mb-1">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500"></span>
                </span>
                <p className="text-[10px] font-bold text-cyan-500 uppercase tracking-widest">AI Analysis</p>
              </div>
              <p className="text-xs leading-relaxed text-slate-300">{p.ai}</p>
            </div>
          </div>
        </div>
      ))}
    </main>
  </div>
);

const StatCard = ({ label, val, color }: any) => (
  <div className="bg-white/5 p-3 rounded-2xl">
    <p className="text-[9px] text-slate-500 uppercase font-bold mb-1 tracking-tighter">{label}</p>
    <p className={`text-lg font-mono font-bold ${color}`}>{val}</p>
  </div>
);

export default App;
