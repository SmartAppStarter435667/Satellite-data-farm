import React, { useState, useEffect, useRef, useCallback } from 'react';

// =============================================
// 型定義
// =============================================
interface FarmData {
  id: string;
  name: string;
  prefecture: string;
  lat: number;
  lon: number;
  ndvi: number;
  temp: number;
  radar_url: string;
  vis_url: string;
  ai: string;
  date: string;
  update: string;
  comments: Comment[];
}

interface Comment {
  id: string;
  user: string;
  text: string;
  photo_url?: string;
  created_at: string;
}

interface Photo {
  file: File;
  lat: number | null;
  lon: number | null;
  preview: string;
}

// =============================================
// NDVI カラースケール（農業標準）
// =============================================
const ndviToColor = (ndvi: number): string => {
  if (ndvi < 0)   return '#5b4fcf'; // 水・建物
  if (ndvi < 0.1) return '#d4a84b'; // 裸地・砂漠
  if (ndvi < 0.2) return '#c8c84e'; // まばらな植生
  if (ndvi < 0.4) return '#85c43b'; // 低密度植生
  if (ndvi < 0.6) return '#3fa83f'; // 健全な農地
  return '#1a5c2e';                 // 高密度・旺盛な植生
};

const ndviLabel = (ndvi: number): string => {
  if (ndvi < 0)   return '水域/建物';
  if (ndvi < 0.1) return '裸地';
  if (ndvi < 0.2) return '植生薄い';
  if (ndvi < 0.4) return '成長中';
  if (ndvi < 0.6) return '健全';
  return '旺盛';
};

// =============================================
// Exif から緯度経度を取得するユーティリティ
// =============================================
async function extractExifCoords(file: File): Promise<{lat: number, lon: number} | null> {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const view = new DataView(e.target!.result as ArrayBuffer);
        // JPEG SOI check
        if (view.getUint16(0) !== 0xFFD8) { resolve(null); return; }
        let offset = 2;
        while (offset < view.byteLength - 2) {
          const marker = view.getUint16(offset);
          if (marker === 0xFFE1) { // APP1 (Exif)
            const exifOffset = offset + 10;
            const isBigEndian = view.getUint16(exifOffset) === 0x4D4D;
            const ifdOffset = view.getUint32(exifOffset + 4, !isBigEndian) + exifOffset;
            const numEntries = view.getUint16(ifdOffset, !isBigEndian);
            let gpsIFDOffset = -1;
            for (let i = 0; i < numEntries; i++) {
              const entryOffset = ifdOffset + 2 + i * 12;
              const tag = view.getUint16(entryOffset, !isBigEndian);
              if (tag === 0x8825) {
                gpsIFDOffset = view.getUint32(entryOffset + 8, !isBigEndian) + exifOffset;
              }
            }
            if (gpsIFDOffset > 0) {
              const gpsEntries = view.getUint16(gpsIFDOffset, !isBigEndian);
              let lat = 0, lon = 0, latRef = 'N', lonRef = 'E';
              for (let i = 0; i < gpsEntries; i++) {
                const e = gpsIFDOffset + 2 + i * 12;
                const tag = view.getUint16(e, !isBigEndian);
                if (tag === 0x0001) latRef = String.fromCharCode(view.getUint8(e + 8));
                if (tag === 0x0003) lonRef = String.fromCharCode(view.getUint8(e + 8));
                if (tag === 0x0002 || tag === 0x0004) {
                  const valOffset = view.getUint32(e + 8, !isBigEndian) + exifOffset;
                  const deg = view.getUint32(valOffset, !isBigEndian) / view.getUint32(valOffset + 4, !isBigEndian);
                  const min = view.getUint32(valOffset + 8, !isBigEndian) / view.getUint32(valOffset + 12, !isBigEndian);
                  const sec = view.getUint32(valOffset + 16, !isBigEndian) / view.getUint32(valOffset + 20, !isBigEndian);
                  const val = deg + min / 60 + sec / 3600;
                  if (tag === 0x0002) lat = val;
                  else lon = val;
                }
              }
              if (lat !== 0 && lon !== 0) {
                resolve({ lat: latRef === 'S' ? -lat : lat, lon: lonRef === 'W' ? -lon : lon });
                return;
              }
            }
          }
          offset += 2 + view.getUint16(offset + 2);
        }
        resolve(null);
      } catch { resolve(null); }
    };
    reader.readAsArrayBuffer(file.slice(0, 65536));
  });
}

// =============================================
// SAMPLE DATA（47都道府県の代表データ）
// =============================================
const PREFECTURES_SAMPLE: FarmData[] = [
  { id: 'hokkaido', name: '北海道', prefecture: '北海道', lat: 43.06, lon: 141.35, ndvi: 0.72, temp: 8.2, vis_url: '', radar_url: '', ai: '旺盛な生育。麦類・大豆の生育が順調です。北部の一部に水分不足の傾向あり、早期灌水を推奨します。', date: '2025年06月15日', update: '2025-06-15', comments: [{ id: 'c1', user: '農家A', text: '今年は例年より早く穂が出てきました！', created_at: '2025-06-10' }] },
  { id: 'aomori', name: '青森県', prefecture: '青森県', lat: 40.82, lon: 140.74, ndvi: 0.64, temp: 12.5, vis_url: '', radar_url: '', ai: '健全な生育状態。りんご園のNDVI値は平均を上回り、着果率も良好です。', date: '2025年06月15日', update: '2025-06-15', comments: [] },
  { id: 'iwate', name: '岩手県', prefecture: '岩手県', lat: 39.70, lon: 141.15, ndvi: 0.58, temp: 14.1, vis_url: '', radar_url: '', ai: '生育は概ね良好。沿岸部の農地では塩害モニタリングを継続推奨。', date: '2025年06月15日', update: '2025-06-15', comments: [] },
  { id: 'niigata', name: '新潟県', prefecture: '新潟県', lat: 37.90, lon: 139.02, ndvi: 0.61, temp: 18.3, vis_url: '', radar_url: '', ai: '稲作エリアのNDVIが上昇中。梅雨入り後の日照不足に注意。Sentinel-1レーダーで水管理を確認中。', date: '2025年06月15日', update: '2025-06-15', comments: [{ id: 'c2', user: '新潟農協', text: 'コシヒカリ圃場の活着が良好です', created_at: '2025-06-12' }] },
  { id: 'toyama', name: '富山県', prefecture: '富山県', lat: 36.70, lon: 137.21, ndvi: 0.55, temp: 20.1, vis_url: '', radar_url: '', ai: '水稲の生育は標準的。チューリップ農家は球根収穫期が近いため、水分管理を最終確認。', date: '2025年06月15日', update: '2025-06-15', comments: [] },
  { id: 'ishikawa', name: '石川県', prefecture: '石川県', lat: 36.59, lon: 136.63, ndvi: 0.52, temp: 21.3, vis_url: '', radar_url: '', ai: '能登の農地は復旧作業後の生育観察継続中。NDVI値は昨年比+0.08と回復傾向。', date: '2025年06月15日', update: '2025-06-15', comments: [] },
  { id: 'fukui', name: '福井県', prefecture: '福井県', lat: 36.07, lon: 136.22, ndvi: 0.57, temp: 21.8, vis_url: '', radar_url: '', ai: '越前かにの代わりに農地モニタリング中。水稲の生育順調で大雨被害なし。', date: '2025年06月15日', update: '2025-06-15', comments: [] },
  { id: 'nagano', name: '長野県', prefecture: '長野県', lat: 36.65, lon: 138.18, ndvi: 0.63, temp: 16.4, vis_url: '', radar_url: '', ai: 'りんご・ぶどう農園の生育は標準以上。高原野菜は涼しい気候で生育良好。', date: '2025年06月15日', update: '2025-06-15', comments: [] },
  { id: 'shizuoka', name: '静岡県', prefecture: '静岡県', lat: 34.98, lon: 138.38, ndvi: 0.59, temp: 22.6, vis_url: '', radar_url: '', ai: 'お茶畑のNDVIは平均0.59で健全。二番茶収穫期に向けて施肥タイミングを最適化。', date: '2025年06月15日', update: '2025-06-15', comments: [] },
  { id: 'aichi', name: '愛知県', prefecture: '愛知県', lat: 35.18, lon: 136.91, ndvi: 0.45, temp: 24.2, vis_url: '', radar_url: '', ai: '都市近郊農地のNDVI値は施設農業の影響で変動あり。キャベツ産地は出荷量増加中。', date: '2025年06月15日', update: '2025-06-15', comments: [] },
  { id: 'osaka', name: '大阪府', prefecture: '大阪府', lat: 34.69, lon: 135.50, ndvi: 0.22, temp: 26.5, vis_url: '', radar_url: '', ai: '都市農業エリア。少数の農地でなにわ野菜を栽培中。緑地保全に向けた取り組みを確認。', date: '2025年06月15日', update: '2025-06-15', comments: [] },
  { id: 'kyoto', name: '京都府', prefecture: '京都府', lat: 35.02, lon: 135.76, ndvi: 0.48, temp: 23.8, vis_url: '', radar_url: '', ai: '京野菜（九条ねぎ・聖護院大根等）産地のNDVI良好。嵐山周辺の竹林が強いシグナルを出力中。', date: '2025年06月15日', update: '2025-06-15', comments: [] },
  { id: 'hyogo', name: '兵庫県', prefecture: '兵庫県', lat: 34.69, lon: 135.18, ndvi: 0.54, temp: 23.5, vis_url: '', radar_url: '', ai: '但馬・丹波の農地は生育順調。神戸市街地周辺は農地面積縮小傾向をモニタリング中。', date: '2025年06月15日', update: '2025-06-15', comments: [] },
  { id: 'okayama', name: '岡山県', prefecture: '岡山県', lat: 34.66, lon: 133.93, ndvi: 0.61, temp: 23.1, vis_url: '', radar_url: '', ai: 'ピオーネ（ぶどう）産地のNDVI高値安定。晴れの国らしく日照量も十分。', date: '2025年06月15日', update: '2025-06-15', comments: [] },
  { id: 'hiroshima', name: '広島県', prefecture: '広島県', lat: 34.40, lon: 132.46, ndvi: 0.53, temp: 23.8, vis_url: '', radar_url: '', ai: 'レモン産地（尾道・大崎上島）の生育は良好。Sentinel-1で島嶼部農地の水分量を確認中。', date: '2025年06月15日', update: '2025-06-15', comments: [] },
  { id: 'yamaguchi', name: '山口県', prefecture: '山口県', lat: 34.19, lon: 131.47, ndvi: 0.56, temp: 22.9, vis_url: '', radar_url: '', ai: 'なし・かき産地のモニタリング継続中。農地のNDVIは平均水準で安定。', date: '2025年06月15日', update: '2025-06-15', comments: [] },
  { id: 'tokushima', name: '徳島県', prefecture: '徳島県', lat: 34.07, lon: 134.56, ndvi: 0.49, temp: 24.4, vis_url: '', radar_url: '', ai: 'すだち農園の生育好調。吉野川流域の水稲エリアは水管理適切。', date: '2025年06月15日', update: '2025-06-15', comments: [] },
  { id: 'ehime', name: '愛媛県', prefecture: '愛媛県', lat: 33.84, lon: 132.77, ndvi: 0.62, temp: 23.6, vis_url: '', radar_url: '', ai: '柑橘類（みかん・伊予柑）産地のNDVI値は例年比+5%と好調。品質の高い収穫が期待されます。', date: '2025年06月15日', update: '2025-06-15', comments: [] },
  { id: 'kochi', name: '高知県', prefecture: '高知県', lat: 33.56, lon: 133.53, ndvi: 0.67, temp: 24.0, vis_url: '', radar_url: '', ai: 'ショウガ・ニラの施設農業エリアは生育良好。四万十川流域の農地で水害リスク継続監視。', date: '2025年06月15日', update: '2025-06-15', comments: [] },
  { id: 'fukuoka', name: '福岡県', prefecture: '福岡県', lat: 33.61, lon: 130.42, ndvi: 0.51, temp: 24.8, vis_url: '', radar_url: '', ai: '博多あまおうの生育モニタリング完了。筑紫平野の水稲エリアは田植え後の活着が順調。', date: '2025年06月15日', update: '2025-06-15', comments: [] },
  { id: 'saga', name: '佐賀県', prefecture: '佐賀県', lat: 33.26, lon: 130.30, ndvi: 0.66, temp: 24.3, vis_url: '', radar_url: '', ai: '佐賀平野の水稲・麦作は順調な生育を示しています。有明海沿岸の農地で塩分濃度の定期観測を推奨します。', date: '2025年06月15日', update: '2025-06-15', comments: [{ id: 'c3', user: '佐賀農業センター', text: '今年の梅雨は雨が少ない。灌水スケジュールを見直しました', created_at: '2025-06-08' }] },
  { id: 'nagasaki', name: '長崎県', prefecture: '長崎県', lat: 32.74, lon: 129.87, ndvi: 0.58, temp: 24.1, vis_url: '', radar_url: '', ai: '島嶼部農地のSentinel-1観測でジャガイモ・対馬の農地状況を把握。島嶼特有の地形補正処理済み。', date: '2025年06月15日', update: '2025-06-15', comments: [] },
  { id: 'kumamoto', name: '熊本県', prefecture: '熊本県', lat: 32.79, lon: 130.74, ndvi: 0.69, temp: 24.5, vis_url: '', radar_url: '', ai: 'トマト・メロンの施設農業産地は順調。阿蘇の農地でも放牧草地の生育良好を確認。', date: '2025年06月15日', update: '2025-06-15', comments: [] },
  { id: 'oita', name: '大分県', prefecture: '大分県', lat: 33.24, lon: 131.61, ndvi: 0.55, temp: 23.9, vis_url: '', radar_url: '', ai: 'かぼすの産地モニタリング中。森林農地混在エリアのNDVIは平均0.55で安定。', date: '2025年06月15日', update: '2025-06-15', comments: [] },
  { id: 'miyazaki', name: '宮崎県', prefecture: '宮崎県', lat: 31.91, lon: 131.42, ndvi: 0.71, temp: 25.1, vis_url: '', radar_url: '', ai: 'マンゴー・ピーマンの主要産地は生育旺盛。Gemini AI分析：今後10日間の高温予報あり、早朝灌水を推奨。', date: '2025年06月15日', update: '2025-06-15', comments: [] },
  { id: 'kagoshima', name: '鹿児島県', prefecture: '鹿児島県', lat: 31.56, lon: 130.56, ndvi: 0.68, temp: 25.8, vis_url: '', radar_url: '', ai: 'さつまいも・茶の主要産地は高NDVI値を維持。桜島の火山性土壌でも生育への影響は限定的。', date: '2025年06月15日', update: '2025-06-15', comments: [] },
  { id: 'okinawa', name: '沖縄県', prefecture: '沖縄県', lat: 26.21, lon: 127.68, ndvi: 0.73, temp: 28.5, vis_url: '', radar_url: '', ai: 'さとうきびのNDVI値は例年を上回る高値。台風シーズン前の農地防風対策チェックリストを提供中。', date: '2025年06月15日', update: '2025-06-15', comments: [] },
  { id: 'tokyo', name: '東京都', prefecture: '東京都', lat: 35.68, lon: 139.69, ndvi: 0.18, temp: 26.8, vis_url: '', radar_url: '', ai: '都市農地（小平・あきる野等）のNDVIは都市化の影響で低め。農地保全指定区域は良好な値を維持。', date: '2025年06月15日', update: '2025-06-15', comments: [] },
];

// =============================================
// メインApp
// =============================================
const App = () => {
  const [activeTab, setActiveTab] = useState<'japan' | 'globe' | 'sns' | 'upload' | 'about'>('japan');
  const [selectedFarm, setSelectedFarm] = useState<FarmData | null>(null);
  const [filterPref, setFilterPref] = useState<string>('all');
  const [photo, setPhoto] = useState<Photo | null>(null);
  const [matchedFarm, setMatchedFarm] = useState<FarmData | null>(null);
  const [commentText, setCommentText] = useState('');
  const [sortBy, setSortBy] = useState<'ndvi_desc' | 'ndvi_asc' | 'temp_desc'>('ndvi_desc');

  const farms = PREFECTURES_SAMPLE;
  const sortedFarms = [...farms].sort((a, b) => {
    if (sortBy === 'ndvi_desc') return b.ndvi - a.ndvi;
    if (sortBy === 'ndvi_asc') return a.ndvi - b.ndvi;
    return b.temp - a.temp;
  }).filter(f => filterPref === 'all' || f.prefecture === filterPref);

  const handlePhotoUpload = useCallback(async (file: File) => {
    const preview = URL.createObjectURL(file);
    const coords = await extractExifCoords(file);
    let matched: FarmData | null = null;
    if (coords) {
      matched = farms.reduce((prev, curr) => {
        const dPrev = Math.hypot(prev.lat - coords.lat, prev.lon - coords.lon);
        const dCurr = Math.hypot(curr.lat - coords.lat, curr.lon - coords.lon);
        return dCurr < dPrev ? curr : prev;
      }, farms[0]);
    }
    setPhoto({ file, lat: coords?.lat ?? null, lon: coords?.lon ?? null, preview });
    setMatchedFarm(matched);
    setActiveTab('upload');
  }, [farms]);

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* ナビゲーション */}
      <nav className="fixed top-0 w-full z-50 bg-gray-900/95 backdrop-blur-md border-b border-green-900/30">
        <div className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-lg">🛰️</span>
            <h1 className="text-base font-black tracking-tight">
              <span className="text-green-400">SATELLITE</span>
              <span className="text-gray-400 font-light"> PRO</span>
            </h1>
          </div>
          <div className="hidden md:flex gap-6 text-xs font-bold uppercase tracking-widest">
            {(['japan','globe','sns','upload','about'] as const).map(tab => (
              <button key={tab} onClick={() => setActiveTab(tab)}
                className={`transition-colors ${activeTab === tab ? 'text-green-400' : 'text-gray-500 hover:text-gray-300'}`}>
                {tab === 'japan' ? '農地データ' : tab === 'globe' ? '地球儀' : tab === 'sns' ? 'コミュニティ' : tab === 'upload' ? '写真解析' : '衛星解説'}
              </button>
            ))}
          </div>
          {/* モバイルメニュー */}
          <div className="md:hidden flex gap-2 overflow-x-auto">
            {(['japan','globe','sns','upload','about'] as const).map(tab => (
              <button key={tab} onClick={() => setActiveTab(tab)}
                className={`whitespace-nowrap px-3 py-1 rounded-full text-[10px] font-bold ${activeTab === tab ? 'bg-green-500 text-black' : 'bg-gray-800 text-gray-400'}`}>
                {tab === 'japan' ? '農地' : tab === 'globe' ? '地球儀' : tab === 'sns' ? 'SNS' : tab === 'upload' ? '写真' : '解説'}
              </button>
            ))}
          </div>
        </div>
      </nav>

      <main className="pt-14 min-h-screen">
        {/* ===== 農地データタブ ===== */}
        {activeTab === 'japan' && (
          <div className="max-w-7xl mx-auto px-4 py-8">
            {/* フィルター */}
            <div className="flex flex-wrap gap-3 mb-6">
              <select value={filterPref} onChange={e => setFilterPref(e.target.value)}
                className="bg-gray-800 border border-gray-700 text-sm px-3 py-2 rounded-lg text-white">
                <option value="all">全都道府県</option>
                {[...new Set(farms.map(f => f.prefecture))].map(p => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
              <select value={sortBy} onChange={e => setSortBy(e.target.value as any)}
                className="bg-gray-800 border border-gray-700 text-sm px-3 py-2 rounded-lg text-white">
                <option value="ndvi_desc">NDVI（高順）</option>
                <option value="ndvi_asc">NDVI（低順）</option>
                <option value="temp_desc">気温（高順）</option>
              </select>
              <span className="text-xs text-gray-500 self-center">{sortedFarms.length}件表示</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {sortedFarms.map(farm => (
                <div key={farm.id} onClick={() => setSelectedFarm(farm)}
                  className="bg-gray-900 rounded-2xl border border-gray-800 hover:border-green-700 transition-all cursor-pointer overflow-hidden">
                  
                  {/* NDVI カラーバー */}
                  <div className="h-1.5" style={{ backgroundColor: ndviToColor(farm.ndvi) }} />
                  
                  <div className="p-5">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <h3 className="font-bold text-base">{farm.name}</h3>
                        <span className="text-[10px] text-gray-500">{farm.date}</span>
                      </div>
                      <span className="text-xs px-2 py-1 rounded-full font-mono font-bold"
                        style={{ backgroundColor: ndviToColor(farm.ndvi) + '33', color: ndviToColor(farm.ndvi) }}>
                        {ndviLabel(farm.ndvi)}
                      </span>
                    </div>

                    <div className="flex gap-4 mb-4">
                      <div>
                        <p className="text-[9px] text-gray-500 uppercase font-bold">NDVI</p>
                        <p className="text-2xl font-black" style={{ color: ndviToColor(farm.ndvi) }}>{farm.ndvi.toFixed(2)}</p>
                      </div>
                      <div>
                        <p className="text-[9px] text-gray-500 uppercase font-bold">地表温度</p>
                        <p className="text-2xl font-black text-orange-400">{farm.temp}℃</p>
                      </div>
                      <div>
                        <p className="text-[9px] text-gray-500 uppercase font-bold">コメント</p>
                        <p className="text-2xl font-black text-blue-400">{farm.comments.length}</p>
                      </div>
                    </div>

                    <div className="bg-gray-800/50 rounded-xl p-3">
                      <p className="text-[9px] text-green-400 font-bold mb-1">🤖 AI 営農アドバイス</p>
                      <p className="text-xs text-gray-300 leading-relaxed line-clamp-2">{farm.ai}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ===== 地球儀タブ ===== */}
        {activeTab === 'globe' && <GlobeSection farms={farms} onSelect={setSelectedFarm} />}

        {/* ===== SNSタブ ===== */}
        {activeTab === 'sns' && (
          <div className="max-w-3xl mx-auto px-4 py-8">
            <h2 className="text-xl font-bold mb-2">農家コミュニティ</h2>
            <p className="text-sm text-gray-400 mb-6">農地ごとに写真付きコメントを投稿・共有できます。</p>
            {farms.filter(f => f.comments.length > 0).map(farm => (
              <div key={farm.id} className="mb-8">
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-2 h-2 rounded-full" style={{ backgroundColor: ndviToColor(farm.ndvi) }} />
                  <h3 className="font-bold text-sm">{farm.name}</h3>
                  <span className="text-[10px] text-gray-500">NDVI {farm.ndvi.toFixed(2)}</span>
                </div>
                {farm.comments.map(c => (
                  <div key={c.id} className="bg-gray-900 rounded-xl p-4 mb-2 border border-gray-800">
                    <div className="flex justify-between mb-1">
                      <span className="text-xs font-bold text-green-400">{c.user}</span>
                      <span className="text-[10px] text-gray-600">{c.created_at}</span>
                    </div>
                    <p className="text-sm text-gray-300">{c.text}</p>
                  </div>
                ))}
              </div>
            ))}
          </div>
        )}

        {/* ===== 写真解析タブ ===== */}
        {activeTab === 'upload' && (
          <div className="max-w-2xl mx-auto px-4 py-8">
            <h2 className="text-xl font-bold mb-2">📸 写真1枚で農地解析</h2>
            <p className="text-sm text-gray-400 mb-6">Exifデータ付き写真をアップロードすると、農地を自動特定し衛星データと紐付けます。</p>
            
            <label className="block border-2 border-dashed border-gray-700 rounded-2xl p-8 text-center cursor-pointer hover:border-green-600 transition-colors">
              <input type="file" accept="image/*" className="hidden"
                onChange={e => e.target.files?.[0] && handlePhotoUpload(e.target.files[0])} />
              {photo ? (
                <img src={photo.preview} className="max-h-60 mx-auto rounded-xl mb-4" alt="preview" />
              ) : (
                <div className="text-gray-500">
                  <div className="text-4xl mb-3">🌾</div>
                  <p className="font-bold">写真をドロップ or クリック</p>
                  <p className="text-xs mt-1">JPEG/PNG対応。Exifデータから位置情報を自動取得</p>
                </div>
              )}
            </label>

            {photo && (
              <div className="mt-4 bg-gray-900 rounded-2xl p-5 border border-gray-800">
                <h3 className="font-bold mb-3">解析結果</h3>
                {photo.lat ? (
                  <div className="space-y-2">
                    <div className="flex gap-6">
                      <div>
                        <p className="text-[10px] text-gray-500">緯度</p>
                        <p className="font-mono text-sm text-green-400">{photo.lat.toFixed(5)}</p>
                      </div>
                      <div>
                        <p className="text-[10px] text-gray-500">経度</p>
                        <p className="font-mono text-sm text-green-400">{photo.lon?.toFixed(5)}</p>
                      </div>
                    </div>
                    {matchedFarm && (
                      <div className="bg-green-900/20 border border-green-800 rounded-xl p-4 mt-3">
                        <p className="text-xs text-green-400 font-bold mb-1">✅ 農地マッチング成功</p>
                        <p className="font-bold">{matchedFarm.name}</p>
                        <p className="text-xs text-gray-400">NDVI: {matchedFarm.ndvi} / 地表温度: {matchedFarm.temp}℃</p>
                        <p className="text-xs text-gray-300 mt-2">{matchedFarm.ai}</p>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="bg-yellow-900/20 border border-yellow-800 rounded-xl p-4">
                    <p className="text-xs text-yellow-400 font-bold">⚠️ Exif位置情報なし</p>
                    <p className="text-xs text-gray-400 mt-1">スマートフォンの位置情報をONにして撮影すると自動マッチングが可能になります。</p>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* ===== 衛星解説タブ ===== */}
        {activeTab === 'about' && (
          <div className="max-w-3xl mx-auto px-4 py-8 space-y-8">
            <h2 className="text-xl font-bold">衛星データ解説</h2>
            {[
              { name: 'Landsat 8/9', tag: '光学・熱赤外衛星 / NASA', icon: '🔴', color: 'red', res: '30m (熱:100m)', update: '16日', desc: 'NASAが運用する農業衛星。NDVI（植生指数）と地表温度を30m解像度で計測。農地全体の生育状況と水分ストレスを高精度で把握できます。' },
              { name: 'Sentinel-2', tag: '光学衛星 / ESA', icon: '🟢', color: 'green', res: '10m', update: '5日', desc: '欧州宇宙機関の高解像度光学衛星。Landsatより細かく農地区画（10m）を判別可能。生育の遅れているエリアを色分けして表示します。' },
              { name: 'Sentinel-1 SAR', tag: 'レーダー衛星 / ESA', icon: '📡', color: 'blue', res: '10m', update: '6〜12日', desc: 'マイクロ波レーダーで雲・夜間を問わず観測可能。梅雨時期や台風後の農地水分量・地表変動をリアルタイム把握。日本の農業に必須の衛星です。' },
              { name: 'ひまわり 8/9号', tag: '静止気象衛星 / JAXA', icon: '🌤️', color: 'yellow', res: '2km（可視光）', update: '10分', desc: '日本が運用する気象衛星。約10分ごとに日本全域を更新するため、リアルタイムの雲・日照・気象変化を把握。農作業のタイミング判断に活用。' },
            ].map(s => (
              <div key={s.name} className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
                <div className="flex items-start gap-4">
                  <span className="text-3xl">{s.icon}</span>
                  <div className="flex-1">
                    <p className="text-[10px] text-gray-500 font-bold uppercase">{s.tag}</p>
                    <h3 className="text-lg font-black mb-1">{s.name}</h3>
                    <div className="flex gap-4 mb-3">
                      <span className="text-[10px] bg-gray-800 px-2 py-1 rounded-full">解像度: {s.res}</span>
                      <span className="text-[10px] bg-gray-800 px-2 py-1 rounded-full">更新: {s.update}</span>
                    </div>
                    <p className="text-sm text-gray-400 leading-relaxed">{s.desc}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {/* ===== 農地詳細モーダル ===== */}
      {selectedFarm && (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-end md:items-center justify-center p-4"
          onClick={() => setSelectedFarm(null)}>
          <div className="bg-gray-900 rounded-3xl w-full max-w-lg max-h-[85vh] overflow-y-auto"
            onClick={e => e.stopPropagation()}>
            <div className="h-2 rounded-t-3xl" style={{ backgroundColor: ndviToColor(selectedFarm.ndvi) }} />
            <div className="p-6">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h2 className="text-xl font-black">{selectedFarm.name}</h2>
                  <p className="text-xs text-gray-500">{selectedFarm.date}</p>
                </div>
                <button onClick={() => setSelectedFarm(null)} className="text-gray-500 hover:text-white text-xl">×</button>
              </div>

              {/* 衛星画像 */}
              <div className="grid grid-cols-2 gap-2 mb-4">
                <div>
                  <p className="text-[9px] text-gray-500 mb-1">Landsat (可視光)</p>
                  <div className="aspect-square bg-gray-800 rounded-xl flex items-center justify-center">
                    {selectedFarm.vis_url
                      ? <img src={selectedFarm.vis_url} className="w-full h-full object-cover rounded-xl" />
                      : <p className="text-[9px] text-gray-600">GitHub Actions 実行後に表示</p>}
                  </div>
                </div>
                <div>
                  <p className="text-[9px] text-gray-500 mb-1">Sentinel-1 (レーダー)</p>
                  <div className="aspect-square bg-gray-800 rounded-xl flex items-center justify-center">
                    {selectedFarm.radar_url
                      ? <img src={selectedFarm.radar_url} className="w-full h-full object-cover rounded-xl" />
                      : <p className="text-[9px] text-gray-600">GitHub Actions 実行後に表示</p>}
                  </div>
                </div>
              </div>

              <div className="flex gap-4 mb-4">
                <div className="flex-1 bg-gray-800 rounded-xl p-3">
                  <p className="text-[9px] text-gray-500">NDVI</p>
                  <p className="text-2xl font-black" style={{ color: ndviToColor(selectedFarm.ndvi) }}>{selectedFarm.ndvi.toFixed(2)}</p>
                  <p className="text-[9px] text-gray-500">{ndviLabel(selectedFarm.ndvi)}</p>
                </div>
                <div className="flex-1 bg-gray-800 rounded-xl p-3">
                  <p className="text-[9px] text-gray-500">地表温度</p>
                  <p className="text-2xl font-black text-orange-400">{selectedFarm.temp}℃</p>
                  <p className="text-[9px] text-gray-500">Landsat 8/9</p>
                </div>
              </div>

              <div className="bg-green-900/20 border border-green-900/30 rounded-xl p-4 mb-4">
                <p className="text-[9px] text-green-400 font-bold mb-1">🤖 Gemini 2.0 AI 営農アドバイス</p>
                <p className="text-sm text-gray-300 leading-relaxed">{selectedFarm.ai}</p>
              </div>

              {/* SNSコメント */}
              <div>
                <h3 className="text-sm font-bold mb-3 flex items-center gap-2">
                  💬 農家コメント
                  <span className="bg-gray-700 text-xs px-2 py-0.5 rounded-full">{selectedFarm.comments.length}</span>
                </h3>
                {selectedFarm.comments.map(c => (
                  <div key={c.id} className="bg-gray-800 rounded-xl p-3 mb-2">
                    <div className="flex justify-between mb-1">
                      <span className="text-xs font-bold text-green-400">{c.user}</span>
                      <span className="text-[10px] text-gray-600">{c.created_at}</span>
                    </div>
                    <p className="text-xs text-gray-300">{c.text}</p>
                  </div>
                ))}
                <div className="flex gap-2 mt-3">
                  <input value={commentText} onChange={e => setCommentText(e.target.value)}
                    placeholder="コメントを入力..." 
                    className="flex-1 bg-gray-800 rounded-xl px-3 py-2 text-xs text-white placeholder-gray-600 border border-gray-700" />
                  <button className="bg-green-600 hover:bg-green-500 px-4 py-2 rounded-xl text-xs font-bold transition-colors"
                    onClick={() => setCommentText('')}>投稿</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// =============================================
// Globe.GL コンポーネント（CDN版）
// =============================================
const GlobeSection = ({ farms, onSelect }: { farms: FarmData[], onSelect: (f: FarmData) => void }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const globeRef = useRef<any>(null);

  useEffect(() => {
    // Globe.GL のダイナミックロード
    const script = document.createElement('script');
    script.src = 'https://unpkg.com/globe.gl';
    script.onload = () => {
      if (!containerRef.current || globeRef.current) return;
      const Globe = (window as any).Globe;
      
      globeRef.current = Globe({ animateIn: true })(containerRef.current)
        .globeImageUrl('//unpkg.com/three-globe/example/img/earth-dark.jpg')
        .bumpImageUrl('//unpkg.com/three-globe/example/img/earth-topology.png')
        .backgroundImageUrl('//unpkg.com/three-globe/example/img/night-sky.png')
        .width(containerRef.current.clientWidth)
        .height(containerRef.current.clientHeight)
        .pointsData(farms)
        .pointLat('lat')
        .pointLng('lon')
        .pointAltitude(0.02)
        .pointRadius((d: FarmData) => d.ndvi * 0.5 + 0.2)
        .pointColor((d: FarmData) => ndviToColor(d.ndvi))
        .pointLabel((d: FarmData) => `
          <div style="background:rgba(0,0,0,0.8);border:1px solid ${ndviToColor(d.ndvi)};border-radius:8px;padding:8px;font-family:monospace;font-size:11px;color:white;">
            <b>${d.name}</b><br/>
            NDVI: <span style="color:${ndviToColor(d.ndvi)}">${d.ndvi.toFixed(2)}</span><br/>
            温度: ${d.temp}℃
          </div>`)
        .onPointClick((d: FarmData) => onSelect(d))
        .pointOfView({ lat: 36.5, lng: 138, altitude: 1.5 });
    };
    document.head.appendChild(script);
    return () => { document.head.removeChild(script); };
  }, [farms, onSelect]);

  return (
    <div className="relative w-full" style={{ height: 'calc(100vh - 56px)' }}>
      <div ref={containerRef} className="w-full h-full" />
      <div className="absolute top-4 left-4 bg-gray-900/90 rounded-xl p-3 border border-gray-700 text-xs">
        <p className="font-bold text-green-400 mb-2">NDVI スケール</p>
        {[
          { label: '旺盛 (0.6+)', color: '#1a5c2e' },
          { label: '健全 (0.4-0.6)', color: '#3fa83f' },
          { label: '成長中 (0.2-0.4)', color: '#85c43b' },
          { label: '植生薄 (0.1-0.2)', color: '#c8c84e' },
          { label: '裸地 (0-0.1)', color: '#d4a84b' },
        ].map(i => (
          <div key={i.label} className="flex items-center gap-2 mb-1">
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: i.color }} />
            <span className="text-gray-400">{i.label}</span>
          </div>
        ))}
        <p className="text-gray-600 mt-2">点をクリックで詳細表示</p>
      </div>
    </div>
  );
};

export default App;
