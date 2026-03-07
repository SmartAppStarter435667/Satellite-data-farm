import os, ee, json, time
from datetime import datetime, timedelta

# 認証設定
EE_JSON = os.getenv("EE_SERVICE_ACCOUNT_JSON")
with open("service_account.json", "w") as f: f.write(EE_JSON)
ee.Initialize(ee.ServiceAccountCredentials("your-account", "service_account.json"))

# 都道府県リスト（順次追加してください）
PREFECTURES = [
    {"id": "hokkaido", "name": "北海道", "lat": 43.06, "lon": 141.35},
    {"id": "saga", "name": "佐賀県", "lat": 33.26, "lon": 130.30},
    {"id": "tokyo", "name": "東京都", "lat": 35.68, "lon": 139.69}
]

def get_data(lat, lon):
    try:
        roi = ee.Geometry.Point([lon, lat]).buffer(5000).bounds()
        # Sentinel-2
        s2 = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(roi).filterDate(datetime.now() - timedelta(days=90), datetime.now()).sort('CLOUDY_PIXEL_PERCENTAGE').first()
        # Landsat 8 (温度用)
        l8 = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2").filterBounds(roi).filterDate(datetime.now() - timedelta(days=90), datetime.now()).sort('CLOUD_COVER').first()

        # [span_4](start_span)RGB画像URL (3バンド指定でエラー回避)[span_4](end_span)
        img_url = s2.getThumbURL({'bands':['B4','B3','B2'], 'min':0, 'max':4000, 'dimensions':600, 'format':'png'})
        
        # 指標計算
        stats = s2.multiply(1).reduceRegion(ee.Reducer.mean(), roi, 30).getInfo()
        ndvi = (stats['B8'] - stats['B4']) / (stats['B8'] + stats['B4'])
        ndwi = (stats['B3'] - stats['B8']) / (stats['B3'] + stats['B8'])
        cloud = s2.get('CLOUDY_PIXEL_PERCENTAGE').getInfo()
        
        # 温度計算
        temp_k = l8.select('ST_B10').reduceRegion(ee.Reducer.mean(), roi, 30).getInfo().get('ST_B10', 0)
        lst_c = (temp_k * 0.00341802 + 149.0) - 273.15 if temp_k else 0

        return {"img": img_url, "ndvi": round(ndvi, 3), "ndwi": round(ndwi, 3), "temp": round(lst_c, 1), "cloud": round(cloud, 1), "date": s2.date().format('YYYY-MM-DD').getInfo()}
    except: return None

def main():
    results = []
    for p in PREFECTURES:
        data = get_data(p['lat'], p['lon'])
        if data: results.append({**p, **data})
        time.sleep(2)
    os.makedirs("frontend/src", exist_ok=True)
    with open("frontend/src/data.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__": main()
