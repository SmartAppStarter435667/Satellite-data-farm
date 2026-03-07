import os, ee, json, time
from datetime import datetime, timedelta

# 認証省略 (前回同様)
ee.Initialize(ee.ServiceAccountCredentials("your-account", "key.json"))

# 都道府県リスト（代表的な5件を例示。47件まで増やせます）
PREFECTURES = [
    {"id": "hokkaido", "name": "北海道", "lat": 43.06, "lon": 141.35},
    {"id": "tokyo", "name": "東京都", "lat": 35.68, "lon": 139.69},
    {"id": "saga", "name": "佐賀県", "lat": 33.26, "lon": 130.30},
    {"id": "okinawa", "name": "沖縄県", "lat": 26.21, "lon": 127.68}
]

def get_data(lat, lon):
    roi = ee.Geometry.Point([lon, lat]).buffer(5000).bounds()
    # 期間を90日に広げて画像不足を回避
    img = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
        .filterBounds(roi) \
        .filterDate(datetime.now() - timedelta(days=90), datetime.now()) \
        .sort('CLOUDY_PIXEL_PERCENTAGE') \
        .first() # 最も雲が少ない1枚を取得

    if img.getInfo() is None: return None # 画像がない場合

    # 画像URL (RGB) - スケーリングを0-4000に調整
    url = img.select(['B4', 'B3', 'B2']).getThumbURL({'min': 0, 'max': 4000, 'dimensions': 512, 'format': 'png'})
    
    # NDVI計算
    ndvi = img.normalizedDifference(['B8', 'B4']).reduceRegion(ee.Reducer.mean(), roi, 30).getInfo().get('NDVI', 0)
    
    return {"img": url, "ndvi": round(ndvi, 2)}

def main():
    results = []
    for pref in PREFECTURES:
        print(f"Fetching {pref['name']}...")
        data = get_data(pref['lat'], pref['lon'])
        if data:
            results.append({**pref, **data})
        [span_0](start_span)[span_1](start_span)time.sleep(1) # API制限(429)対策[span_0](end_span)[span_1](end_span)

    with open("frontend/src/data.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
