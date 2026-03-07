import React from 'react';
import data from './data.json';

const App = () => {
  return (
    <div className="min-h-screen bg-[#0a0a0a] text-slate-100 p-4 md:p-10">
      <header className="mb-12 text-center">
        <h1 className="text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-emerald-400">
          JAPAN SATELLITE PORTAL
        </h1>
        <p className="text-slate-500 mt-2 italic text-sm">Comprehensive Earth Observation Data</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-7xl mx-auto">
        {data.map((item: any) => (
          <div key={item.id} className="bg-zinc-900/50 border border-white/10 rounded-3xl overflow-hidden backdrop-blur-sm">
            <div className="relative aspect-video">
              <img src={item.img} className="w-full h-full object-cover" alt={item.name} />
              <div className="absolute top-4 left-4 bg-black/60 px-3 py-1 rounded-full text-xs font-mono border border-white/10">
                {item.date}
              </div>
            </div>

            <div className="p-6">
              <h2 className="text-2xl font-bold mb-6 flex items-center">
                <span className="w-2 h-8 bg-cyan-500 rounded-full mr-3"></span>
                {item.name}
              </h2>

              <div className="grid grid-cols-2 gap-4">
                <DataCard label="植生(NDVI)" value={item.ndvi} color="text-emerald-400" />
                <DataCard label="水指数(NDWI)" value={item.ndwi} color="text-blue-400" />
                <DataCard label="地表温度" value={`${item.temp}℃`} color="text-orange-400" />
                <DataCard label="雲量" value={`${item.cloud}%`} color="text-slate-400" />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const DataCard = ({ label, value, color }: any) => (
  <div className="bg-white/5 p-3 rounded-2xl border border-white/5">
    <p className="text-[10px] text-slate-500 uppercase font-bold tracking-widest mb-1">{label}</p>
    <p className={`text-xl font-mono font-bold ${color}`}>{value}</p>
  </div>
);

export default App;
