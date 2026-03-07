import os, ee, json, time
from datetime import datetime, timedelta

# 1. 認証設定
EE_JSON = os.getenv("EE_SERVICE_ACCOUNT_JSON")
with open("service_account.json", "w") as f: f.write(EE_JSON)
ee.Initialize(ee.ServiceAccountCredentials("your-account", "service_account.json"))

# 都道府県リスト（代表地点）
PREFECTURES = [
    {"id": "hokkaido", "name": "北海道", "lat": 43.06, "lon": 141.35},
    {"id": "saga", "name": "佐賀県", "lat": 33.26, "lon": 130.30},
    {"id": "tokyo", "name": "東京都", "lat": 35.68, "lon": 139.69},
    # ここに47都道府県を順次追加可能
]

def get_full_satellite_data(lat, lon):
    try:
        roi = ee.Geometry.Point([lon, lat]).buffer(5000).bounds()
        
        # --- Sentinel-2 データ (RGB, NDVI, NDWI, Cloud) ---
        s2_img = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
            .filterBounds(roi) \
            .filterDate(datetime.now() - timedelta(days=90), datetime.now()) \
            .sort('CLOUDY_PIXEL_PERCENTAGE') \
            .first()

        # 画像URL (RGB)
        img_url = s2_img.getThumbURL({'bands':['B4','B3','B2'], 'min':0, 'max':4000, 'dimensions':600, 'format':'png'})
        
        # NDVI (植生)
        ndvi = s2_img.normalizedDifference(['B8', 'B4']).reduceRegion(ee.Reducer.mean(), roi, 30).getInfo().get('NDVI', 0)
        
        # NDWI (水)
        ndwi = s2_img.normalizedDifference(['B3', 'B8']).reduceRegion(ee.Reducer.mean(), roi, 30).getInfo().get('nd', 0)
        
        # 雲量
        cloud = s2_img.get('CLOUDY_PIXEL_PERCENTAGE').getInfo()

        # --- Landsat 8 データ (LST: 地表面温度) ---
        l8_img = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2") \
            .filterBounds(roi) \
            .filterDate(datetime.now() - timedelta(days=90), datetime.now()) \
            .sort('CLOUD_COVER') \
            .first()
        
        # ケルビンを摂氏に変換 (簡易計算)
        temp_k = l8_img.select('ST_B10').reduceRegion(ee.Reducer.mean(), roi, 30).getInfo().get('ST_B10', 0)
        lst_c = (temp_k * 0.00341802 + 149.0) - 273.15 if temp_k else 0

        return {
            "img": img_url,
            "ndvi": round(ndvi, 3),
            "ndwi": round(ndwi, 3),
            "temp": round(lst_c, 1),
            "cloud": round(cloud, 1),
            "date": s2_img.date().format('YYYY-MM-DD').getInfo()
        }
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def main():
    results = []
    for pref in PREFECTURES:
        print(f"Processing {pref['name']}...")
        data = get_full_satellite_data(pref['lat'], pref['lon'])
        if data:
            results.append({**pref, **data})
        time.sleep(2) # API制限(429)対策

    os.makedirs("frontend/src", exist_ok=True)
    with open("frontend/src/data.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
