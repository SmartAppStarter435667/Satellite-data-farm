import os, ee, json, time
from datetime import datetime, timedelta

# 認証設定
EE_JSON = os.getenv("EE_SERVICE_ACCOUNT_JSON")
with open("service_account.json", "w") as f: f.write(EE_JSON)
ee.Initialize(ee.ServiceAccountCredentials("your-account", "service_account.json"))

# 47都道府県の代表地点 (サンプルとして3件、実際は47件記述)
PREFECTURES = [
    {"id": "hokkaido", "name": "北海道", "lat": 43.06, "lon": 141.35},
    {"id": "saga", "name": "佐賀県", "lat": 33.26, "lon": 130.30},
    {"id": "tokyo", "name": "東京都", "lat": 35.68, "lon": 139.69},
    # ... ここに残りの都道府県を追加
]

def get_satellite_info(lat, lon):
    try:
        roi = ee.Geometry.Point([lon, lat]).buffer(10000).bounds()
        # 期間を広げ(90日)、雲が少ない画像をソートして1番良いものを採用
        img = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
            .filterBounds(roi) \
            .filterDate(datetime.now() - timedelta(days=90), datetime.now()) \
            .sort('CLOUDY_PIXEL_PERCENTAGE') \
            .first()

        # 画像URL生成 (スケーリング max: 4000 で暗さを解消)
        url = img.select(['B4', 'B3', 'B2']).getThumbURL({
            'min': 0, 'max': 4000, 'dimensions': 600, 'format': 'png'
        })
        
        # NDVI計算
        ndvi = img.normalizedDifference(['B8', 'B4']).reduceRegion(ee.Reducer.mean(), roi, 30).getInfo().get('NDVI', 0)
        
        return {"img": url, "ndvi": round(ndvi, 3), "date": img.date().format('YYYY-MM-DD').getInfo()}
    except:
        return None

def main():
    results = []
    for pref in PREFECTURES:
        print(f"Fetching {pref['name']}...")
        data = get_satellite_info(pref['lat'], pref['lon'])
        if data:
            results.append({**pref, **data})
        time.sleep(1) # API負荷軽減

    # Reactが読み込める場所にJSONを保存
    os.makedirs("frontend/src", exist_ok=True)
    with open("frontend/src/data.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
