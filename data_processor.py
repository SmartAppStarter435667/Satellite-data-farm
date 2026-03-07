import os, ee, json, time
from datetime import datetime, timedelta

# 認証
EE_JSON = os.getenv("EE_SERVICE_ACCOUNT_JSON")
with open("service_account.json", "w") as f: f.write(EE_JSON)
ee.Initialize(ee.ServiceAccountCredentials("your-account", "service_account.json"))

# 47都道府県の座標（代表地点）
PREFECTURES = [
    {"id": "hokkaido", "name": "北海道", "lat": 43.06, "lon": 141.35},
    {"id": "saga", "name": "佐賀県", "lat": 33.26, "lon": 130.30},
    {"id": "tokyo", "name": "東京都", "lat": 35.68, "lon": 139.69},
    # 必要に応じて追加
]

def get_satellite_data(lat, lon):
    try:
        roi = ee.Geometry.Point([lon, lat]).buffer(10000).bounds()
        # 過去90日から最も雲が少ない画像を取得
        img = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
            .filterBounds(roi) \
            .filterDate(datetime.now() - timedelta(days=90), datetime.now()) \
            .sort('CLOUDY_PIXEL_PERCENTAGE') \
            .first()

        # [span_5](start_span)[span_6](start_span)RGB 3バンドのみを選択してエラーを回避[span_5](end_span)[span_6](end_span)
        vis_params = {'bands': ['B4', 'B3', 'B2'], 'min': 0, 'max': 4000, 'dimensions': 600, 'format': 'png'}
        img_url = img.getThumbURL(vis_params)
        
        ndvi = img.normalizedDifference(['B8', 'B4']).reduceRegion(ee.Reducer.mean(), roi, 30).getInfo().get('NDVI', 0)
        
        return {"img": img_url, "ndvi": round(ndvi, 3), "date": img.date().format('YYYY-MM-DD').getInfo()}
    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    results = []
    for pref in PREFECTURES:
        print(f"Fetching {pref['name']}...")
        data = get_satellite_data(pref['lat'], pref['lon'])
        if data:
            results.append({**pref, **data})
        [span_7](start_span)time.sleep(2) # Quota制限対策[span_7](end_span)

    os.makedirs("frontend/src", exist_ok=True)
    with open("frontend/src/data.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
