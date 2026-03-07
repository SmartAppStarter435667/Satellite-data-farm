import React from 'react';
import data from './data.json';

const App = () => {
  return (
    <div className="min-h-screen bg-black text-slate-200">
      <header className="p-8 border-b border-white/10 text-center">
        <h1 className="text-3xl font-black tracking-widest text-emerald-400">JAPAN SAT-EYE</h1>
        <p className="text-sm text-slate-500 mt-2">47 Prefectures Real-time Monitoring</p>
      </header>

      <main className="max-w-7xl mx-auto p-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {data.map((pref: any) => (
          <div key={pref.id} className="bg-zinc-900 rounded-2xl overflow-hidden border border-white/5 hover:border-emerald-500/50 transition-all shadow-2xl">
            <div className="relative aspect-video">
              <img src={pref.img} alt={pref.name} className="w-full h-full object-cover" />
              <div className="absolute bottom-2 right-2 bg-black/70 backdrop-blur text-[10px] px-2 py-1 rounded">
                Observed: {pref.date}
              </div>
            </div>
            <div className="p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold">{pref.name}</h2>
                <div className="text-right">
                  <span className="text-[10px] block text-slate-500 uppercase tracking-tighter">NDVI Index</span>
                  <span className={`text-lg font-mono font-bold ${pref.ndvi > 0.4 ? 'text-emerald-400' : 'text-amber-400'}`}>
                    {pref.ndvi}
                  </span>
                </div>
              </div>
              <div className="w-full bg-white/5 h-1.5 rounded-full overflow-hidden">
                <div className="bg-emerald-500 h-full" style={{ width: `${Math.max(0, pref.ndvi * 100)}%` }}></div>
              </div>
            </div>
          </div>
        ))}
      </main>
    </div>
  );
};

export default App;
