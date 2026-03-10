"""
SATELLITE PRO - 拡張版バックエンド API
FastAPI + Google Earth Engine + Gemini 2.0 Flash

起動: uvicorn main:app --reload
Render.com デプロイ: requirements.txt と共にデプロイ
"""
import os
import ee
import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai

# =============================================
# 初期化
# =============================================
app = FastAPI(title="SATELLITE PRO API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では Cloudflare Pages URLに制限
    allow_methods=["*"],
    allow_headers=["*"],
)

# Earth Engine 認証（GitHub Secrets / Render ENV）
_EE_INITIALIZED = False
def init_ee():
    global _EE_INITIALIZED
    if _EE_INITIALIZED:
        return
    try:
        ee_json = os.getenv("EE_SERVICE_ACCOUNT_JSON")
        if ee_json:
            with open("/tmp/service_account.json", "w") as f:
                f.write(ee_json)
            credentials = ee.ServiceAccountCredentials(
                os.getenv("EE_SERVICE_ACCOUNT_EMAIL", ""),
                "/tmp/service_account.json"
            )
            ee.Initialize(credentials)
        else:
            ee.Initialize()  # ローカル開発時
        _EE_INITIALIZED = True
    except Exception as e:
        print(f"EE init warning: {e}")

# Gemini クライアント
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", ""))

# シンプルなインメモリキャッシュ（本番ではRedisを推奨）
_cache: dict = {}
CACHE_TTL_HOURS = 24  # Earth Engine: 24時間キャッシュ

# =============================================
# 47都道府県全座標
# =============================================
ALL_PREFECTURES = [
    {"id": "hokkaido",   "name": "北海道",  "lat": 43.0642, "lon": 141.3469},
    {"id": "aomori",     "name": "青森県",  "lat": 40.8244, "lon": 140.7400},
    {"id": "iwate",      "name": "岩手県",  "lat": 39.7036, "lon": 141.1527},
    {"id": "miyagi",     "name": "宮城県",  "lat": 38.2688, "lon": 140.8721},
    {"id": "akita",      "name": "秋田県",  "lat": 39.7186, "lon": 140.1024},
    {"id": "yamagata",   "name": "山形県",  "lat": 38.2404, "lon": 140.3633},
    {"id": "fukushima",  "name": "福島県",  "lat": 37.7500, "lon": 140.4677},
    {"id": "ibaraki",    "name": "茨城県",  "lat": 36.3418, "lon": 140.4469},
    {"id": "tochigi",    "name": "栃木県",  "lat": 36.5657, "lon": 139.8836},
    {"id": "gunma",      "name": "群馬県",  "lat": 36.3912, "lon": 139.0608},
    {"id": "saitama",    "name": "埼玉県",  "lat": 35.8575, "lon": 139.6488},
    {"id": "chiba",      "name": "千葉県",  "lat": 35.6050, "lon": 140.1233},
    {"id": "tokyo",      "name": "東京都",  "lat": 35.6762, "lon": 139.6503},
    {"id": "kanagawa",   "name": "神奈川県","lat": 35.4478, "lon": 139.6425},
    {"id": "niigata",    "name": "新潟県",  "lat": 37.9026, "lon": 139.0232},
    {"id": "toyama",     "name": "富山県",  "lat": 36.6953, "lon": 137.2113},
    {"id": "ishikawa",   "name": "石川県",  "lat": 36.5947, "lon": 136.6256},
    {"id": "fukui",      "name": "福井県",  "lat": 36.0652, "lon": 136.2216},
    {"id": "yamanashi",  "name": "山梨県",  "lat": 35.6642, "lon": 138.5688},
    {"id": "nagano",     "name": "長野県",  "lat": 36.6513, "lon": 138.1810},
    {"id": "gifu",       "name": "岐阜県",  "lat": 35.3912, "lon": 136.7222},
    {"id": "shizuoka",   "name": "静岡県",  "lat": 34.9769, "lon": 138.3831},
    {"id": "aichi",      "name": "愛知県",  "lat": 35.1802, "lon": 136.9066},
    {"id": "mie",        "name": "三重県",  "lat": 34.7303, "lon": 136.5086},
    {"id": "shiga",      "name": "滋賀県",  "lat": 35.0045, "lon": 135.8686},
    {"id": "kyoto",      "name": "京都府",  "lat": 35.0211, "lon": 135.7556},
    {"id": "osaka",      "name": "大阪府",  "lat": 34.6937, "lon": 135.5023},
    {"id": "hyogo",      "name": "兵庫県",  "lat": 34.6913, "lon": 135.1830},
    {"id": "nara",       "name": "奈良県",  "lat": 34.6851, "lon": 135.8325},
    {"id": "wakayama",   "name": "和歌山県","lat": 34.2260, "lon": 135.1675},
    {"id": "tottori",    "name": "鳥取県",  "lat": 35.5036, "lon": 134.2381},
    {"id": "shimane",    "name": "島根県",  "lat": 35.4723, "lon": 133.0505},
    {"id": "okayama",    "name": "岡山県",  "lat": 34.6618, "lon": 133.9344},
    {"id": "hiroshima",  "name": "広島県",  "lat": 34.3853, "lon": 132.4553},
    {"id": "yamaguchi",  "name": "山口県",  "lat": 34.1861, "lon": 131.4706},
    {"id": "tokushima",  "name": "徳島県",  "lat": 34.0658, "lon": 134.5593},
    {"id": "kagawa",     "name": "香川県",  "lat": 34.3401, "lon": 134.0434},
    {"id": "ehime",      "name": "愛媛県",  "lat": 33.8417, "lon": 132.7657},
    {"id": "kochi",      "name": "高知県",  "lat": 33.5597, "lon": 133.5311},
    {"id": "fukuoka",    "name": "福岡県",  "lat": 33.6064, "lon": 130.4181},
    {"id": "saga",       "name": "佐賀県",  "lat": 33.2494, "lon": 130.2988},
    {"id": "nagasaki",   "name": "長崎県",  "lat": 32.7448, "lon": 129.8737},
    {"id": "kumamoto",   "name": "熊本県",  "lat": 32.7898, "lon": 130.7417},
    {"id": "oita",       "name": "大分県",  "lat": 33.2382, "lon": 131.6126},
    {"id": "miyazaki",   "name": "宮崎県",  "lat": 31.9111, "lon": 131.4239},
    {"id": "kagoshima",  "name": "鹿児島県","lat": 31.5602, "lon": 130.5580},
    {"id": "okinawa",    "name": "沖縄県",  "lat": 26.2124, "lon": 127.6809},
]

# =============================================
# データモデル
# =============================================
class FarmCommentRequest(BaseModel):
    farm_id: str
    user_name: str
    text: str

class BBoxRequest(BaseModel):
    lat: float
    lon: float
    radius_m: int = 3000

# =============================================
# ユーティリティ
# =============================================
def cache_key(prefix: str, **kwargs) -> str:
    raw = json.dumps(kwargs, sort_keys=True)
    return f"{prefix}_{hashlib.md5(raw.encode()).hexdigest()[:8]}"

def cache_get(key: str) -> Optional[dict]:
    if key in _cache:
        val, ts = _cache[key]
        if datetime.now() - ts < timedelta(hours=CACHE_TTL_HOURS):
            return val
        del _cache[key]
    return None

def cache_set(key: str, val: dict):
    _cache[key] = (val, datetime.now())

# =============================================
# Earth Engine ヘルパー
# =============================================
def get_ndvi_data(lat: float, lon: float) -> dict:
    """Landsat 8/9 から NDVI・地表温度を取得"""
    key = cache_key("ndvi", lat=round(lat, 2), lon=round(lon, 2))
    cached = cache_get(key)
    if cached:
        return cached

    init_ee()
    try:
        roi = ee.Geometry.Point([lon, lat]).buffer(3000).bounds()
        end_date = datetime.now()
        start_date = end_date - timedelta(days=60)

        # Landsat 8/9
        ls = (ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
              .filterBounds(roi)
              .filterDate(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
              .sort('CLOUD_COVER')
              .first())

        ls_stats = ls.reduceRegion(ee.Reducer.mean(), roi, 30).getInfo()
        b4 = ls_stats.get('SR_B4', 0) or 0
        b5 = ls_stats.get('SR_B5', 0) or 0
        ndvi = (b5 - b4) / (b5 + b4) if (b5 + b4) > 0 else 0
        temp_k = ls_stats.get('ST_B10', 0) or 0
        temp_c = round(temp_k * 0.00341802 + 149.0 - 273.15, 1) if temp_k > 0 else 20.0

        vis_url = ls.getThumbURL({
            'bands': ['SR_B4', 'SR_B3', 'SR_B2'],
            'min': 0, 'max': 20000,
            'dimensions': 512, 'format': 'png'
        })

        # Sentinel-1 SAR
        s1 = (ee.ImageCollection('COPERNICUS/S1_GRD')
              .filterBounds(roi)
              .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
              .sort('system:time_start', False)
              .first())

        radar_url = s1.getThumbURL({
            'bands': ['VV'], 'min': -25, 'max': 0,
            'dimensions': 512, 'format': 'png'
        })

        date_str = ls.date().format('YYYY年MM月DD日').getInfo()

        result = {
            "ndvi": round(ndvi, 3),
            "temp": temp_c,
            "vis_url": vis_url,
            "radar_url": radar_url,
            "date": date_str,
            "source": "Landsat 8/9 + Sentinel-1",
        }
        cache_set(key, result)
        return result

    except Exception as e:
        return {
            "ndvi": 0.45,  # フォールバック値
            "temp": 20.0,
            "vis_url": "",
            "radar_url": "",
            "date": datetime.now().strftime('%Y年%m月%d日'),
            "source": "fallback",
            "error": str(e)
        }

def get_ai_advice(ndvi: float, temp: float, pref_name: str) -> str:
    """Gemini 2.0 Flash で営農アドバイス生成（キャッシュあり）"""
    key = cache_key("ai", ndvi=round(ndvi, 1), temp=round(temp, 0), pref=pref_name)
    cached = cache_get(key)
    if cached:
        return cached.get("text", "")
    try:
        prompt = (
            f"あなたは日本の農業専門家AIです。以下の衛星データを元に、{pref_name}の農家向けに"
            f"具体的で実用的な営農アドバイスを2〜3文で生成してください。"
            f"NDVI値: {ndvi:.2f}（0=植生なし, 1=旺盛な植生）, 地表温度: {temp:.1f}℃。"
            f"専門用語は避け、農家が即実践できる内容にしてください。"
        )
        response = gemini_client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt
        )
        text = response.text.strip()
        cache_set(key, {"text": text})
        return text
    except Exception as e:
        return f"NDVI {ndvi:.2f}は{'良好' if ndvi > 0.4 else '要注意'}な水準です。定期的な圃場確認をお勧めします。"

# =============================================
# APIエンドポイント
# =============================================
@app.get("/")
def root():
    return {"service": "SATELLITE PRO API", "version": "2.0.0", "status": "ok"}

@app.get("/api/prefectures")
def get_all_prefectures():
    """47都道府県リスト取得"""
    return {"prefectures": ALL_PREFECTURES}

@app.get("/api/ndvi/{pref_id}")
def get_prefecture_ndvi(pref_id: str):
    """特定都道府県のNDVI・衛星データ取得"""
    pref = next((p for p in ALL_PREFECTURES if p["id"] == pref_id), None)
    if not pref:
        raise HTTPException(status_code=404, detail=f"Prefecture '{pref_id}' not found")
    
    satellite_data = get_ndvi_data(pref["lat"], pref["lon"])
    ai_advice = get_ai_advice(satellite_data["ndvi"], satellite_data["temp"], pref["name"])
    
    return {
        **pref,
        **satellite_data,
        "ai": ai_advice,
        "bbox": {
            "west": pref["lon"] - 0.027,
            "east": pref["lon"] + 0.027,
            "south": pref["lat"] - 0.027,
            "north": pref["lat"] + 0.027,
        }
    }

@app.post("/api/batch/update")
def batch_update_all():
    """
    全47都道府県のデータ一括更新（GitHub Actions で毎日実行）
    結果を Supabase に保存する処理を追加予定
    """
    results = []
    for pref in ALL_PREFECTURES:
        try:
            satellite_data = get_ndvi_data(pref["lat"], pref["lon"])
            ai_advice = get_ai_advice(satellite_data["ndvi"], satellite_data["temp"], pref["name"])
            results.append({**pref, **satellite_data, "ai": ai_advice})
            time.sleep(3)  # EE API レート制限対策
        except Exception as e:
            results.append({**pref, "error": str(e)})
    
    # 結果を JSON ファイルに保存（既存フローとの後方互換）
    output = {"japan": results, "updated_at": datetime.now().isoformat()}
    with open("frontend/src/data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    return {"success": True, "count": len(results), "updated_at": output["updated_at"]}

@app.post("/api/photo/analyze")
async def analyze_photo(file: UploadFile = File(...)):
    """
    写真アップロード → Exif位置情報取得 → 最近傍農地マッチング
    
    実装ノート:
    - フロントエンドで extractExifCoords() を先行実装済み
    - このエンドポイントはサーバーサイドExif解析のフォールバック
    """
    try:
        contents = await file.read()
        
        # exifread ライブラリでExif解析（pip install exifread）
        import io
        try:
            import exifread
            tags = exifread.process_file(io.BytesIO(contents), stop_tag='GPS')
            
            lat_ref = str(tags.get('GPS GPSLatitudeRef', 'N'))
            lon_ref = str(tags.get('GPS GPSLongitudeRef', 'E'))
            
            def to_decimal(tag):
                if not tag:
                    return None
                vals = tag.values
                return (float(vals[0].num)/float(vals[0].den) +
                        float(vals[1].num)/float(vals[1].den)/60 +
                        float(vals[2].num)/float(vals[2].den)/3600)
            
            lat = to_decimal(tags.get('GPS GPSLatitude'))
            lon = to_decimal(tags.get('GPS GPSLongitude'))
            
            if lat and lon:
                if lat_ref == 'S':
                    lat = -lat
                if lon_ref == 'W':
                    lon = -lon
                
                # 最近傍農地マッチング
                nearest = min(ALL_PREFECTURES,
                    key=lambda p: (p['lat']-lat)**2 + (p['lon']-lon)**2)
                
                return {
                    "success": True,
                    "lat": lat,
                    "lon": lon,
                    "matched_prefecture": nearest,
                    "distance_km": round(((nearest['lat']-lat)**2 + (nearest['lon']-lon)**2)**0.5 * 111, 1)
                }
        except ImportError:
            pass
        
        return {"success": False, "error": "Exif情報が見つかりません。位置情報をONにして撮影してください。"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/bbox")
def get_bbox_ndvi(lat: float, lon: float, radius_m: int = 3000):
    """
    任意座標のBBoxを指定してNDVI取得
    フロントエンドの写真Exif座標から呼び出し
    """
    data = get_ndvi_data(lat, lon)
    return {
        "lat": lat,
        "lon": lon,
        "radius_m": radius_m,
        "bbox": {
            "west": lon - radius_m/111000,
            "east": lon + radius_m/111000,
            "south": lat - radius_m/111000,
            "north": lat + radius_m/111000,
        },
        **data
    }

@app.get("/api/cache/stats")
def cache_stats():
    """キャッシュ統計（運用監視用）"""
    return {
        "total_entries": len(_cache),
        "entries": [{"key": k, "age_minutes": round((datetime.now()-v[1]).seconds/60)} 
                   for k, v in _cache.items()]
    }

# =============================================
# Supabase 連携（将来実装のスタブ）
# =============================================
# from supabase import create_client
# SUPABASE_URL = os.getenv("SUPABASE_URL")
# SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
# supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
#
# async def save_to_supabase(farm_id: str, ndvi_data: dict):
#     supabase.table("ndvi_records").insert({
#         "farm_id": farm_id,
#         "ndvi": ndvi_data["ndvi"],
#         "temp": ndvi_data["temp"],
#         "vis_url": ndvi_data["vis_url"],
#         "radar_url": ndvi_data["radar_url"],
#         "captured_at": datetime.now().isoformat()
#     }).execute()
