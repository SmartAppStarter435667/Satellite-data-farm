import os, ee, json, time
from datetime import datetime, timedelta
from google import genai

# 1. 認証
EE_JSON = os.getenv("EE_SERVICE_ACCOUNT_JSON")
with open("service_account.json", "w") as f: f.write(EE_JSON)
ee.Initialize(ee.ServiceAccountCredentials("your-account", "service_account.json"))
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# 47都道府県 + 海外代表地点
LOCATIONS = {
    "japan": [
        {"id": "hokkaido", "name": "北海道", "lat": 43.06, "lon": 141.35},
        {"id": "aomori", "name": "青森県", "lat": 40.82, "lon": 140.74},
        # ... (中略：実際にはここに47個すべて入りますが、コードを短くするため代表例を記載)
        {"id": "saga", "name": "佐賀県", "lat": 33.26, "lon": 130.30},
        {"id": "okinawa", "name": "沖縄県", "lat": 26.21, "lon": 127.68}
    ],
    "overseas": [
        {"id": "ny", "name": "ニューヨーク", "lat": 40.71, "lon": -74.00},
        {"id": "paris", "name": "パリ", "lat": 48.85, "lon": 2.35},
        {"id": "sydney", "name": "シドニー", "lat": -33.86, "lon": 151.20}
    ]
}

def get_landsat_data(lat, lon):
    try:
        roi = ee.Geometry.Point([lon, lat]).buffer(5000).bounds()
        # Landsat 8/9 Collection 2 Level 2 を使用
        img = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2") \
            .filterBounds(roi) \
            .filterDate(datetime.now() - timedelta(days=120), datetime.now()) \
            .sort('CLOUD_COVER') \
            .first()

        # 画像URL (Landsatのバンド: B4=Red, B3=Green, B2=Blue)
        img_url = img.getThumbURL({'bands':['SR_B4','SR_B3','SR_B2'], 'min':0, 'max':20000, 'dimensions':600, 'format':'png'})
        
        # 数値取得
        stats = img.reduceRegion(ee.Reducer.mean(), roi, 30).getInfo()
        
        # 指標計算 (Landsat 8: B5=NIR, B4=Red, B3=Green)
        ndvi = (stats['SR_B5'] - stats['SR_B4']) / (stats['SR_B5'] + stats['SR_B4'])
        ndwi = (stats['SR_B3'] - stats['SR_B5']) / (stats['SR_B3'] + stats['SR_B5'])
        temp_k = stats.get('ST_B10', 0)
        lst_c = (temp_k * 0.00341802 + 149.0) - 273.15 if temp_k else 0
        cloud = img.get('CLOUD_COVER').getInfo()

        # AI分析 (お天気キャスター風)
        ai_text = "衛星データの解析に時間がかかっています。"
        for _ in range(3): # 3回リトライ
            try:
                prompt = f"地表温度{lst_c:.1f}度、植生指数{ndvi:.2f}。この地域の農業・環境状況を、お天気お姉さんのように親しみやすく1行で伝えて。"
                response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
                ai_text = response.text
                break
            except: time.sleep(15)

        return {
            "img": img_url, "ndvi": round(ndvi, 2), "ndwi": round(ndwi, 2),
            "temp": round(lst_c, 1), "cloud": round(cloud, 1), "ai": ai_text,
            "date": img.date().format('YYYY-MM-DD').getInfo()
        }
    except: return None

def main():
    final_data = {"japan": [], "overseas": []}
    for category in ["japan", "overseas"]:
        for loc in LOCATIONS[category]:
            print(f"Fetching {loc['name']}...")
            res = get_landsat_data(loc['lat'], loc['lon'])
            if res: final_data[category].append({**loc, **res})
            time.sleep(10) # 47件あるので制限回避のため長めに待機

    os.makedirs("frontend/src", exist_ok=True)
    with open("frontend/src/data.json", "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__": main()
