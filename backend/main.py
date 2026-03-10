"""
SATELLITE PRO - FastAPI エントリポイント（リファクタリング版）
ルーターとサービスを分離した保守しやすい構成

ディレクトリ構成:
  backend/
  ├── main.py               ← このファイル
  ├── routers/
  │   ├── ndvi.py           (既存 backend_main.py から移行)
  │   ├── photos.py
  │   └── sns.py            ← 新規
  └── services/
      ├── earth_engine.py
      ├── gemini.py
      ├── mongo.py          ← 新規
      └── neo4j_service.py  ← 新規
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ルーターインポート
from routers.sns import router as sns_router

# =============================================
# アプリ初期化
# =============================================
app = FastAPI(
    title="SATELLITE PRO API",
    version="2.1.0",
    description="次世代農地監視SaaS バックエンドAPI",
)

# CORS（本番では Cloudflare Pages の URL に絞る）
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "*"  # 開発中は全許可、本番では Cloudflare Pages URLを設定
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ルーター登録
app.include_router(sns_router)

# =============================================
# 既存エンドポイント（backend_main.py から移行）
# ※ backend_main.py の内容をそのまま下に追加してください
# =============================================
import ee, json, time, hashlib
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, UploadFile, File
from pydantic import BaseModel
from google import genai

# --- 以下 backend_main.py の内容をコピー ---
_EE_INITIALIZED = False
def init_ee():
    global _EE_INITIALIZED
    if _EE_INITIALIZED: return
    try:
        ee_json = os.getenv("EE_SERVICE_ACCOUNT_JSON")
        if ee_json:
            with open("/tmp/service_account.json", "w") as f: f.write(ee_json)
            ee.Initialize(ee.ServiceAccountCredentials(
                os.getenv("EE_SERVICE_ACCOUNT_EMAIL", ""), "/tmp/service_account.json"))
        else:
            ee.Initialize()
        _EE_INITIALIZED = True
    except Exception as e:
        print(f"EE init warning: {e}")

gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", ""))
_cache: dict = {}
CACHE_TTL_HOURS = 24

ALL_PREFECTURES = [
    {"id": "hokkaido","name": "北海道","lat": 43.0642,"lon": 141.3469},
    {"id": "aomori","name": "青森県","lat": 40.8244,"lon": 140.7400},
    {"id": "iwate","name": "岩手県","lat": 39.7036,"lon": 141.1527},
    {"id": "miyagi","name": "宮城県","lat": 38.2688,"lon": 140.8721},
    {"id": "akita","name": "秋田県","lat": 39.7186,"lon": 140.1024},
    {"id": "yamagata","name": "山形県","lat": 38.2404,"lon": 140.3633},
    {"id": "fukushima","name": "福島県","lat": 37.7500,"lon": 140.4677},
    {"id": "ibaraki","name": "茨城県","lat": 36.3418,"lon": 140.4469},
    {"id": "tochigi","name": "栃木県","lat": 36.5657,"lon": 139.8836},
    {"id": "gunma","name": "群馬県","lat": 36.3912,"lon": 139.0608},
    {"id": "saitama","name": "埼玉県","lat": 35.8575,"lon": 139.6488},
    {"id": "chiba","name": "千葉県","lat": 35.6050,"lon": 140.1233},
    {"id": "tokyo","name": "東京都","lat": 35.6762,"lon": 139.6503},
    {"id": "kanagawa","name": "神奈川県","lat": 35.4478,"lon": 139.6425},
    {"id": "niigata","name": "新潟県","lat": 37.9026,"lon": 139.0232},
    {"id": "toyama","name": "富山県","lat": 36.6953,"lon": 137.2113},
    {"id": "ishikawa","name": "石川県","lat": 36.5947,"lon": 136.6256},
    {"id": "fukui","name": "福井県","lat": 36.0652,"lon": 136.2216},
    {"id": "yamanashi","name": "山梨県","lat": 35.6642,"lon": 138.5688},
    {"id": "nagano","name": "長野県","lat": 36.6513,"lon": 138.1810},
    {"id": "gifu","name": "岐阜県","lat": 35.3912,"lon": 136.7222},
    {"id": "shizuoka","name": "静岡県","lat": 34.9769,"lon": 138.3831},
    {"id": "aichi","name": "愛知県","lat": 35.1802,"lon": 136.9066},
    {"id": "mie","name": "三重県","lat": 34.7303,"lon": 136.5086},
    {"id": "shiga","name": "滋賀県","lat": 35.0045,"lon": 135.8686},
    {"id": "kyoto","name": "京都府","lat": 35.0211,"lon": 135.7556},
    {"id": "osaka","name": "大阪府","lat": 34.6937,"lon": 135.5023},
    {"id": "hyogo","name": "兵庫県","lat": 34.6913,"lon": 135.1830},
    {"id": "nara","name": "奈良県","lat": 34.6851,"lon": 135.8325},
    {"id": "wakayama","name": "和歌山県","lat": 34.2260,"lon": 135.1675},
    {"id": "tottori","name": "鳥取県","lat": 35.5036,"lon": 134.2381},
    {"id": "shimane","name": "島根県","lat": 35.4723,"lon": 133.0505},
    {"id": "okayama","name": "岡山県","lat": 34.6618,"lon": 133.9344},
    {"id": "hiroshima","name": "広島県","lat": 34.3853,"lon": 132.4553},
    {"id": "yamaguchi","name": "山口県","lat": 34.1861,"lon": 131.4706},
    {"id": "tokushima","name": "徳島県","lat": 34.0658,"lon": 134.5593},
    {"id": "kagawa","name": "香川県","lat": 34.3401,"lon": 134.0434},
    {"id": "ehime","name": "愛媛県","lat": 33.8417,"lon": 132.7657},
    {"id": "kochi","name": "高知県","lat": 33.5597,"lon": 133.5311},
    {"id": "fukuoka","name": "福岡県","lat": 33.6064,"lon": 130.4181},
    {"id": "saga","name": "佐賀県","lat": 33.2494,"lon": 130.2988},
    {"id": "nagasaki","name": "長崎県","lat": 32.7448,"lon": 129.8737},
    {"id": "kumamoto","name": "熊本県","lat": 32.7898,"lon": 130.7417},
    {"id": "oita","name": "大分県","lat": 33.2382,"lon": 131.6126},
    {"id": "miyazaki","name": "宮崎県","lat": 31.9111,"lon": 131.4239},
    {"id": "kagoshima","name": "鹿児島県","lat": 31.5602,"lon": 130.5580},
    {"id": "okinawa","name": "沖縄県","lat": 26.2124,"lon": 127.6809},
]

def cache_key(prefix, **kwargs):
    return f"{prefix}_{hashlib.md5(json.dumps(kwargs,sort_keys=True).encode()).hexdigest()[:8]}"
def cache_get(key):
    if key in _cache:
        val, ts = _cache[key]
        if datetime.now() - ts < timedelta(hours=CACHE_TTL_HOURS): return val
        del _cache[key]
    return None
def cache_set(key, val): _cache[key] = (val, datetime.now())

def get_ndvi_data(lat, lon):
    key = cache_key("ndvi", lat=round(lat,2), lon=round(lon,2))
    cached = cache_get(key)
    if cached: return cached
    init_ee()
    try:
        roi = ee.Geometry.Point([lon, lat]).buffer(3000).bounds()
        end_date = datetime.now(); start_date = end_date - timedelta(days=60)
        ls = (ee.ImageCollection("LANDSAT/LC08/C02/T1_L2").filterBounds(roi)
              .filterDate(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
              .sort('CLOUD_COVER').first())
        ls_stats = ls.reduceRegion(ee.Reducer.mean(), roi, 30).getInfo()
        b4, b5 = ls_stats.get('SR_B4',0) or 0, ls_stats.get('SR_B5',0) or 0
        ndvi = (b5-b4)/(b5+b4) if (b5+b4) > 0 else 0
        temp_k = ls_stats.get('ST_B10',0) or 0
        temp_c = round(temp_k*0.00341802+149.0-273.15,1) if temp_k > 0 else 20.0
        vis_url = ls.getThumbURL({'bands':['SR_B4','SR_B3','SR_B2'],'min':0,'max':20000,'dimensions':512,'format':'png'})
        s1 = (ee.ImageCollection('COPERNICUS/S1_GRD').filterBounds(roi)
              .filter(ee.Filter.listContains('transmitterReceiverPolarisation','VV'))
              .sort('system:time_start',False).first())
        radar_url = s1.getThumbURL({'bands':['VV'],'min':-25,'max':0,'dimensions':512,'format':'png'})
        result = {"ndvi":round(ndvi,3),"temp":temp_c,"vis_url":vis_url,"radar_url":radar_url,
                  "date":ls.date().format('YYYY年MM月DD日').getInfo(),"source":"Landsat 8/9 + Sentinel-1"}
        cache_set(key, result); return result
    except Exception as e:
        return {"ndvi":0.45,"temp":20.0,"vis_url":"","radar_url":"",
                "date":datetime.now().strftime('%Y年%m月%d日'),"source":"fallback","error":str(e)}

def get_ai_advice(ndvi, temp, pref_name):
    key = cache_key("ai", ndvi=round(ndvi,1), temp=round(temp,0), pref=pref_name)
    cached = cache_get(key)
    if cached: return cached.get("text","")
    try:
        prompt = (f"あなたは日本の農業専門家AIです。{pref_name}の農家向けに"
                  f"具体的で実用的な営農アドバイスを2〜3文で。"
                  f"NDVI:{ndvi:.2f}, 地表温度:{temp:.1f}℃。専門用語は避けてください。")
        text = gemini_client.models.generate_content(model='gemini-2.0-flash',contents=prompt).text.strip()
        cache_set(key, {"text": text}); return text
    except: return f"NDVI {ndvi:.2f}は{'良好' if ndvi>0.4 else '要注意'}な水準です。定期的な圃場確認を。"

# =============================================
# エンドポイント
# =============================================
@app.get("/")
def root():
    return {"service": "SATELLITE PRO API", "version": "2.1.0", "status": "ok"}

@app.get("/api/prefectures")
def get_all_prefectures():
    return {"prefectures": ALL_PREFECTURES}

@app.get("/api/ndvi/{pref_id}")
def get_prefecture_ndvi(pref_id: str):
    pref = next((p for p in ALL_PREFECTURES if p["id"] == pref_id), None)
    if not pref: raise HTTPException(404, f"Prefecture '{pref_id}' not found")
    sat = get_ndvi_data(pref["lat"], pref["lon"])
    ai = get_ai_advice(sat["ndvi"], sat.get("temp", 20.0), pref["name"])
    return {**pref, **sat, "ai": ai,
            "bbox": {"west": pref["lon"]-0.027, "east": pref["lon"]+0.027,
                     "south": pref["lat"]-0.027, "north": pref["lat"]+0.027}}

@app.get("/api/bbox")
def get_bbox_ndvi(lat: float, lon: float, radius_m: int = 3000):
    data = get_ndvi_data(lat, lon)
    return {"lat":lat,"lon":lon,"radius_m":radius_m,
            "bbox":{"west":lon-radius_m/111000,"east":lon+radius_m/111000,
                    "south":lat-radius_m/111000,"north":lat+radius_m/111000},**data}

@app.post("/api/photo/analyze")
async def analyze_photo(file: UploadFile = File(...)):
    try:
        import io, exifread
        contents = await file.read()
        tags = exifread.process_file(io.BytesIO(contents), stop_tag='GPS')
        lat_ref = str(tags.get('GPS GPSLatitudeRef','N'))
        lon_ref = str(tags.get('GPS GPSLongitudeRef','E'))
        def to_dec(tag):
            if not tag: return None
            v = tag.values
            return float(v[0].num)/float(v[0].den)+float(v[1].num)/float(v[1].den)/60+float(v[2].num)/float(v[2].den)/3600
        lat, lon = to_dec(tags.get('GPS GPSLatitude')), to_dec(tags.get('GPS GPSLongitude'))
        if lat and lon:
            if lat_ref == 'S': lat = -lat
            if lon_ref == 'W': lon = -lon
            nearest = min(ALL_PREFECTURES, key=lambda p: (p['lat']-lat)**2+(p['lon']-lon)**2)
            return {"success":True,"lat":lat,"lon":lon,"matched_prefecture":nearest,
                    "distance_km":round(((nearest['lat']-lat)**2+(nearest['lon']-lon)**2)**0.5*111,1)}
        return {"success":False,"error":"Exif位置情報なし"}
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/cache/stats")
def cache_stats():
    return {"total_entries":len(_cache),
            "entries":[{"key":k,"age_minutes":round((datetime.now()-v[1]).seconds/60)} for k,v in _cache.items()]}
