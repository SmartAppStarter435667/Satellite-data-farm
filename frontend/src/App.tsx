import React from 'react';
import data from './data.json';

const App = () => {
  return (
    <div className="min-h-screen bg-[#050505] text-white font-sans">
      <nav className="p-6 border-b border-white/10 backdrop-blur-md sticky top-0 z-50">
        <h1 className="text-2xl font-black tracking-tighter text-cyan-400">JAPAN SATELLITE <span className="text-white">EYE</span></h1>
      </nav>

      <main className="p-4 md:p-10 max-w-7xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {data.map((item: any) => (
            <div key={item.id} className="group bg-[#111] border border-white/5 rounded-2xl overflow-hidden hover:border-cyan-500/50 transition-all">
              <div className="relative aspect-video">
                <img src={item.img} className="object-cover w-full h-full group-hover:scale-105 transition-transform duration-700" alt={item.name} />
                <div className="absolute top-4 right-4 bg-black/60 backdrop-blur px-3 py-1 rounded-full text-xs font-mono">
                  {item.date}
                </div>
              </div>
              
              <div className="p-6">
                <div className="flex justify-between items-end mb-4">
                  <h2 className="text-2xl font-bold">{item.name}</h2>
                  <div className="text-right">
                    <p className="text-[10px] text-gray-500 uppercase tracking-widest">NDVI Index</p>
                    <p className={`text-xl font-mono font-bold ${item.ndvi > 0.4 ? 'text-green-400' : 'text-yellow-400'}`}>
                      {item.ndvi}
                    </p>
                  </div>
                </div>
                <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
                  <div className="h-full bg-cyan-500" style={{ width: `${(item.ndvi + 1) * 50}%` }}></div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
};

export default App;
