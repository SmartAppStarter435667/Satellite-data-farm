"""
SATELLITE PRO - 拡張版 data_processor.py
47都道府県対応 + Supabase書き込み + キャッシュ戦略

GitHub Actions で毎日実行:
  - Google Earth Engine でNDVI・温度・衛星画像取得
  - Gemini 2.0 Flash でAI営農アドバイス生成
  - Supabase の prefecture_cache テーブルに保存
  - 後方互換のため frontend/src/data.json にも書き出し
"""
import os, ee, json, time, hashlib
from datetime import datetime, timedelta
from google import genai

# =============================================
# 認証設定
# =============================================
EE_JSON = os.getenv("EE_SERVICE_ACCOUNT_JSON")
EE_EMAIL = os.getenv("EE_SERVICE_ACCOUNT_EMAIL", "your-service-account@project.iam.gserviceaccount.com")

if EE_JSON:
    with open("service_account.json", "w") as f:
        f.write(EE_JSON)
    ee.Initialize(ee.ServiceAccountCredentials(EE_EMAIL, "service_account.json"))
else:
    ee.Initialize()  # ローカル開発時（gcloud auth application-default login 済み）

gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Supabase（オプション）
try:
    from supabase import create_client
    supabase = create_client(
        os.getenv("SUPABASE_URL", ""),
        os.getenv("SUPABASE_SERVICE_KEY", "")
    )
    SUPABASE_AVAILABLE = bool(os.getenv("SUPABASE_URL"))
except ImportError:
    SUPABASE_AVAILABLE = False
    print("Supabase not installed. JSON only mode.")

# =============================================
# 47都道府県座標
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
# コアロジック
# =============================================
def get_satellite_data(lat: float, lon: float) -> dict:
    """Landsat 8/9 + Sentinel-1 からデータ取得"""
    roi = ee.Geometry.Point([lon, lat]).buffer(3000).bounds()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=60)

    # Landsat 8/9（雲量最小を選択）
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
    temp_c = round(temp_k * 0.00341802 + 149.0 - 273.15, 1) if temp_k > 0 else None

    vis_url = ls.getThumbURL({
        'bands': ['SR_B4', 'SR_B3', 'SR_B2'],
        'min': 0, 'max': 20000,
        'dimensions': 512, 'format': 'png'
    })

    # Sentinel-1 SAR（雲貫通・梅雨対応）
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

    return {
        "ndvi": round(ndvi, 3),
        "temp": temp_c,
        "vis_url": vis_url,
        "radar_url": radar_url,
        "date": date_str,
    }


def get_ai_advice(ndvi: float, temp: float | None, pref_name: str) -> str:
    """Gemini 2.0 Flash でAIアドバイス生成"""
    temp_str = f"{temp:.1f}℃" if temp else "不明"
    prompt = (
        f"あなたは日本の農業専門家AIです。以下の衛星データを元に、{pref_name}の農家向けに"
        f"具体的で実用的な営農アドバイスを2〜3文で生成してください。"
        f"NDVI値: {ndvi:.2f}（0=植生なし, 1=旺盛な植生）, 地表温度: {temp_str}。"
        f"専門用語は避け、農家が即実践できる内容にしてください。"
    )
    try:
        response = gemini_client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        print(f"  Gemini error: {e}")
        status = "良好" if ndvi > 0.4 else "低め"
        return f"NDVI {ndvi:.2f}は{status}な水準です。継続的な圃場観察をお勧めします。"


def save_to_supabase(pref_id: str, pref_name: str, lat: float, lon: float, data: dict):
    """Supabase の prefecture_cache に保存"""
    if not SUPABASE_AVAILABLE:
        return
    try:
        supabase.table("prefecture_cache").upsert({
            "prefecture_id": pref_id,
            "prefecture_name": pref_name,
            "lat": lat,
            "lon": lon,
            "ndvi": data.get("ndvi"),
            "temp_celsius": data.get("temp"),
            "vis_url": data.get("vis_url"),
            "radar_url": data.get("radar_url"),
            "ai_advice": data.get("ai"),
            "satellite_date": data.get("date"),
            "updated_at": datetime.now().isoformat()
        }).execute()
        print(f"  ✅ Supabase保存完了")
    except Exception as e:
        print(f"  ⚠️ Supabase保存失敗: {e}")


# =============================================
# メイン処理
# =============================================
def main():
    print(f"\n{'='*50}")
    print(f"SATELLITE PRO - データ更新開始")
    print(f"日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"対象: {len(ALL_PREFECTURES)}都道府県")
    print(f"{'='*50}\n")

    results = {"japan": [], "updated_at": datetime.now().isoformat()}
    success_count = 0

    for i, pref in enumerate(ALL_PREFECTURES):
        print(f"[{i+1:02d}/{len(ALL_PREFECTURES)}] {pref['name']} ({pref['id']})...")
        
        try:
            # 衛星データ取得
            sat_data = get_satellite_data(pref["lat"], pref["lon"])
            print(f"  NDVI: {sat_data['ndvi']:.3f}, 温度: {sat_data['temp']}℃")

            # AIアドバイス生成（NDVIが前回から0.05以上変化した場合のみ生成推奨）
            ai_text = get_ai_advice(sat_data["ndvi"], sat_data.get("temp"), pref["name"])
            
            record = {
                **pref,
                **sat_data,
                "ai": ai_text,
                "images": {
                    "visible": sat_data["vis_url"],
                    "radar": sat_data["radar_url"],
                },
                "metrics": {
                    "ndvi": sat_data["ndvi"],
                    "temp": sat_data.get("temp", 0),
                    "update": datetime.now().strftime('%Y-%m-%d'),
                }
            }
            results["japan"].append(record)
            
            # Supabase保存
            save_to_supabase(pref["id"], pref["name"], pref["lat"], pref["lon"], {
                **sat_data, "ai": ai_text
            })

            success_count += 1
            time.sleep(4)  # EE APIレート制限対策（推奨: 3〜5秒）

        except Exception as e:
            print(f"  ❌ エラー: {e}")
            # エラー時はフォールバック値で続行
            results["japan"].append({
                **pref,
                "ndvi": 0.0, "temp": None,
                "vis_url": "", "radar_url": "",
                "ai": "データ取得中にエラーが発生しました。次回の更新をお待ちください。",
                "date": datetime.now().strftime('%Y年%m月%d日'),
                "images": {"visible": "", "radar": ""},
                "metrics": {"ndvi": 0, "temp": 0, "update": datetime.now().strftime('%Y-%m-%d')},
                "error": str(e)
            })

    # JSON書き出し（後方互換）
    os.makedirs("frontend/src", exist_ok=True)
    with open("frontend/src/data.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*50}")
    print(f"完了: {success_count}/{len(ALL_PREFECTURES)} 成功")
    print(f"JSON書き出し: frontend/src/data.json")
    if SUPABASE_AVAILABLE:
        print(f"Supabase: prefecture_cache 更新完了")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
