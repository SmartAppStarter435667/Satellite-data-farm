import React from 'react';
import data from './data.json';

const App = () => (
  <div className="min-h-screen bg-black text-slate-100 p-4 md:p-8">
    <h1 className="text-3xl font-black mb-10 text-emerald-400 tracking-tighter">SATELLITE AI PORTAL</h1>
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {data.map((item: any) => (
        <div key={item.id} className="bg-zinc-900 border border-white/10 rounded-2xl overflow-hidden shadow-xl">
          <img src={item.img} className="w-full aspect-video object-cover" alt={item.name} />
          <div className="p-5">
            <h2 className="text-xl font-bold mb-4">{item.name}</h2>
            <div className="grid grid-cols-2 gap-2 text-sm mb-4">
              <div className="bg-white/5 p-2 rounded">植生: <span className="text-emerald-400 font-mono">{item.ndvi}</span></div>
              <div className="bg-white/5 p-2 rounded">水域: <span className="text-blue-400 font-mono">{item.ndwi}</span></div>
              <div className="bg-white/5 p-2 rounded">温度: <span className="text-orange-400 font-mono">{item.temp}℃</span></div>
              <div className="bg-white/5 p-2 rounded">雲量: <span className="text-slate-400 font-mono">{item.cloud}%</span></div>
            </div>
            <div className="bg-emerald-500/10 border border-emerald-500/20 p-3 rounded-lg">
              <p className="text-[10px] text-emerald-500 font-bold uppercase mb-1">AI分析</p>
              <p className="text-xs leading-relaxed">{item.ai}</p>
            </div>
          </div>
        </div>
      ))}
    </div>
  </div>
);

export default App;
